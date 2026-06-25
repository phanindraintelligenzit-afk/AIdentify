"""
Audit Report Generator — Generates compliance reports from stored audit events.

Supports three report types:
  1. Daily Compliance Summary
  2. Weekly Compliance Digest
  3. Incident Report

Output formats: Markdown (email/Slack) and HTML (dashboard).
Data source: SQLite audit log database.
"""

import json
import logging
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TEMPLATES_DIR = Path(__file__).parent / "templates"
REPORT_VERSION = "1.0.0"

# Risk score thresholds
RISK_LOW = 30
RISK_MEDIUM = 50
RISK_HIGH = 70
RISK_CRITICAL = 85

# Rule definitions (from schema Section 2)
RULE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "RULE-001": {"name": "PII Leakage in Output", "severity": "critical"},
    "RULE-002": {"name": "Decision Without User Consent", "severity": "violation"},
    "RULE-003": {"name": "Low Confidence Decision", "severity": "warning"},
    "RULE-004": {"name": "Unauthorized Data Access", "severity": "critical"},
    "RULE-005": {"name": "Data Retention Exceeded", "severity": "violation"},
    "RULE-006": {"name": "High-Risk Without Human Oversight", "severity": "violation"},
    "RULE-007": {"name": "Off-Policy Action", "severity": "violation"},
    "RULE-008": {"name": "Cross-Border Data Transfer", "severity": "warning"},
    "RULE-009": {"name": "Model Version Deprecated", "severity": "warning"},
    "RULE-010": {"name": "Excessive Data Collection", "severity": "warning"},
    "RULE-011": {"name": "Consent Scope Mismatch", "severity": "violation"},
    "RULE-012": {"name": "Right to Explanation Not Available", "severity": "violation"},
    "RULE-013": {"name": "Anomalous Decision Rate", "severity": "warning"},
    "RULE-014": {"name": "Sensitive Category Processing", "severity": "critical"},
    "RULE-015": {"name": "Audit Log Tampering Detected", "severity": "critical"},
}

SEVERITY_ORDER = {"critical": 0, "violation": 1, "warning": 2, "info": 3}


# ---------------------------------------------------------------------------
# Data Access Layer
# ---------------------------------------------------------------------------

class AuditDataSource:
    """Queries the SQLite audit log database for report generation."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_events_in_range(
        self,
        start: datetime,
        end: datetime,
        agent_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve all events within a time range."""
        conn = self._connect()
        try:
            start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
            end_str = end.strftime("%Y-%m-%dT%H:%M:%S")
            if agent_name:
                rows = conn.execute(
                    "SELECT event_json FROM audit_events "
                    "WHERE timestamp >= ? AND timestamp < ? AND agent_name = ? "
                    "ORDER BY timestamp ASC",
                    (start_str, end_str, agent_name),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT event_json FROM audit_events "
                    "WHERE timestamp >= ? AND timestamp < ? "
                    "ORDER BY timestamp ASC",
                    (start_str, end_str),
                ).fetchall()
            return [json.loads(row["event_json"]) for row in rows]
        finally:
            conn.close()

    def get_events_by_risk(
        self,
        min_risk: float,
        start: datetime,
        end: datetime,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve high-risk events in a time range."""
        conn = self._connect()
        try:
            start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
            end_str = end.strftime("%Y-%m-%dT%H:%M:%S")
            rows = conn.execute(
                "SELECT event_json FROM audit_events "
                "WHERE risk_score >= ? AND timestamp >= ? AND timestamp < ? "
                "ORDER BY risk_score DESC, timestamp ASC LIMIT ?",
                (min_risk, start_str, end_str, limit),
            ).fetchall()
            return [json.loads(row["event_json"]) for row in rows]
        finally:
            conn.close()

    def get_events_by_rule(
        self,
        rule_id: str,
        start: datetime,
        end: datetime,
    ) -> List[Dict[str, Any]]:
        """Retrieve events that triggered a specific rule (via risk_factors)."""
        conn = self._connect()
        try:
            start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
            end_str = end.strftime("%Y-%m-%dT%H:%M:%S")
            # risk_factors is inside event_json; we filter in Python
            rows = conn.execute(
                "SELECT event_json FROM audit_events "
                "WHERE timestamp >= ? AND timestamp < ?",
                (start_str, end_str),
            ).fetchall()
            events = [json.loads(row["event_json"]) for row in rows]
            return [
                e for e in events
                if rule_id in (e.get("risk_factors") or [])
            ]
        finally:
            conn.close()

    def count_events(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        agent_name: Optional[str] = None,
    ) -> int:
        """Count events, optionally filtered by time range and agent."""
        conn = self._connect()
        try:
            query = "SELECT COUNT(*) as cnt FROM audit_events WHERE 1=1"
            params: list = []
            if start:
                query += " AND timestamp >= ?"
                params.append(start.strftime("%Y-%m-%dT%H:%M:%S"))
            if end:
                query += " AND timestamp < ?"
                params.append(end.strftime("%Y-%m-%dT%H:%M:%S"))
            if agent_name:
                query += " AND agent_name = ?"
                params.append(agent_name)
            row = conn.execute(query, params).fetchone()
            return row["cnt"]
        finally:
            conn.close()

    def get_critical_events(
        self,
        start: datetime,
        end: datetime,
    ) -> List[Dict[str, Any]]:
        """Retrieve events with critical-level risk factors."""
        conn = self._connect()
        try:
            start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
            end_str = end.strftime("%Y-%m-%dT%H:%M:%S")
            rows = conn.execute(
                "SELECT event_json FROM audit_events "
                "WHERE timestamp >= ? AND timestamp < ? "
                "ORDER BY timestamp ASC",
                (start_str, end_str),
            ).fetchall()
            events = [json.loads(row["event_json"]) for row in rows]
            critical_rules = {rid for rid, r in RULE_DEFINITIONS.items() if r["severity"] == "critical"}
            return [
                e for e in events
                if critical_rules.intersection(set(e.get("risk_factors") or []))
            ]
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Report Context Builders
# ---------------------------------------------------------------------------

def _risk_label(score: float) -> str:
    if score >= RISK_CRITICAL:
        return "critical"
    elif score >= RISK_HIGH:
        return "high"
    elif score >= RISK_MEDIUM:
        return "medium"
    elif score >= RISK_LOW:
        return "low"
    return "minimal"


def _trend_indicator(current: float, previous: float) -> str:
    if current > previous * 1.05:
        return "📈"
    elif current < previous * 0.95:
        return "📉"
    return "➡️"


def _compute_compliance_score(events: List[Dict[str, Any]]) -> float:
    """Compute a 0-100 compliance score from events."""
    if not events:
        return 100.0
    total = len(events)
    violations = sum(
        1 for e in events
        if any(
            RULE_DEFINITIONS.get(rf, {}).get("severity") in ("critical", "violation")
            for rf in (e.get("risk_factors") or [])
        )
    )
    score = max(0.0, 100.0 - (violations / total) * 100.0)
    return round(score, 1)


def _compute_coverage(events: List[Dict[str, Any]], article: str) -> float:
    """Compute coverage percentage for an EU AI Act article."""
    if not events:
        return 100.0
    tagged = sum(1 for e in events if article in (e.get("compliance_tags") or []))
    return round(tagged / len(events) * 100, 1)


# ---- Daily Summary Builder ----

def build_daily_context(
    events: List[Dict[str, Any]],
    prev_events: List[Dict[str, Any]],
    date: datetime,
) -> Dict[str, Any]:
    """Build the template context for a daily compliance summary."""
    total = len(events)
    prev_total = len(prev_events)

    # Unique agents
    agents = set(e["agent_name"] for e in events)
    prev_agents = set(e["agent_name"] for e in prev_events)

    # Avg confidence
    conf_scores = [e.get("confidence_score") or e.get("output_summary", {}).get("confidence_score") for e in events]
    conf_scores = [c for c in conf_scores if c is not None]
    avg_conf = round(sum(conf_scores) / len(conf_scores), 3) if conf_scores else 0.0

    prev_conf_scores = [e.get("confidence_score") or e.get("output_summary", {}).get("confidence_score") for e in prev_events]
    prev_conf_scores = [c for c in prev_conf_scores if c is not None]
    prev_avg_conf = round(sum(prev_conf_scores) / len(prev_conf_scores), 3) if prev_conf_scores else 0.0

    # Avg risk
    risk_scores = [e.get("risk_score", 0) for e in events]
    avg_risk = round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else 0.0
    prev_risk_scores = [e.get("risk_score", 0) for e in prev_events]
    prev_avg_risk = round(sum(prev_risk_scores) / len(prev_risk_scores), 1) if prev_risk_scores else 0.0

    # PII events
    pii_events = sum(1 for e in events if e.get("input_summary", {}).get("pii_detected") or e.get("output_summary", {}).get("pii_detected"))
    prev_pii = sum(1 for e in prev_events if e.get("input_summary", {}).get("pii_detected") or e.get("output_summary", {}).get("pii_detected"))

    # Consent violations
    consent_violations = sum(1 for e in events if (e.get("consent_flags") or {}).get("user_consent_obtained") is False)
    prev_consent_v = sum(1 for e in prev_events if (e.get("consent_flags") or {}).get("user_consent_obtained") is False)

    # Violation count (events with critical or violation risk factors)
    violation_count = sum(
        1 for e in events
        if any(
            RULE_DEFINITIONS.get(rf, {}).get("severity") in ("critical", "violation")
            for rf in (e.get("risk_factors") or [])
        )
    )
    prev_violation_count = sum(
        1 for e in prev_events
        if any(
            RULE_DEFINITIONS.get(rf, {}).get("severity") in ("critical", "violation")
            for rf in (e.get("risk_factors") or [])
        )
    )
    violation_delta = (
        round((violation_count - prev_violation_count) / max(prev_violation_count, 1) * 100, 1)
        if prev_violation_count > 0
        else (100.0 if violation_count > 0 else 0.0)
    )

    # Critical count
    critical_count = sum(
        1 for e in events
        if any(
            RULE_DEFINITIONS.get(rf, {}).get("severity") == "critical"
            for rf in (e.get("risk_factors") or [])
        )
    )

    # Top violations
    rule_counter: Counter = Counter()
    for e in events:
        for rf in e.get("risk_factors") or []:
            if rf in RULE_DEFINITIONS:
                rule_counter[rf] += 1
    top_violations = []
    for rule_id, count in rule_counter.most_common(10):
        rule_def = RULE_DEFINITIONS[rule_id]
        prev_count = sum(1 for e in prev_events if rule_id in (e.get("risk_factors") or []))
        delta_str = f"+{count - prev_count}" if count >= prev_count else str(count - prev_count)
        top_violations.append({
            "rule_id": rule_id,
            "rule_name": rule_def["name"],
            "count": count,
            "severity": rule_def["severity"],
            "delta": delta_str,
        })

    # Agent activity
    agent_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "risk_sum": 0.0, "violations": 0})
    for e in events:
        name = e["agent_name"]
        agent_stats[name]["count"] += 1
        agent_stats[name]["risk_sum"] += e.get("risk_score", 0)
        if any(
            RULE_DEFINITIONS.get(rf, {}).get("severity") in ("critical", "violation")
            for rf in (e.get("risk_factors") or [])
        ):
            agent_stats[name]["violations"] += 1

    agent_activity = []
    for name, stats in sorted(agent_stats.items(), key=lambda x: -x[1]["count"]):
        avg_r = round(stats["risk_sum"] / stats["count"], 1)
        status = "🟢" if avg_r < RISK_LOW else ("🟡" if avg_r < RISK_MEDIUM else ("🟠" if avg_r < RISK_HIGH else "🔴"))
        agent_activity.append({
            "agent_name": name,
            "decisions": stats["count"],
            "avg_risk": avg_r,
            "violations": stats["violations"],
            "status": status,
        })

    # High-risk events (top 5)
    sorted_by_risk = sorted(events, key=lambda e: -e.get("risk_score", 0))
    high_risk_events = []
    for e in sorted_by_risk[:5]:
        risk_factors = e.get("risk_factors") or []
        primary_rule = risk_factors[0] if risk_factors else "—"
        rule_name = RULE_DEFINITIONS.get(primary_rule, {}).get("name", primary_rule)
        high_risk_events.append({
            "time": e["timestamp"][:19],
            "agent": e["agent_name"],
            "action": e["action_type"],
            "risk_score": e.get("risk_score", 0),
            "rule": rule_name,
        })

    # PII incidents
    pii_incidents = []
    for e in events:
        inp = e.get("input_summary", {})
        out = e.get("output_summary", {})
        if inp.get("pii_detected"):
            pii_incidents.append({
                "time": e["timestamp"][:19],
                "agent": e["agent_name"],
                "pii_types": ", ".join(inp.get("pii_types", [])),
                "direction": "input",
                "risk_score": e.get("risk_score", 0),
            })
        if out.get("pii_detected"):
            pii_incidents.append({
                "time": e["timestamp"][:19],
                "agent": e["agent_name"],
                "pii_types": ", ".join(out.get("pii_types", [])),
                "direction": "output",
                "risk_score": e.get("risk_score", 0),
            })

    # EU AI Act coverage
    coverage = {
        "art_12": _compute_coverage(events, "art_12"),
        "art_13": _compute_coverage(events, "art_13"),
        "art_14": _compute_coverage(events, "art_14"),
        "art_15": _compute_coverage(events, "art_15"),
    }

    # Recommendations
    recommendations = []
    if critical_count > 0:
        recommendations.append(f"🚨 {critical_count} critical incident(s) require immediate review.")
    if violation_count > total * 0.05:
        recommendations.append(f"⚠️ Violation rate ({violation_count}/{total}) exceeds 5% threshold.")
    if pii_events > 0:
        recommendations.append(f"🔒 {pii_events} PII incident(s) detected — verify data handling.")
    if avg_risk > RISK_HIGH:
        recommendations.append(f"📊 Average risk score ({avg_risk}) is elevated — review high-risk agents.")
    if not recommendations:
        recommendations.append("✅ All metrics within normal parameters.")

    compliance_score = _compute_compliance_score(events)

    return {
        "date": date.strftime("%Y-%m-%d"),
        "total_events": total,
        "violation_count": violation_count,
        "violation_delta": violation_delta,
        "critical_count": critical_count,
        "compliance_score": compliance_score,
        "unique_agents": len(agents),
        "avg_confidence": avg_conf,
        "avg_risk": avg_risk,
        "pii_events": pii_events,
        "consent_violations": consent_violations,
        "trends": {
            "total_events": _trend_indicator(total, prev_total),
            "unique_agents": _trend_indicator(len(agents), len(prev_agents)),
            "avg_confidence": _trend_indicator(avg_conf, prev_avg_conf),
            "avg_risk": _trend_indicator(avg_risk, prev_avg_risk),
            "pii_events": _trend_indicator(pii_events, prev_pii),
            "consent_violations": _trend_indicator(consent_violations, prev_consent_v),
        },
        "top_violations": top_violations,
        "agent_activity": agent_activity,
        "high_risk_events": high_risk_events,
        "pii_incidents": pii_incidents,
        "coverage": coverage,
        "recommendations": recommendations,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": REPORT_VERSION,
    }


# ---- Weekly Digest Builder ----

def build_weekly_context(
    this_week_events: List[Dict[str, Any]],
    last_week_events: List[Dict[str, Any]],
    week_start: datetime,
    week_end: datetime,
) -> Dict[str, Any]:
    """Build the template context for a weekly compliance digest."""
    total = len(this_week_events)
    prev_total = len(last_week_events)

    # Violation rate
    def _violation_rate(evts):
        if not evts:
            return 0.0
        v = sum(
            1 for e in evts
            if any(
                RULE_DEFINITIONS.get(rf, {}).get("severity") in ("critical", "violation")
                for rf in (e.get("risk_factors") or [])
            )
        )
        return round(v / len(evts) * 100, 1)

    # Critical incidents
    def _critical_count(evts):
        return sum(
            1 for e in evts
            if any(
                RULE_DEFINITIONS.get(rf, {}).get("severity") == "critical"
                for rf in (e.get("risk_factors") or [])
            )
        )

    # Compliance score
    this_score = _compute_compliance_score(this_week_events)
    prev_score = _compute_compliance_score(last_week_events)

    # New agents
    this_agents = set(e["agent_name"] for e in this_week_events)
    last_agents = set(e["agent_name"] for e in last_week_events)
    new_agents = this_agents - last_agents

    # Deltas
    def _delta_str(curr, prev):
        d = curr - prev
        return f"+{d}" if d >= 0 else str(d)

    def _status(curr, prev, higher_is_worse=False):
        if higher_is_worse:
            if curr > prev * 1.1:
                return "🔴"
            elif curr > prev * 1.05:
                return "🟡"
            return "🟢"
        else:
            if curr < prev * 0.9:
                return "🔴"
            elif curr < prev * 0.95:
                return "🟡"
            return "🟢"

    # Violations by rule (daily breakdown)
    day_names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    rule_daily: Dict[str, Dict[str, int]] = defaultdict(lambda: {d: 0 for d in day_names})
    rule_totals: Counter = Counter()
    for e in this_week_events:
        try:
            dt = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
            day_idx = dt.weekday()
            day_key = day_names[day_idx]
        except (ValueError, IndexError):
            day_key = "mon"
        for rf in e.get("risk_factors") or []:
            if rf in RULE_DEFINITIONS:
                rule_daily[rf][day_key] += 1
                rule_totals[rf] += 1

    violations_by_rule = []
    for rule_id, total_count in rule_totals.most_common(15):
        rule_def = RULE_DEFINITIONS[rule_id]
        daily = rule_daily[rule_id]
        violations_by_rule.append({
            "rule_name": rule_def["name"],
            "mon": daily["mon"],
            "tue": daily["tue"],
            "wed": daily["wed"],
            "thu": daily["thu"],
            "fri": daily["fri"],
            "sat": daily["sat"],
            "sun": daily["sun"],
            "total": total_count,
        })

    # Violations by agent
    agent_violations: Dict[str, Counter] = defaultdict(Counter)
    agent_violation_count: Counter = Counter()
    for e in this_week_events:
        for rf in e.get("risk_factors") or []:
            if rf in RULE_DEFINITIONS:
                agent_violations[e["agent_name"]][rf] += 1
                agent_violation_count[e["agent_name"]] += 1

    violations_by_agent = []
    for agent, count in agent_violation_count.most_common(20):
        most_common_rule_id = agent_violations[agent].most_common(1)[0][0] if agent_violations[agent] else "—"
        most_common_rule_name = RULE_DEFINITIONS.get(most_common_rule_id, {}).get("name", most_common_rule_id)
        agent_events = [e for e in this_week_events if e["agent_name"] == agent]
        avg_r = round(sum(e.get("risk_score", 0) for e in agent_events) / len(agent_events), 1) if agent_events else 0.0
        violations_by_agent.append({
            "agent": agent,
            "count": count,
            "most_common_rule": most_common_rule_name,
            "risk_level": _risk_label(avg_r),
        })

    # EU AI Act status
    def _article_status(events, article):
        cov = _compute_coverage(events, article)
        if cov >= 95:
            return "✅", f"Full coverage ({cov}%)"
        elif cov >= 80:
            return "⚠️", f"Partial coverage ({cov}%)"
        else:
            return "❌", f"Insufficient coverage ({cov}%)"

    eu_ai_act = {}
    for art_key, art_num in [("art_12", "Art. 12"), ("art_13", "Art. 13"), ("art_14", "Art. 14"),
                              ("art_15", "Art. 15"), ("art_16", "Art. 16"), ("art_17", "Art. 17")]:
        status_icon, notes = _article_status(this_week_events, art_key)
        eu_ai_act[art_key] = {"status": status_icon, "notes": notes}

    # Model version report
    model_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "conf_sum": 0.0, "versions": set()})
    for e in this_week_events:
        model = e.get("model_version", "unknown")
        model_stats[model]["count"] += 1
        conf = e.get("confidence_score") or e.get("output_summary", {}).get("confidence_score")
        if conf is not None:
            model_stats[model]["conf_sum"] += conf
        model_stats[model]["versions"].add(e.get("model_version", "unknown"))

    model_report = []
    for model, stats in sorted(model_stats.items(), key=lambda x: -x[1]["count"]):
        avg_c = round(stats["conf_sum"] / stats["count"], 3) if stats["count"] > 0 else 0.0
        model_report.append({
            "model": model,
            "version": ", ".join(stats["versions"]),
            "deployed": "—",
            "decisions": stats["count"],
            "avg_confidence": avg_c,
            "status": "🟢" if avg_c >= 0.7 else "🟡" if avg_c >= 0.5 else "🔴",
        })

    # New violations this week (not seen last week)
    this_rule_ids: set = set()
    for e in this_week_events:
        for rf in e.get("risk_factors") or []:
            if rf in RULE_DEFINITIONS:
                this_rule_ids.add(rf)
    last_rule_ids: set = set()
    for e in last_week_events:
        for rf in e.get("risk_factors") or []:
            if rf in RULE_DEFINITIONS:
                last_rule_ids.add(rf)
    new_rule_ids = this_rule_ids - last_rule_ids
    new_violations = []
    for rid in new_rule_ids:
        rule_def = RULE_DEFINITIONS[rid]
        first_event = next(
            (e for e in this_week_events if rid in (e.get("risk_factors") or [])),
            None,
        )
        count = sum(1 for e in this_week_events if rid in (e.get("risk_factors") or []))
        new_violations.append({
            "rule_id": rid,
            "rule_name": rule_def["name"],
            "severity": rule_def["severity"],
            "first_seen": first_event["timestamp"][:19] if first_event else "—",
            "count": count,
            "description": f"New violation type detected this week.",
        })

    # Resolved issues (in last week but not this week)
    resolved_ids = last_rule_ids - this_rule_ids
    resolved_issues = []
    for rid in resolved_ids:
        rule_def = RULE_DEFINITIONS[rid]
        resolved_issues.append({
            "rule_id": rid,
            "rule_name": rule_def["name"],
            "resolved_at": week_start.strftime("%Y-%m-%d"),
        })

    # Action items
    action_items = []
    if _critical_count(this_week_events) > 0:
        action_items.append({
            "priority": "HIGH",
            "description": f"Review {_critical_count(this_week_events)} critical incident(s)",
            "owner": "Compliance Team",
            "due_date": (week_end + timedelta(days=1)).strftime("%Y-%m-%d"),
        })
    if _violation_rate(this_week_events) > 5.0:
        action_items.append({
            "priority": "MEDIUM",
            "description": f"Violation rate ({_violation_rate(this_week_events)}%) exceeds 5% threshold",
            "owner": "ML Ops",
            "due_date": (week_end + timedelta(days=3)).strftime("%Y-%m-%d"),
        })
    if new_violations:
        action_items.append({
            "priority": "HIGH",
            "description": f"Investigate {len(new_violations)} new violation type(s)",
            "owner": "Compliance Team",
            "due_date": (week_end + timedelta(days=2)).strftime("%Y-%m-%d"),
        })

    # Trends
    trends = {
        "decision_volume": f"{total} decisions this week ({_delta_str(total, prev_total)} vs last week)",
        "risk_distribution": f"Avg risk: {round(sum(e.get('risk_score', 0) for e in this_week_events) / max(total, 1), 1)}",
        "model_performance": f"{len(model_report)} model(s) active",
    }

    return {
        "week_start": week_start.strftime("%Y-%m-%d"),
        "week_end": week_end.strftime("%Y-%m-%d"),
        "this_week": {
            "total": total,
            "violation_rate": _violation_rate(this_week_events),
            "critical": _critical_count(this_week_events),
            "compliance_score": this_score,
            "new_agents": len(new_agents),
        },
        "last_week": {
            "total": prev_total,
            "violation_rate": _violation_rate(last_week_events),
            "critical": _critical_count(last_week_events),
            "compliance_score": prev_score,
        },
        "deltas": {
            "total": _delta_str(total, prev_total),
            "violation_rate": _delta_str(_violation_rate(this_week_events), _violation_rate(last_week_events)),
            "critical": _delta_str(_critical_count(this_week_events), _critical_count(last_week_events)),
            "compliance_score": _delta_str(this_score, prev_score),
        },
        "status": {
            "total": _status(total, prev_total),
            "violation_rate": _status(_violation_rate(this_week_events), _violation_rate(last_week_events), higher_is_worse=True),
            "critical": _status(_critical_count(this_week_events), _critical_count(last_week_events), higher_is_worse=True),
            "compliance_score": _status(this_score, prev_score),
            "new_agents": "🟡" if new_agents else "🟢",
        },
        "trends": trends,
        "violations_by_rule": violations_by_rule,
        "violations_by_agent": violations_by_agent,
        "eu_ai_act": eu_ai_act,
        "model_report": model_report,
        "retention": {
            "active_count": total,
            "pending_anon": 0,
            "purged": 0,
            "storage_gb": 0.0,
            "storage_pct": 0.0,
        },
        "new_violations": new_violations,
        "resolved_issues": resolved_issues,
        "action_items": action_items,
        "appendix": {
            "log_link": "—",
            "metrics_link": "—",
            "incident_link": "—",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "next_report_date": (week_end + timedelta(days=7)).strftime("%Y-%m-%d"),
    }


# ---- Incident Report Builder ----

def build_incident_context(
    events: List[Dict[str, Any]],
    incident_id: str,
    severity: str = "high",
) -> Dict[str, Any]:
    """Build the template context for an incident report."""
    if not events:
        return {
            "incident_id": incident_id,
            "severity": severity,
            "severity_level": 3,
            "status": "open",
            "detected_at": "—",
            "resolved_at": "—",
            "duration": "—",
            "affected_users": 0,
            "affected_agents": [],
            "regulatory_impact": "—",
            "summary": "No events found for this incident.",
            "triggering_events": [],
            "rules_triggered": [],
            "timeline": [],
            "impact": {
                "pii_exposed": "no",
                "pii_types": "—",
                "records_affected": 0,
                "data_classification": "—",
                "affected_decisions": 0,
                "legal_effect_decisions": 0,
                "users_notified": "no",
                "eu_ai_act_articles": "—",
                "gdpr_articles": "—",
                "notification_required": "no",
                "dpa_notified": "pending",
                "users_notified_reg": "pending",
            },
            "root_cause": "No data available.",
            "remediation_actions": [],
            "evidence_events": "[]",
            "hash_verification": {
                "integrity_status": "unknown",
                "first_hash": "—",
                "last_hash": "—",
            },
            "lessons_learned": "N/A",
            "signoff": {
                "incident_commander": {"name": "—", "date": "—", "signature": "—"},
                "compliance_officer": {"name": "—", "date": "—", "signature": "—"},
                "ciso": {"name": "—", "date": "—", "signature": "—"},
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "classification": "internal",
        }

    # Sort by timestamp
    events = sorted(events, key=lambda e: e.get("timestamp", ""))

    detected_at = events[0]["timestamp"][:19] if events else "—"
    resolved_at = events[-1]["timestamp"][:19] if len(events) > 1 else "—"

    # Duration
    try:
        t1 = datetime.fromisoformat(events[0]["timestamp"].replace("Z", "+00:00"))
        t2 = datetime.fromisoformat(events[-1]["timestamp"].replace("Z", "+00:00"))
        duration = str(t2 - t1)
    except (ValueError, IndexError):
        duration = "—"

    # Affected agents and users
    affected_agents = list(set(e["agent_name"] for e in events))
    user_ids = set(e.get("user_id") for e in events if e.get("user_id"))
    affected_users = len(user_ids)

    # Triggering events
    triggering_events = []
    for e in events[:20]:
        triggering_events.append({
            "event_id": e["event_id"],
            "timestamp": e["timestamp"][:19],
            "agent": e["agent_name"],
            "action": e["action_type"],
            "risk_score": e.get("risk_score", 0),
        })

    # Rules triggered
    rule_counter: Counter = Counter()
    for e in events:
        for rf in e.get("risk_factors") or []:
            if rf in RULE_DEFINITIONS:
                rule_counter[rf] += 1
    rules_triggered = []
    for rule_id, count in rule_counter.most_common():
        rule_def = RULE_DEFINITIONS[rule_id]
        rules_triggered.append({
            "rule_id": rule_id,
            "rule_name": rule_def["name"],
            "severity": rule_def["severity"],
            "details": f"Triggered {count} time(s)",
        })

    # Timeline
    timeline = []
    for e in events[:50]:
        risk_factors = e.get("risk_factors") or []
        primary_rule = risk_factors[0] if risk_factors else "event"
        timeline.append({
            "time": e["timestamp"][:19],
            "event_type": primary_rule,
            "actor": e["agent_name"],
            "details": e.get("output_summary", {}).get("decision", "—")[:100],
        })

    # Impact assessment
    pii_events = [e for e in events if (e.get("output_summary", {}) or {}).get("pii_detected") or (e.get("input_summary", {}) or {}).get("pii_detected")]
    pii_types = set()
    for e in pii_events:
        pii_types.update(e.get("input_summary", {}).get("pii_types", []))
        pii_types.update(e.get("output_summary", {}).get("pii_types", []))

    legal_effect = sum(1 for e in events if e.get("action_type") in ("decision", "approve", "reject", "escalate"))

    # EU AI Act articles from compliance tags
    article_counter: Counter = Counter()
    for e in events:
        for tag in e.get("compliance_tags") or []:
            article_counter[tag] += 1
    eu_articles = [k for k, v in article_counter.most_common() if k.startswith("art_")]

    # Severity level (1-5)
    max_risk = max((e.get("risk_score", 0) for e in events), default=0)
    if max_risk >= RISK_CRITICAL:
        severity_level = 5
        severity_label = "critical"
    elif max_risk >= RISK_HIGH:
        severity_level = 4
        severity_label = "high"
    elif max_risk >= RISK_MEDIUM:
        severity_level = 3
        severity_label = "medium"
    elif max_risk >= RISK_LOW:
        severity_level = 2
        severity_label = "low"
    else:
        severity_level = 1
        severity_label = "info"

    # Evidence
    evidence_events = json.dumps(
        [
            {
                "event_id": e["event_id"],
                "timestamp": e["timestamp"],
                "agent": e["agent_name"],
                "risk_score": e.get("risk_score", 0),
                "risk_factors": e.get("risk_factors", []),
            }
            for e in events[:20]
        ],
        indent=2,
    )

    # Hash verification
    first_hash = events[0].get("input_summary", {}).get("prompt_hash", "—") if events else "—"
    last_hash = events[-1].get("output_summary", {}).get("output_hash", "—") if events else "—"

    # Remediation actions
    remediation_actions = []
    for rule_id, count in rule_counter.most_common(5):
        rule_def = RULE_DEFINITIONS[rule_id]
        remediation_actions.append({
            "action": f"Address {rule_def['name']} ({count} occurrences)",
            "owner": "Compliance Team",
            "status": "open",
            "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d"),
        })

    return {
        "incident_id": incident_id,
        "severity": severity_label,
        "severity_level": severity_level,
        "status": "open",
        "detected_at": detected_at,
        "resolved_at": resolved_at,
        "duration": duration,
        "affected_users": affected_users,
        "affected_agents": ", ".join(affected_agents),
        "regulatory_impact": "EU AI Act, GDPR" if eu_articles else "Under review",
        "summary": f"Incident involving {len(events)} event(s) across {len(affected_agents)} agent(s). "
                    f"Max risk score: {max_risk}. "
                    f"Primary rules: {', '.join(r['rule_name'] for r in rules_triggered[:3])}.",
        "triggering_events": triggering_events,
        "rules_triggered": rules_triggered,
        "timeline": timeline,
        "impact": {
            "pii_exposed": "yes" if pii_events else "no",
            "pii_types": ", ".join(pii_types) if pii_types else "—",
            "records_affected": len(events),
            "data_classification": "confidential",
            "affected_decisions": len(events),
            "legal_effect_decisions": legal_effect,
            "users_notified": "no",
            "eu_ai_act_articles": ", ".join(eu_articles) if eu_articles else "—",
            "gdpr_articles": "Art. 6, Art. 32" if pii_events else "—",
            "notification_required": "yes" if severity_level >= 4 else "no",
            "dpa_notified": "pending",
            "users_notified_reg": "pending",
        },
        "root_cause": "Root cause analysis pending. Initial assessment indicates "
                       f"{rules_triggered[0]['rule_name'] if rules_triggered else 'unknown issue'} "
                       f"as the primary trigger.",
        "remediation_actions": remediation_actions,
        "evidence_events": evidence_events,
        "hash_verification": {
            "integrity_status": "verified",
            "first_hash": first_hash[:32] + "..." if len(str(first_hash)) > 32 else str(first_hash),
            "last_hash": last_hash[:32] + "..." if len(str(last_hash)) > 32 else str(last_hash),
        },
        "lessons_learned": "To be completed after incident resolution.",
        "signoff": {
            "incident_commander": {"name": "—", "date": "—", "signature": "—"},
            "compliance_officer": {"name": "—", "date": "—", "signature": "—"},
            "ciso": {"name": "—", "date": "—", "signature": "—"},
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "confidential",
    }


# ---------------------------------------------------------------------------
# Report Generator
# ---------------------------------------------------------------------------

class ReportGenerator:
    """
    Generates compliance reports from audit event data.

    Usage:
        gen = ReportGenerator(db_path="audit_events.db")
        md = gen.generate_daily(date="2026-06-21")
        html = gen.generate_daily(date="2026-06-21", output_format="html")
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.data_source = AuditDataSource(db_path)
        self._jinja = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        template = self._jinja.get_template(template_name)
        return template.render(**context)

    def _markdown_to_html(self, markdown_text: str) -> str:
        """Simple Markdown-to-HTML conversion for dashboard output."""
        import re

        html = markdown_text

        # Escape HTML entities
        html = html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Headers
        html = re.sub(r"^###### (.+)$", r"<h6>\1</h6>", html, flags=re.MULTILINE)
        html = re.sub(r"^##### (.+)$", r"<h5>\1</h5>", html, flags=re.MULTILINE)
        html = re.sub(r"^#### (.+)$", r"<h4>\1</h4>", html, flags=re.MULTILINE)
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)

        # Bold
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)

        # Italic
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

        # Code blocks
        html = re.sub(r"```(\w*)\n(.*?)```", r"<pre><code>\2</code></pre>", html, flags=re.DOTALL)

        # Inline code
        html = re.sub(r"`(.+?)`", r"<code>\1</code>", html)

        # Tables
        def _table_to_html(table_text: str) -> str:
            lines = table_text.strip().split("\n")
            if len(lines) < 2:
                return table_text
            html_table = "<table><thead><tr>"
            headers = [h.strip() for h in lines[0].split("|") if h.strip()]
            for h in headers:
                html_table += f"<th>{h}</th>"
            html_table += "</tr></thead><tbody>"
            for line in lines[2:]:  # skip header and separator
                cells = [c.strip() for c in line.split("|") if c.strip()]
                if cells:
                    html_table += "<tr>"
                    for c in cells:
                        html_table += f"<td>{c}</td>"
                    html_table += "</tr>"
            html_table += "</tbody></table>"
            return html_table

        # Find table blocks
        table_pattern = re.compile(r"(\|.+\|\n\|[-| ]+\|\n(?:\|.+\|\n?)+)")
        html = table_pattern.sub(lambda m: _table_to_html(m.group(1)), html)

        # Unordered lists
        html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
        html = re.sub(r"(<li>.*</li>\n?)+", r"<ul>\g<0></ul>", html)

        # Horizontal rule
        html = re.sub(r"^---$", r"<hr/>", html, flags=re.MULTILINE)

        # Line breaks
        html = html.replace("\n\n", "</p><p>")

        return f"<div class='report'>{html}</div>"

    def generate_daily(
        self,
        date: Optional[str] = None,
        output_format: str = "markdown",
    ) -> str:
        """
        Generate a daily compliance summary.

        Args:
            date: Date string (YYYY-MM-DD). Defaults to today.
            output_format: "markdown" or "html".

        Returns:
            Rendered report string.
        """
        if date:
            report_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            report_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        start = report_date
        end = start + timedelta(days=1)
        prev_start = start - timedelta(days=1)
        prev_end = start

        events = self.data_source.get_events_in_range(start, end)
        prev_events = self.data_source.get_events_in_range(prev_start, prev_end)

        context = build_daily_context(events, prev_events, report_date)
        md = self._render_template("daily.md.j2", context)

        if output_format == "html":
            return self._markdown_to_html(md)
        return md

    def generate_weekly(
        self,
        week_start: Optional[str] = None,
        output_format: str = "markdown",
    ) -> str:
        """
        Generate a weekly compliance digest.

        Args:
            week_start: Start date string (YYYY-MM-DD). Defaults to Monday of current week.
            output_format: "markdown" or "html".

        Returns:
            Rendered report string.
        """
        if week_start:
            start = datetime.strptime(week_start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            start = today - timedelta(days=today.weekday())

        end = start + timedelta(days=7)
        prev_start = start - timedelta(days=7)
        prev_end = start

        this_events = self.data_source.get_events_in_range(start, end)
        last_events = self.data_source.get_events_in_range(prev_start, prev_end)

        context = build_weekly_context(this_events, last_events, start, end)
        md = self._render_template("weekly.md.j2", context)

        if output_format == "html":
            return self._markdown_to_html(md)
        return md

    def generate_incident(
        self,
        incident_id: str,
        rule_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        severity: str = "high",
        output_format: str = "markdown",
    ) -> str:
        """
        Generate an incident report for critical rule violations.

        Args:
            incident_id: Unique incident identifier.
            rule_id: Rule ID that triggered the incident (e.g., "RULE-001").
            start_date: Start date for event lookup (YYYY-MM-DD). Defaults to 7 days ago.
            end_date: End date for event lookup (YYYY-MM-DD). Defaults to today.
            severity: Incident severity level.
            output_format: "markdown" or "html".

        Returns:
            Rendered report string.
        """
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
        else:
            end = datetime.now(timezone.utc)

        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            start = end - timedelta(days=7)

        if rule_id:
            events = self.data_source.get_events_by_rule(rule_id, start, end)
        else:
            events = self.data_source.get_events_by_risk(RISK_HIGH, start, end)

        context = build_incident_context(events, incident_id, severity)
        md = self._render_template("incident.md.j2", context)

        if output_format == "html":
            return self._markdown_to_html(md)
        return md

"""
Compliance Rules Engine — Evaluates audit events against compliance rules.

Implements all 15 rules from the compliance audit schema (Section 2).
Each rule is evaluated against an AuditEvent and returns a TriggeredRule
if the condition is met.

Usage:
    from compliance.rules_engine import RulesEngine
    engine = RulesEngine()
    results = engine.evaluate(audit_event)
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import yaml

from compliance.models import (
    ActionType,
    AuditEvent,
    ConsentFlags,
    DataLineage,
    InputSummary,
    OutputSummary,
)

# ---------------------------------------------------------------------------
# Severity levels (ordered by increasing severity)
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"


SEVERITY_ORDER = {
    Severity.INFO: 0,
    Severity.WARNING: 1,
    Severity.VIOLATION: 2,
    Severity.CRITICAL: 3,
}

# Severity weights for risk scoring
SEVERITY_WEIGHTS = {
    Severity.INFO: 5,
    Severity.WARNING: 15,
    Severity.VIOLATION: 35,
    Severity.CRITICAL: 50,
}


# ---------------------------------------------------------------------------
# Triggered rule result
# ---------------------------------------------------------------------------

class TriggeredRule:
    """Result of a single rule evaluation."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        severity: Severity,
        message: str,
        articles: Optional[List[str]] = None,
        auto_block: bool = False,
    ):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.severity = severity
        self.message = message
        self.articles = articles or []
        self.auto_block = auto_block

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "message": self.message,
            "articles": self.articles,
            "auto_block": self.auto_block,
        }

    def __repr__(self) -> str:
        return (
            f"TriggeredRule({self.rule_id}, {self.name}, "
            f"severity={self.severity.value})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TriggeredRule):
            return NotImplemented
        return self.rule_id == other.rule_id


# ---------------------------------------------------------------------------
# Evaluation result
# ---------------------------------------------------------------------------

class EvaluationResult:
    """Aggregated result of evaluating all rules against an event."""

    def __init__(
        self,
        event_id: str,
        triggered_rules: List[TriggeredRule],
        risk_score: float,
        requires_human_review: bool,
        auto_block: bool,
    ):
        self.event_id = event_id
        self.triggered_rules = triggered_rules
        self.risk_score = risk_score
        self.requires_human_review = requires_human_review
        self.auto_block = auto_block

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "triggered_rules": [r.to_dict() for r in self.triggered_rules],
            "risk_score": self.risk_score,
            "requires_human_review": self.requires_human_review,
            "auto_block": self.auto_block,
        }

    @property
    def has_critical(self) -> bool:
        return any(r.severity == Severity.CRITICAL for r in self.triggered_rules)

    @property
    def has_violation(self) -> bool:
        return any(
            r.severity in (Severity.VIOLATION, Severity.CRITICAL)
            for r in self.triggered_rules
        )

    @property
    def max_severity(self) -> Severity:
        if not self.triggered_rules:
            return Severity.INFO
        return max(self.triggered_rules, key=lambda r: SEVERITY_ORDER[r.severity]).severity


# ---------------------------------------------------------------------------
# Rules Engine
# ---------------------------------------------------------------------------

class RulesEngine:
    """
    Evaluates audit events against the 15 compliance rules defined in
    the compliance audit schema (Section 2).

    Rules are loaded from rules_config.yaml. Each rule's condition is
    evaluated against the event fields.
    """

    DEFAULT_CONFIG_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "rules_config.yaml"
    )

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config: Optional[Dict[str, Any]] = None
        self._rules: List[Dict[str, Any]] = []
        self._load_config()

    # ------------------------------------------------------------------
    # Config loading
    # ------------------------------------------------------------------

    def _load_config(self) -> None:
        with open(self.config_path, "r") as f:
            raw = yaml.safe_load(f)
        # Config has top-level "rules_engine" key; flatten it
        self._config = raw.get("rules_engine", raw)
        self._rules = [
            r for r in self._config.get("rules", []) if r.get("enabled", True)
        ]

    def reload(self) -> None:
        """Reload rules configuration from disk."""
        self._load_config()

    @property
    def rules(self) -> List[Dict[str, Any]]:
        return list(self._rules)

    # ------------------------------------------------------------------
    # Main evaluation entry point
    # ------------------------------------------------------------------

    def evaluate(self, event: AuditEvent) -> EvaluationResult:
        """
        Evaluate all enabled rules against the given audit event.

        Args:
            event: The audit event to evaluate.

        Returns:
            EvaluationResult with triggered rules, risk score, and flags.
        """
        triggered: List[TriggeredRule] = []

        for rule_cfg in self._rules:
            rule_id = rule_cfg["id"]
            result = self._evaluate_rule(rule_id, rule_cfg, event)
            if result is not None:
                triggered.append(result)

        # Calculate risk score
        risk_score = self._calculate_risk_score(triggered, event)

        # Determine flags
        auto_block = any(r.auto_block for r in triggered)
        requires_human_review = auto_block or risk_score >= 70

        return EvaluationResult(
            event_id=event.event_id,
            triggered_rules=triggered,
            risk_score=risk_score,
            requires_human_review=requires_human_review,
            auto_block=auto_block,
        )

    # ------------------------------------------------------------------
    # Individual rule evaluators
    # ------------------------------------------------------------------

    def _evaluate_rule(
        self, rule_id: str, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        """Dispatch to the correct rule evaluator by rule_id."""
        evaluators = {
            "RULE-001": self._eval_rule_001,
            "RULE-002": self._eval_rule_002,
            "RULE-003": self._eval_rule_003,
            "RULE-004": self._eval_rule_004,
            "RULE-005": self._eval_rule_005,
            "RULE-006": self._eval_rule_006,
            "RULE-007": self._eval_rule_007,
            "RULE-008": self._eval_rule_008,
            "RULE-009": self._eval_rule_009,
            "RULE-010": self._eval_rule_010,
            "RULE-011": self._eval_rule_011,
            "RULE-012": self._eval_rule_012,
            "RULE-013": self._eval_rule_013,
            "RULE-014": self._eval_rule_014,
            "RULE-015": self._eval_rule_015,
        }
        evaluator = evaluators.get(rule_id)
        if evaluator is None:
            return None
        return evaluator(rule_cfg, event)

    # ----- RULE-001: PII Leakage in Output -----
    def _eval_rule_001(
        self, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        output = event.output_summary
        if not output.pii_detected:
            return None

        sensitive = set(
            self._config.get("sensitive_pii_categories", [])
        )
        event_pii_types = set(output.pii_types or [])
        leaked_sensitive = event_pii_types & sensitive

        if not leaked_sensitive:
            return None

        return TriggeredRule(
            rule_id="RULE-001",
            name=rule_cfg["name"],
            description=rule_cfg["description"],
            severity=Severity.CRITICAL,
            message=(
                f"Sensitive PII leaked in output: {', '.join(sorted(leaked_sensitive))}. "
                f"Output PII types: {sorted(event_pii_types)}"
            ),
            articles=rule_cfg.get("articles", []),
            auto_block=rule_cfg.get("auto_block", True),
        )

    # ----- RULE-002: Decision Without User Consent -----
    def _eval_rule_002(
        self, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        consent = event.consent_flags
        if consent is None:
            return None
        if consent.user_consent_obtained:
            return None
        if consent.consent_type.value != "none":
            return None

        # Check if action involves personal data
        personal_actions = {
            ActionType.DECISION, ActionType.APPROVE, ActionType.REJECT,
            ActionType.DATA_ACCESS, ActionType.DATA_WRITE, ActionType.DATA_DELETE,
            ActionType.CLASSIFY, ActionType.RECOMMEND,
        }
        if event.action_type not in personal_actions:
            return None

        return TriggeredRule(
            rule_id="RULE-002",
            name=rule_cfg["name"],
            description=rule_cfg["description"],
            severity=Severity.VIOLATION,
            message=(
                f"Action '{event.action_type.value}' performed without user consent "
                f"(consent_type: none) on personal data."
            ),
            articles=rule_cfg.get("articles", []),
            auto_block=rule_cfg.get("auto_block", True),
        )

    # ----- RULE-003: Low Confidence Decision -----
    def _eval_rule_003(
        self, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        threshold = rule_cfg.get("threshold", 0.70)
        high_stakes_actions = {
            ActionType.APPROVE, ActionType.DECISION, ActionType.ESCALATE,
        }
        if event.action_type not in high_stakes_actions:
            return None

        confidence = event.confidence_score
        if confidence is None:
            confidence = event.output_summary.confidence_score
        if confidence is None or confidence >= threshold:
            return None

        return TriggeredRule(
            rule_id="RULE-003",
            name=rule_cfg["name"],
            description=rule_cfg["description"],
            severity=Severity.WARNING,
            message=(
                f"Low confidence ({confidence:.2f} < {threshold}) for "
                f"high-stakes action '{event.action_type.value}'."
            ),
            articles=rule_cfg.get("articles", []),
            auto_block=rule_cfg.get("auto_block", False),
        )

    # ----- RULE-004: Unauthorized Data Access -----
    def _eval_rule_004(
        self, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        lineage = event.data_lineage
        if lineage is None:
            return None

        unauthorized = [
            src for src in lineage.sources_accessed
            if src.authorization_verified is False
        ]
        if not unauthorized:
            return None

        sources_str = ", ".join(s.source_id for s in unauthorized)
        return TriggeredRule(
            rule_id="RULE-004",
            name=rule_cfg["name"],
            description=rule_cfg["description"],
            severity=Severity.CRITICAL,
            message=(
                f"Unauthorized data access detected for sources: {sources_str}. "
                f"{len(unauthorized)} source(s) without verified authorization."
            ),
            articles=rule_cfg.get("articles", []),
            auto_block=rule_cfg.get("auto_block", True),
        )

    # ----- RULE-005: Data Retention Exceeded -----
    def _eval_rule_005(
        self, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        lineage = event.data_lineage
        if lineage is None or lineage.retention_policy is None:
            return None

        policies = self._config.get("retention_policies", {})
        retention_key = lineage.retention_policy
        max_days = policies.get(retention_key, policies.get("default", 730))

        try:
            event_dt = datetime.fromisoformat(
                event.timestamp.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            return None

        age_days = (datetime.now(timezone.utc) - event_dt).days
        if age_days <= max_days:
            return None

        return TriggeredRule(
            rule_id="RULE-005",
            name=rule_cfg["name"],
            description=rule_cfg["description"],
            severity=Severity.VIOLATION,
            message=(
                f"Data retention exceeded for policy '{retention_key}': "
                f"age={age_days}d, max={max_days}d."
            ),
            articles=rule_cfg.get("articles", []),
            auto_block=rule_cfg.get("auto_block", False),
        )

    # ----- RULE-006: High-Risk Without Human Oversight -----
    def _eval_rule_006(
        self, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        risk_threshold = rule_cfg.get("risk_threshold", 70)
        if event.risk_score < risk_threshold:
            return None

        if event.human_review is not None and event.human_review.review_decision is not None:
            return None

        return TriggeredRule(
            rule_id="RULE-006",
            name=rule_cfg["name"],
            description=rule_cfg["description"],
            severity=Severity.VIOLATION,
            message=(
                f"High-risk event (score={event.risk_score}) without human review. "
                f"Risk threshold: {risk_threshold}."
            ),
            articles=rule_cfg.get("articles", []),
            auto_block=rule_cfg.get("auto_block", True),
        )

    # ----- RULE-007: Off-Policy Action -----
    def _eval_rule_007(
        self, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        allowlists = self._config.get("agent_allowlists", {})
        allowed = allowlists.get(
            event.agent_name,
            allowlists.get("__default__", []),
        )
        if event.action_type.value in allowed:
            return None

        return TriggeredRule(
            rule_id="RULE-007",
            name=rule_cfg["name"],
            description=rule_cfg["description"],
            severity=Severity.VIOLATION,
            message=(
                f"Action '{event.action_type.value}' is not in the allowlist "
                f"for agent '{event.agent_name}'."
            ),
            articles=rule_cfg.get("articles", []),
            auto_block=rule_cfg.get("auto_block", True),
        )

    # ----- RULE-008: Cross-Border Data Transfer -----
    def _eval_rule_008(
        self, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        lineage = event.data_lineage
        if lineage is None:
            return None

        adequate = set(self._config.get("adequate_jurisdictions", []))
        metadata = event.metadata or {}
        has_scc = metadata.get("data_transfer_mechanism", "").upper() in (
            "SCC", "STANDARD_CONTRACTUAL_CLAUSES", "BCR", "ADEQUACY"
        )

        # Check if any source is from a non-adequate jurisdiction
        non_adequate_sources = []
        for src in lineage.sources_accessed:
            src_jurisdiction = metadata.get("jurisdiction", "EU")
            if src_jurisdiction not in adequate and not has_scc:
                non_adequate_sources.append(src.source_id)

        if not non_adequate_sources:
            return None

        return TriggeredRule(
            rule_id="RULE-008",
            name=rule_cfg["name"],
            description=rule_cfg["description"],
            severity=Severity.WARNING,
            message=(
                f"Cross-border data transfer detected from sources: "
                f"{', '.join(non_adequate_sources)}. "
                f"No adequacy decision or SCC mechanism flagged."
            ),
            articles=rule_cfg.get("articles", []),
            auto_block=rule_cfg.get("auto_block", False),
        )

    # ----- RULE-009: Model Version Deprecated -----
    def _eval_rule_009(
        self, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        approved = set(self._config.get("approved_models", []))
        if event.model_version in approved:
            return None

        return TriggeredRule(
            rule_id="RULE-009",
            name=rule_cfg["name"],
            description=rule_cfg["description"],
            severity=Severity.WARNING,
            message=(
                f"Model version '{event.model_version}' is not in the approved "
                f"model registry."
            ),
            articles=rule_cfg.get("articles", []),
            auto_block=rule_cfg.get("auto_block", False),
        )

    # ----- RULE-010: Excessive Data Collection -----
    def _eval_rule_010(
        self, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        lineage = event.data_lineage
        if lineage is None:
            return None

        max_sources = rule_cfg.get("max_sources_per_event", 10)
        max_records = rule_cfg.get("max_records_per_event", 1000)

        num_sources = len(lineage.sources_accessed)
        total_records = sum(
            (s.records_affected or 0) for s in lineage.sources_accessed
        )

        if num_sources <= max_sources and total_records <= max_records:
            return None

        details = []
        if num_sources > max_sources:
            details.append(f"sources={num_sources} > max={max_sources}")
        if total_records > max_records:
            details.append(f"records={total_records} > max={max_records}")

        return TriggeredRule(
            rule_id="RULE-010",
            name=rule_cfg["name"],
            description=rule_cfg["description"],
            severity=Severity.WARNING,
            message=f"Excessive data collection: {'; '.join(details)}.",
            articles=rule_cfg.get("articles", []),
            auto_block=rule_cfg.get("auto_block", False),
        )

    # ----- RULE-011: Consent Scope Mismatch -----
    def _eval_rule_011(
        self, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        consent = event.consent_flags
        if consent is None or consent.consent_scope is None:
            return None

        required_scopes = self._config.get("required_consopes", {})
        # Fix key name
        required_scopes = self._config.get("required_consent_scopes", {})
        action_key = event.action_type.value
        required = set(required_scopes.get(action_key, required_scopes.get("default", [])))
        current = set(consent.consent_scope)

        missing = required - current
        if not missing:
            return None

        return TriggeredRule(
            rule_id="RULE-011",
            name=rule_cfg["name"],
            description=rule_cfg["description"],
            severity=Severity.VIOLATION,
            message=(
                f"Consent scope mismatch for action '{action_key}': "
                f"missing scopes: {sorted(missing)}. "
                f"Current scopes: {sorted(current)}."
            ),
            articles=rule_cfg.get("articles", []),
            auto_block=rule_cfg.get("auto_block", True),
        )

    # ----- RULE-012: Right to Explanation Not Available -----
    def _eval_rule_012(
        self, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        if event.action_type != ActionType.DECISION:
            return None

        consent = event.consent_flags
        if consent is None:
            return None
        if consent.right_to_explanation is not False:
            return None

        return TriggeredRule(
            rule_id="RULE-012",
            name=rule_cfg["name"],
            description=rule_cfg["description"],
            severity=Severity.VIOLATION,
            message=(
                "Right to explanation not available for decision action "
                f"by agent '{event.agent_name}'. Decision: "
                f"{event.output_summary.decision[:100]}"
            ),
            articles=rule_cfg.get("articles", []),
            auto_block=rule_cfg.get("auto_block", True),
        )

    # ----- RULE-013: Anomalous Decision Rate -----
    def _eval_rule_013(
        self, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        # This rule requires external state (rate tracking).
        # We check for a rate annotation in metadata.
        metadata = event.metadata or {}
        rate_str = metadata.get("agent_decisions_per_minute", "")
        if not rate_str:
            return None

        try:
            rate = float(rate_str)
        except (ValueError, TypeError):
            return None

        rate_limit = rule_cfg.get("rate_limit_per_minute", 50)
        if rate <= rate_limit:
            return None

        return TriggeredRule(
            rule_id="RULE-013",
            name=rule_cfg["name"],
            description=rule_cfg["description"],
            severity=Severity.WARNING,
            message=(
                f"Anomalous decision rate: {rate}/min exceeds limit of "
                f"{rate_limit}/min for agent '{event.agent_name}'."
            ),
            articles=rule_cfg.get("articles", []),
            auto_block=rule_cfg.get("auto_block", False),
        )

    # ----- RULE-014: Sensitive Category Processing -----
    def _eval_rule_014(
        self, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        input_pii = set(event.input_summary.pii_types or [])
        special = set(
            self._config.get("special_category_types", [])
        )
        found = input_pii & special
        if not found:
            return None

        # Check for explicit consent for special categories
        consent = event.consent_flags
        if consent is not None and consent.consent_scope:
            scopes = set(consent.consent_scope)
            if "special_category_processing" in scopes and consent.consent_type.value == "explicit":
                return None

        return TriggeredRule(
            rule_id="RULE-014",
            name=rule_cfg["name"],
            description=rule_cfg["description"],
            severity=Severity.CRITICAL,
            message=(
                f"Sensitive category data processed without explicit consent: "
                f"{sorted(found)}. Input PII types: {sorted(input_pii)}."
            ),
            articles=rule_cfg.get("articles", []),
            auto_block=rule_cfg.get("auto_block", True),
        )

    # ----- RULE-015: Audit Log Tampering Detected -----
    def _eval_rule_015(
        self, rule_cfg: Dict[str, Any], event: AuditEvent
    ) -> Optional[TriggeredRule]:
        metadata = event.metadata or {}

        # Check for hash chain integrity flag
        hash_chain_ok = metadata.get("hash_chain_verified", "true")
        if str(hash_chain_ok).lower() in ("false", "0", "no"):
            return TriggeredRule(
                rule_id="RULE-015",
                name=rule_cfg["name"],
                description=rule_cfg["description"],
                severity=Severity.CRITICAL,
                message=(
                    f"Audit log hash chain integrity check FAILED for event "
                    f"{event.event_id}. Potential tampering detected."
                ),
                articles=rule_cfg.get("articles", []),
                auto_block=rule_cfg.get("auto_block", True),
            )

        # Check for sequence gap flag
        sequence_gap = metadata.get("event_sequence_gap", "false")
        if str(sequence_gap).lower() in ("true", "1", "yes"):
            return TriggeredRule(
                rule_id="RULE-015",
                name=rule_cfg["name"],
                description=rule_cfg["description"],
                severity=Severity.CRITICAL,
                message=(
                    f"Event ID sequence gap detected for event {event.event_id}. "
                    f"Audit log may have been tampered with."
                ),
                articles=rule_cfg.get("articles", []),
                auto_block=rule_cfg.get("auto_block", True),
            )

        return None

    # ------------------------------------------------------------------
    # Risk score calculation
    # ------------------------------------------------------------------

    def _calculate_risk_score(
        self, triggered: List[TriggeredRule], event: AuditEvent
    ) -> float:
        """
        Calculate overall risk score (0-100) based on triggered rules.

        Uses severity weights with diminishing returns for multiple
        rules of the same severity, plus the event's base risk_score.
        """
        if not triggered:
            return event.risk_score

        # Sum severity weights with diminishing returns
        score = 0.0
        severity_counts: Dict[Severity, int] = {}
        for rule in triggered:
            severity_counts[rule.severity] = severity_counts.get(rule.severity, 0) + 1

        for sev, count in severity_counts.items():
            weight = SEVERITY_WEIGHTS[sev]
            # Diminishing returns: first rule gets full weight,
            # subsequent rules get 50% of the previous
            for i in range(count):
                score += weight * (0.5 ** i)

        # Blend with event's base risk_score (60% triggered rules, 40% base)
        blended = 0.6 * score + 0.4 * event.risk_score

        return min(100.0, round(blended, 2))

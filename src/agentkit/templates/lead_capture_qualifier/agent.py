"""Lead Capture & Qualifier — Template for AgentsFactory.

Captures leads from web forms, scores them via AI qualification,
stores in SQLite CRM, and sends Slack alerts for hot leads.

Usage:
    python src/agentkit/templates/lead_capture_qualifier/agent.py --dry-run
    python src/agentkit/templates/lead_capture_qualifier/agent.py --config my_config.yaml
    python src/agentkit/templates/lead_capture_qualifier/agent.py --dry-run --json

All activity is logged to agent_activity table in agentsfactory_metrics.db.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import yaml  # type: ignore

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "agentsfactory_metrics.db"
AGENT_NAME = "lead_capture_qualifier"

# ---------------------------------------------------------------------------
# Simulated incoming leads (replace with form/email ingestion in production)
# ---------------------------------------------------------------------------
SIMULATED_LEADS = [
    {
        "name": "Sarah Chen",
        "email": "sarah@techscale.io",
        "company": "TechScale",
        "phone": "+1-555-0101",
        "source": "web_form",
        "budget": 8000,
        "timeline_months": 1,
        "company_size": 75,
        "industry": "saas",
        "message": "Looking for automation for our onboarding workflow. Need it ASAP.",
    },
    {
        "name": "Mike Johnson",
        "email": "mike@localgym.com",
        "company": "FitLife Gym",
        "phone": "+1-555-0202",
        "source": "email",
        "budget": 500,
        "timeline_months": 6,
        "company_size": 8,
        "industry": "local_business",
        "message": "Might be interested in automating appointment scheduling.",
    },
    {
        "name": "Priya Patel",
        "email": "priya@shopbazaar.in",
        "company": "ShopBazaar",
        "phone": "+91-98765-43210",
        "source": "referral",
        "budget": 12000,
        "timeline_months": 1,
        "company_size": 120,
        "industry": "ecommerce",
        "message": "We process 500+ orders/day manually. Need full automation. Referred by TechScale.",
    },
    {
        "name": "Alex Rivera",
        "email": "alex@unknown.com",
        "company": "Freelance",
        "phone": "",
        "source": "linkedin",
        "budget": 200,
        "timeline_months": 12,
        "company_size": 1,
        "industry": "other",
        "message": "Just exploring options, no rush.",
    },
    {
        "name": "David Kim",
        "email": "david@healthplus.com",
        "company": "HealthPlus Clinic",
        "phone": "+1-555-0303",
        "source": "inbound_call",
        "budget": 3500,
        "timeline_months": 2,
        "company_size": 25,
        "industry": "healthcare",
        "message": "Need patient intake automation and appointment reminders.",
    },
]


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db(db_path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path or DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_tables(crm_path: Path | None = None) -> None:
    # Ensure agent_activity table in metrics DB
    conn = get_db()
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS agent_activity ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, agent_name TEXT NOT NULL, "
        "action TEXT NOT NULL, target TEXT DEFAULT '', "
        "status TEXT DEFAULT 'completed', details TEXT DEFAULT '', "
        "created_at TEXT DEFAULT (datetime('now')));"
    )
    conn.commit()
    conn.close()

    # Ensure leads table in CRM DB
    crm = get_db(crm_path)
    crm.executescript(
        "CREATE TABLE IF NOT EXISTS leads ("
        "id TEXT PRIMARY KEY, name TEXT, company TEXT, email TEXT, "
        "phone TEXT, source TEXT DEFAULT 'inbound', stage TEXT DEFAULT 'new', "
        "score INTEGER DEFAULT 0, notes TEXT DEFAULT '', "
        "created_at TEXT DEFAULT (datetime('now')), "
        "updated_at TEXT DEFAULT (datetime('now')));"
    )
    crm.commit()
    crm.close()


def log_activity(action: str, target: str = "", status: str = "completed", details: str = "") -> None:
    conn = get_db()
    conn.execute(
        "INSERT INTO agent_activity (agent_name, action, target, status, details) "
        "VALUES (?, ?, ?, ?, ?)",
        (AGENT_NAME, action, target, status, details),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config(config_path: Path | None = None) -> dict:
    if config_path is None:
        config_path = Path(__file__).resolve().parent / "config.yaml"
    if not config_path.exists():
        print(f"⚠️  Config not found at {config_path}, using defaults")
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

def score_budget(budget: int) -> int:
    if budget >= 5000:
        return 30
    elif budget >= 1000:
        return 15
    return 5


def score_timeline(months: int) -> int:
    if months <= 1:
        return 25
    elif months <= 3:
        return 15
    return 5


def score_company_size(size: int) -> int:
    if size >= 50:
        return 20
    elif size >= 10:
        return 12
    return 5


def score_industry(industry: str) -> int:
    target = {"ecommerce", "saas", "local_business"}
    related = {"healthcare", "education", "agency"}
    if industry in target:
        return 15
    if industry in related:
        return 8
    return 0


def score_engagement(source: str) -> int:
    scores = {"referral": 10, "inbound_call": 8, "web_form": 6, "email": 4, "linkedin": 3}
    return scores.get(source, 2)


def score_lead(lead: dict) -> dict:
    """Score a lead and return breakdown."""
    breakdown = {
        "budget": score_budget(lead.get("budget", 0)),
        "timeline": score_timeline(lead.get("timeline_months", 99)),
        "company_size": score_company_size(lead.get("company_size", 1)),
        "industry_fit": score_industry(lead.get("industry", "other")),
        "engagement": score_engagement(lead.get("source", "cold")),
    }
    total = sum(v for v in breakdown.values())
    breakdown["total"] = total
    return breakdown


# ---------------------------------------------------------------------------
# CRM operations
# ---------------------------------------------------------------------------

def upsert_lead(lead: dict, score: int, crm_path: Path, dry_run: bool) -> str:
    """Insert or update a lead in the CRM table."""
    lead_id = f"lead_{uuid.uuid4().hex[:12]}"
    if dry_run:
        return lead_id

    conn = get_db(crm_path)
    conn.execute(
        "INSERT OR REPLACE INTO leads (id, name, company, email, phone, source, stage, score, notes, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            lead_id,
            lead.get("name", ""),
            lead.get("company", ""),
            lead.get("email", ""),
            lead.get("phone", ""),
            lead.get("source", "inbound"),
            "qualified" if score >= 70 else "new",
            score,
            lead.get("message", ""),
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return lead_id


# ---------------------------------------------------------------------------
# Notification stubs
# ---------------------------------------------------------------------------

def send_slack_alert(webhook_url: str, lead: dict, score: int) -> dict:
    """Send hot lead alert to Slack."""
    if not webhook_url:
        return {"status": "skipped", "reason": "no webhook configured"}
    message = (
        f"🔥 *Hot Lead Alert!*\n"
        f"• Name: {lead.get('name', 'Unknown')}\n"
        f"• Company: {lead.get('company', 'N/A')}\n"
        f"• Score: {score}/100\n"
        f"• Budget: ${lead.get('budget', 0):,}\n"
        f"• Timeline: {lead.get('timeline_months', '?')} months\n"
        f"• Source: {lead.get('source', 'unknown')}"
    )
    # In production: requests.post(webhook_url, json={"text": message})
    return {"status": "simulated", "message": message}


# ---------------------------------------------------------------------------
# Main qualifier logic
# ---------------------------------------------------------------------------

def run_qualifier(config: dict, dry_run: bool) -> dict:
    """Process all incoming leads."""
    print(f"\n🎯 Lead Capture & Qualifier")
    print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"   Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    hot_threshold = config.get("hot_leader_threshold", 70)
    crm_path = PROJECT_ROOT / config.get("crm_db_path", "data/leads.db")
    crm_path.parent.mkdir(parents=True, exist_ok=True)

    leads = SIMULATED_LEADS
    results = []
    hot_leads = []

    for lead in leads:
        breakdown = score_lead(lead)
        total = breakdown["total"]
        is_hot = total >= hot_threshold

        lead_id = upsert_lead(lead, total, crm_path, dry_run)

        status_icon = "🔥" if is_hot else ("📋" if total >= 40 else "❄️")
        print(f"   {status_icon} {lead['name']} ({lead['company']}) — Score: {total}/100")
        print(f"      Budget: +{breakdown['budget']}  Timeline: +{breakdown['timeline']}  "
              f"Size: +{breakdown['company_size']}  Industry: +{breakdown['industry_fit']}  "
              f"Engagement: +{breakdown['engagement']}")

        if is_hot:
            hot_leads.append({"lead": lead, "score": total, "id": lead_id})
            print(f"      ⚡ HOT LEAD — Slack alert triggered")

        results.append({
            "id": lead_id,
            "name": lead["name"],
            "company": lead["company"],
            "score": total,
            "is_hot": is_hot,
            "breakdown": breakdown,
        })

    # Send Slack alerts for hot leads
    slack_webhook = config.get("slack_webhook", "")
    for hot in hot_leads:
        result = send_slack_alert(slack_webhook, hot["lead"], hot["score"])
        log_activity(
            "hot_lead_alert",
            f"{hot['lead']['name']} ({hot['lead']['company']})",
            result["status"],
            f"Score: {hot['score']}",
        )

    # Summary
    print(f"\n   Summary: {len(leads)} leads processed, {len(hot_leads)} hot leads")
    avg_score = sum(r["score"] for r in results) / len(results) if results else 0
    print(f"   Average score: {avg_score:.1f}/100")

    log_activity(
        "lead_qualifier_run",
        f"{len(leads)} leads processed",
        "completed",
        f"Hot: {len(hot_leads)}, Avg score: {avg_score:.1f}, Mode: {'dry_run' if dry_run else 'live'}",
    )

    return {
        "leads_processed": len(leads),
        "hot_leads": len(hot_leads),
        "average_score": round(avg_score, 1),
        "results": results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lead_capture_qualifier",
        description="Lead Capture & Qualifier — Score leads and alert on hot prospects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python src/agentkit/templates/lead_capture_qualifier/agent.py --dry-run
  python src/agentkit/templates/lead_capture_qualifier/agent.py --config my_config.yaml
  python src/agentkit/templates/lead_capture_qualifier/agent.py --dry-run --json
""",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process leads without writing to CRM (default mode)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config YAML file (default: config.yaml in template directory)",
    )
    parser.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Output results as JSON",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)

    crm_path = PROJECT_ROOT / config.get("crm_db_path", "data/leads.db")
    ensure_tables(crm_path)

    dry_run = True  # Safe default
    if args.dry_run:
        dry_run = True

    result = run_qualifier(config, dry_run)

    if args.output_json:
        print(json.dumps(result, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()

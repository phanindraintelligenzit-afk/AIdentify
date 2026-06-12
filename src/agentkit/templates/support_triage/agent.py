"""Customer Support Triage — Template for AgentsFactory.

Reads incoming messages, classifies urgency, drafts responses,
queues for human review, and tracks response time metrics.

Usage:
    python src/agentkit/templates/support_triage/agent.py --dry-run
    python src/agentkit/templates/support_triage/agent.py --config my_config.yaml
    python src/agentkit/templates/support_triage/agent.py --json

All activity is logged to agent_activity table in agentsfactory_metrics.db.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import yaml  # type: ignore

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "agentsfactory_metrics.db"
AGENT_NAME = "support_triage"

# ---------------------------------------------------------------------------
# Simulated incoming messages (replace with email/API in production)
# ---------------------------------------------------------------------------
SIMULATED_MESSAGES = [
    {
        "id": "msg_001",
        "from": "john@example.com",
        "name": "John Smith",
        "subject": "URGENT: My order hasn't arrived!",
        "body": "Hi, I placed an order 2 weeks ago and it still hasn't arrived. "
                "The tracking shows no updates for 5 days. This is urgent, I need it by Friday. "
                "Order #12345. Please help!",
        "channel": "email",
        "received_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
    },
    {
        "id": "msg_002",
        "from": "sarah@techscale.io",
        "name": "Sarah Chen",
        "subject": "Bug: API integration failing",
        "body": "Hello, our integration with your API has been timing out since this morning. "
                "Error: 504 Gateway Timeout. This is critical — our production system is down. "
                "Please escalate to engineering immediately.",
        "channel": "email",
        "received_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
    },
    {
        "id": "msg_003",
        "from": "mike@localgym.com",
        "name": "Mike Johnson",
        "subject": "Question about billing",
        "body": "Hi there, I was wondering when my next subscription payment will be charged? "
                "I want to make sure my card is up to date. Thanks!",
        "channel": "email",
        "received_at": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
    },
    {
        "id": "msg_004",
        "from": "alex@unknown.com",
        "name": "Alex Rivera",
        "subject": "Feature request: Dark mode",
        "body": "Hey! Love the product. Any plans to add dark mode? "
                "It would be great for late-night coding sessions. Thanks for the great work!",
        "channel": "email",
        "received_at": (datetime.utcnow() - timedelta(hours=12)).isoformat(),
    },
    {
        "id": "msg_005",
        "from": "lisa@complaint.com",
        "name": "Lisa Park",
        "subject": "Complaint: Wrong item received",
        "body": "I received the wrong item in my order. I ordered a Widget Pro but got a Gadget Mini. "
                "This is very frustrating. I want a refund or the correct item sent immediately. "
                "Order #67890. I'm considering a chargeback if this isn't resolved.",
        "channel": "email",
        "received_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
    },
]


# ---------------------------------------------------------------------------
# Response time tracker (in-memory for template; DB in production)
# ---------------------------------------------------------------------------
_response_times: list[float] = []


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_tables() -> None:
    conn = get_db()
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS agent_activity ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, agent_name TEXT NOT NULL, "
        "action TEXT NOT NULL, target TEXT DEFAULT '', "
        "status TEXT DEFAULT 'completed', details TEXT DEFAULT '', "
        "created_at TEXT DEFAULT (datetime('now')));"
        ""
        "CREATE TABLE IF NOT EXISTS support_queue ("
        "id TEXT PRIMARY KEY, message_id TEXT, customer_name TEXT, "
        "customer_email TEXT, subject TEXT, body TEXT, "
        "urgency TEXT DEFAULT 'medium', category TEXT DEFAULT 'general', "
        "response_draft TEXT DEFAULT '', status TEXT DEFAULT 'pending_review', "
        "sla_deadline TEXT, created_at TEXT DEFAULT (datetime('now')), "
        "assigned_to TEXT DEFAULT '');"
    )
    conn.commit()
    conn.close()


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
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# Classification engine
# ---------------------------------------------------------------------------

def classify_urgency(message: dict, config: dict) -> str:
    """Classify urgency using keyword matching + heuristics."""
    text = f"{message.get('subject', '')} {message.get('body', '')}".lower()
    urgency_config = config.get("urgency", {})

    # Check critical first (highest priority)
    for keyword in urgency_config.get("critical", {}).get("keywords", []):
        if keyword.lower() in text:
            return "critical"

    # Check multiple high keywords (2+ = critical)
    high_keywords = urgency_config.get("high", {}).get("keywords", [])
    high_matches = sum(1 for kw in high_keywords if kw.lower() in text)
    if high_matches >= 3:
        return "critical"

    # Check high
    for keyword in high_keywords:
        if keyword.lower() in text:
            return "high"

    # Check medium
    for keyword in urgency_config.get("medium", {}).get("keywords", []):
        if keyword.lower() in text:
            return "medium"

    # Check for exclamation marks / caps (heuristic boost)
    subject = message.get("subject", "")
    if subject.isupper() or subject.count("!") >= 2:
        return "high"

    # Default to low
    return "low"


def classify_category(message: dict, config: dict) -> str:
    """Classify message into a support category."""
    text = f"{message.get('subject', '')} {message.get('body', '')}".lower()
    categories = config.get("categories", {})

    best_category = "general"
    best_score = 0

    for cat_name, cat_config in categories.items():
        keywords = cat_config.get("keywords", [])
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > best_score:
            best_score = score
            best_category = cat_name

    return best_category


def generate_response_draft(message: dict, category: str, config: dict) -> str:
    """Generate a response draft based on category template."""
    templates = config.get("response_templates", {})
    template = templates.get(category, templates.get("general", "Hi {name},\n\n{resolution}\n\nBest regards,\nSupport Team"))

    resolution_placeholder = (
        f"[DRAFT — Please customize based on investigation]\n"
        f"Original message: {message.get('body', '')[:200]}..."
    )

    return template.format(
        name=message.get("name", "there"),
        order_id="[ORDER_ID]",
        resolution=resolution_placeholder,
    )


def compute_sla_deadline(urgency: str, config: dict) -> str:
    """Compute SLA deadline based on urgency level."""
    urgency_config = config.get("urgency", {})
    sla_hours = urgency_config.get(urgency, {}).get("sla_hours", 24)
    deadline = datetime.utcnow() + timedelta(hours=sla_hours)
    return deadline.isoformat()


# ---------------------------------------------------------------------------
# Notification stubs
# ---------------------------------------------------------------------------

def send_critical_alert(webhook_url: str, message: dict, urgency: str) -> dict:
    """Send critical ticket alert to Slack."""
    if not webhook_url:
        return {"status": "skipped", "reason": "no webhook configured"}
    alert = (
        f"🚨 *CRITICAL Support Ticket*\n"
        f"• From: {message.get('name', 'Unknown')} ({message.get('from', '')})\n"
        f"• Subject: {message.get('subject', 'N/A')}\n"
        f"• Urgency: {urgency}\n"
        f"• Channel: {message.get('channel', 'email')}"
    )
    return {"status": "simulated", "message": alert}


# ---------------------------------------------------------------------------
# Main triage logic
# ---------------------------------------------------------------------------

def run_triage(config: dict, dry_run: bool) -> dict:
    """Process all incoming support messages."""
    print(f"\n🎧 Customer Support Triage")
    print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"   Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    messages = SIMULATED_MESSAGES
    results = []
    urgency_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    category_counts: dict[str, int] = {}

    notifications = config.get("notifications", {})
    slack_webhook = notifications.get("slack_webhook", "")

    for msg in messages:
        urgency = classify_urgency(msg, config)
        category = classify_category(msg, config)
        response_draft = generate_response_draft(msg, category, config)
        sla_deadline = compute_sla_deadline(urgency, config)

        urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1

        queue_id = f"ticket_{uuid.uuid4().hex[:10]}"

        # Write to queue (unless dry run)
        if not dry_run:
            conn = get_db()
            conn.execute(
                "INSERT INTO support_queue "
                "(id, message_id, customer_name, customer_email, subject, body, "
                "urgency, category, response_draft, sla_deadline) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    queue_id, msg["id"], msg["name"], msg["from"],
                    msg["subject"], msg["body"][:500],
                    urgency, category, response_draft[:1000], sla_deadline,
                ),
            )
            conn.commit()
            conn.close()

        # Alert on critical
        if urgency == "critical" and notifications.get("alert_on_critical", True):
            send_critical_alert(slack_webhook, msg, urgency)

        urgency_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(urgency, "⚪")
        print(f"   {urgency_icon} [{urgency.upper():8s}] [{category:14s}] {msg['subject']}")
        print(f"      From: {msg['name']} ({msg['from']})")
        print(f"      SLA: {sla_deadline}")
        print(f"      Draft: {response_draft[:80].strip()}...")
        print()

        results.append({
            "queue_id": queue_id,
            "message_id": msg["id"],
            "urgency": urgency,
            "category": category,
            "sla_deadline": sla_deadline,
        })

    # Summary
    print(f"   Summary: {len(messages)} messages triaged")
    print(f"   Urgency:  🔴 Critical={urgency_counts['critical']}  "
          f"🟠 High={urgency_counts['high']}  "
          f"🟡 Medium={urgency_counts['medium']}  "
          f"🟢 Low={urgency_counts['low']}")
    print(f"   Categories: {', '.join(f'{k}={v}' for k, v in category_counts.items())}")

    # Response time metrics (simulated)
    avg_response_time = 2.5  # hours (simulated)
    sla_compliance = 0.92    # 92% within SLA (simulated)
    print(f"   Metrics: Avg response={avg_response_time}h, SLA compliance={sla_compliance:.0%}")

    log_activity(
        "support_triage_run",
        f"{len(messages)} messages triaged",
        "completed",
        f"Critical={urgency_counts['critical']}, High={urgency_counts['high']}, "
        f"Medium={urgency_counts['medium']}, Low={urgency_counts['low']}",
    )

    return {
        "messages_triaged": len(messages),
        "urgency_breakdown": urgency_counts,
        "category_breakdown": category_counts,
        "avg_response_time_hours": avg_response_time,
        "sla_compliance": sla_compliance,
        "results": results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="support_triage",
        description="Customer Support Triage — Classify, draft responses, and queue for review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python src/agentkit/templates/support_triage/agent.py --dry-run
  python src/agentkit/templates/support_triage/agent.py --config my_config.yaml
  python src/agentkit/templates/support_triage/agent.py --dry-run --json
""",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process messages without writing to queue (default mode)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config YAML file",
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
    ensure_tables()

    dry_run = args.dry_run or True

    result = run_triage(config, dry_run)

    if args.output_json:
        print(json.dumps(result, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()

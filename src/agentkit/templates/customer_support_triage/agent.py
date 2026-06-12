"""Customer Support Triage — Template for AgentsFactory.

Reads incoming emails/messages, classifies urgency via keyword matching,
drafts response templates, queues for human review, tracks response times.

Usage:
    python src/agentkit/templates/customer_support_triage/agent.py --dry-run
    python src/agentkit/templates/customer_support_triage/agent.py --config my_config.yaml
    python src/agentkit/templates/customer_support_triage/agent.py --dry-run --json

All activity is logged to agent_activity table in agentsfactory_metrics.db.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path

import yaml  # type: ignore

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "agentsfactory_metrics.db"
AGENT_NAME = "customer_support_triage"

# ---------------------------------------------------------------------------
# Simulated incoming messages (replace with email/API ingestion in production)
# ---------------------------------------------------------------------------
SIMULATED_MESSAGES = [
    {
        "id": "msg_001",
        "from": "alice@example.com",
        "subject": "URGENT: Production server is down",
        "body": "Our production server has been down for 30 minutes. Customers cannot access the platform. This is a critical outage. Please help immediately.",
        "received_at": "2026-06-12T08:15:00",
    },
    {
        "id": "msg_002",
        "from": "bob@example.com",
        "subject": "Refund request for order #4521",
        "body": "I would like to request a refund for my recent order. The product arrived broken and I need to cancel the purchase.",
        "received_at": "2026-06-12T09:30:00",
    },
    {
        "id": "msg_003",
        "from": "carol@example.com",
        "subject": "Question about billing",
        "body": "Hi, I have a question about my latest invoice. There seems to be a billing error on my account. Can you help?",
        "received_at": "2026-06-12T10:00:00",
    },
    {
        "id": "msg_004",
        "from": "dave@example.com",
        "subject": "Feature request: dark mode",
        "body": "Just wanted to send some feedback — it would be great if you added a dark mode option. Love the product overall!",
        "received_at": "2026-06-12T11:00:00",
    },
    {
        "id": "msg_005",
        "from": "eve@example.com",
        "subject": "Security breach — unauthorized access detected",
        "body": "We detected unauthorized access to our account. This is a security breach. Our data may be compromised. Need immediate assistance.",
        "received_at": "2026-06-12T11:45:00",
    },
    {
        "id": "msg_006",
        "from": "frank@example.com",
        "subject": "Bug report: checkout not working",
        "body": "I'm having an issue with the checkout page. It's broken and I can't complete my purchase. This is quite urgent.",
        "received_at": "2026-06-12T12:30:00",
    },
]

# Response templates per urgency tier
RESPONSE_TEMPLATES = {
    "critical": (
        "Hi there,\n\n"
        "Thank you for reaching out. We've flagged your message as CRITICAL and our "
        "engineering team has been notified. A senior support engineer will respond "
        "within 15 minutes.\n\n"
        "Ticket ID: {ticket_id}\n"
        "Priority: CRITICAL\n\n"
        "Best regards,\nSupport Team"
    ),
    "high": (
        "Hi there,\n\n"
        "Thank you for contacting us. Your message has been marked as HIGH priority "
        "and will be reviewed by our support team within 2 hours.\n\n"
        "Ticket ID: {ticket_id}\n"
        "Priority: HIGH\n\n"
        "Best regards,\nSupport Team"
    ),
    "medium": (
        "Hi there,\n\n"
        "Thanks for getting in touch. We've received your message and will get back "
        "to you within 24 hours.\n\n"
        "Ticket ID: {ticket_id}\n\n"
        "Best regards,\nSupport Team"
    ),
    "low": (
        "Hi there,\n\n"
        "Thank you for your message. We appreciate your feedback and will review it "
        "shortly.\n\n"
        "Ticket ID: {ticket_id}\n\n"
        "Best regards,\nSupport Team"
    ),
}

URGENCY_TIERS = ["critical", "high", "medium", "low"]


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
        print(f"⚠️  Config not found at {config_path}, using defaults")
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# Urgency classification
# ---------------------------------------------------------------------------

def classify_urgency(message: dict, keywords: dict) -> tuple[str, int, list[str]]:
    """Classify a message's urgency. Returns (tier, match_count, matched_keywords)."""
    text = f"{message.get('subject', '')} {message.get('body', '')}".lower()
    best_tier = "low"
    best_count = 0
    best_matches: list[str] = []

    for tier in URGENCY_TIERS:
        tier_keywords = keywords.get(tier, [])
        matches = [kw for kw in tier_keywords if kw.lower() in text]
        if matches and (best_count == 0 or URGENCY_TIERS.index(tier) < URGENCY_TIERS.index(best_tier)):
            best_tier = tier
            best_count = len(matches)
            best_matches = matches
        elif matches and tier == best_tier:
            best_count += len(matches)
            best_matches.extend(matches)

    return best_tier, best_count, best_matches


# ---------------------------------------------------------------------------
# Response drafting
# ---------------------------------------------------------------------------

def draft_response(message: dict, urgency: str, ticket_id: str) -> str:
    """Generate a response template for the given urgency level."""
    template = RESPONSE_TEMPLATES.get(urgency, RESPONSE_TEMPLATES["low"])
    return template.format(ticket_id=ticket_id)


# ---------------------------------------------------------------------------
# Human review queue
# ---------------------------------------------------------------------------

def queue_for_review(queue_path: Path, item: dict, dry_run: bool) -> None:
    """Add an item to the human review queue JSON file."""
    queue: list[dict] = []
    if queue_path.exists():
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
    queue.append(item)
    if not dry_run:
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        queue_path.write_text(json.dumps(queue, indent=2, default=str), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main triage logic
# ---------------------------------------------------------------------------

def run_triage(config: dict, dry_run: bool) -> dict:
    """Run the support triage pass."""
    print(f"\n🎧 Customer Support Triage")
    print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"   Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    keywords = config.get("urgency_keywords", {})
    review_queue_path = PROJECT_ROOT / config.get(
        "human_review_queue_path", "data/human_review_queue.json"
    )

    messages = SIMULATED_MESSAGES
    results = []
    review_queue_items = []
    tier_counts = {tier: 0 for tier in URGENCY_TIERS}
    response_times: list[float] = []

    for msg in messages:
        urgency, match_count, matched_kws = classify_urgency(msg, keywords)
        ticket_id = f"TKT-{msg['id'].upper()}"
        response_text = draft_response(msg, urgency, ticket_id)
        tier_counts[urgency] += 1

        # Simulate response time based on urgency (minutes)
        response_time_map = {"critical": 15, "high": 120, "medium": 1440, "low": 2880}
        est_response_time = response_time_map.get(urgency, 2880)
        response_times.append(est_response_time)

        needs_review = urgency in ("critical", "high")

        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(urgency, "⚪")
        print(f"   {icon} [{urgency.upper():8s}] {msg['subject']}")
        print(f"      From: {msg['from']}  |  Ticket: {ticket_id}")
        if matched_kws:
            print(f"      Keywords matched: {', '.join(matched_kws)}")
        print(f"      Est. response: {est_response_time} min")
        print(f"      Draft: {response_text.splitlines()[0]}...")

        if needs_review:
            review_item = {
                "ticket_id": ticket_id,
                "message_id": msg["id"],
                "from": msg["from"],
                "subject": msg["subject"],
                "urgency": urgency,
                "matched_keywords": matched_kws,
                "drafted_response": response_text,
                "queued_at": datetime.utcnow().isoformat(),
            }
            review_queue_items.append(review_item)
            print(f"      📋 Queued for human review")

        results.append({
            "ticket_id": ticket_id,
            "message_id": msg["id"],
            "urgency": urgency,
            "match_count": match_count,
            "matched_keywords": matched_kws,
            "needs_human_review": needs_review,
            "est_response_minutes": est_response_time,
        })
        print()

    # Write human review queue
    for item in review_queue_items:
        queue_for_review(review_queue_path, item, dry_run)

    # Summary
    avg_response = sum(response_times) / len(response_times) if response_times else 0
    print(f"   Summary: {len(messages)} messages processed")
    for tier in URGENCY_TIERS:
        if tier_counts[tier] > 0:
            print(f"   {tier.capitalize():10s}: {tier_counts[tier]}")
    print(f"   Human review queue: {len(review_queue_items)} items")
    print(f"   Avg response time: {avg_response:.0f} min")

    log_activity(
        "support_triage_run",
        f"{len(messages)} messages triaged",
        "completed",
        f"Critical: {tier_counts['critical']}, High: {tier_counts['high']}, "
        f"Review queue: {len(review_queue_items)}, "
        f"Mode: {'dry_run' if dry_run else 'live'}",
    )

    return {
        "messages_processed": len(messages),
        "tier_breakdown": tier_counts,
        "human_review_count": len(review_queue_items),
        "avg_response_minutes": round(avg_response, 1),
        "results": results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="customer_support_triage",
        description="Customer Support Triage — Classify urgency, draft responses, queue for review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python src/agentkit/templates/customer_support_triage/agent.py --dry-run
  python src/agentkit/templates/customer_support_triage/agent.py --config my_config.yaml
  python src/agentkit/templates/customer_support_triage/agent.py --dry-run --json
""",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing to review queue (default mode)",
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
    ensure_tables()

    dry_run = True  # Safe default
    if args.dry_run:
        dry_run = True

    result = run_triage(config, dry_run)

    if args.output_json:
        print(json.dumps(result, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()

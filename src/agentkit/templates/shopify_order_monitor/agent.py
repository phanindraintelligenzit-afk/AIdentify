"""Shopify Order Monitor — Template for AgentsFactory.

Monitors Shopify orders, flags anomalies, sends daily summary.

Usage:
    python src/agentkit/templates/shopify_order_monitor/agent.py --dry-run
    python src/agentkit/templates/shopify_order_monitor/agent.py --config my_config.yaml
    python src/agentkit/templates/shopify_order_monitor/agent.py --dry-run --json

All activity is logged to agent_activity table in agentsfactory_metrics.db.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yaml  # type: ignore

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "agentsfactory_metrics.db"
AGENT_NAME = "shopify_order_monitor"

# ---------------------------------------------------------------------------
# Simulated order data (replace with Shopify API in production)
# ---------------------------------------------------------------------------
SIMULATED_ORDERS = [
    {
        "id": "ord_001",
        "customer_name": "Alice Johnson",
        "customer_email": "alice@example.com",
        "total_value": 89.99,
        "currency": "USD",
        "line_items": [{"product": "Widget Pro", "quantity": 2, "price": 44.99}],
        "shipping_country": "US",
        "shipping_city": "New York",
        "status": "paid",
        "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
    },
    {
        "id": "ord_002",
        "customer_name": "Bob Smith",
        "customer_email": "bob@example.com",
        "total_value": 8500.00,
        "currency": "USD",
        "line_items": [{"product": "Enterprise Bundle", "quantity": 1, "price": 8500.00}],
        "shipping_country": "US",
        "shipping_city": "San Francisco",
        "status": "paid",
        "created_at": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
    },
    {
        "id": "ord_003",
        "customer_name": "Chukwuemeka Obi",
        "customer_email": "chukwu@example.ng",
        "total_value": 299.00,
        "currency": "USD",
        "line_items": [{"product": "Widget Pro", "quantity": 25, "price": 11.96}],
        "shipping_country": "NG",
        "shipping_city": "Lagos",
        "status": "paid",
        "created_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
    },
    {
        "id": "ord_004",
        "customer_name": "Test User",
        "customer_email": "test@test.com",
        "total_value": 0.01,
        "currency": "USD",
        "line_items": [{"product": "Test Product", "quantity": 1, "price": 0.01}],
        "shipping_country": "US",
        "shipping_city": "Test City",
        "status": "paid",
        "created_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
    },
    {
        "id": "ord_005",
        "customer_name": "Diana Chen",
        "customer_email": "diana@example.com",
        "total_value": 159.98,
        "currency": "USD",
        "line_items": [
            {"product": "Widget Pro", "quantity": 1, "price": 89.99},
            {"product": "Gadget Mini", "quantity": 1, "price": 69.99},
        ],
        "shipping_country": "CA",
        "shipping_city": "Toronto",
        "status": "paid",
        "created_at": (datetime.utcnow() - timedelta(hours=8)).isoformat(),
    },
]


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
# Anomaly detection
# ---------------------------------------------------------------------------

def check_anomalies(order: dict, config: dict) -> list[str]:
    """Check an order against thresholds and return list of anomaly flags."""
    flags: list[str] = []
    thresholds = config.get("anomaly_thresholds", {})

    high_value = thresholds.get("high_value_order", 5000)
    bulk_qty = thresholds.get("bulk_quantity", 10)
    risk_countries = thresholds.get("risk_countries", ["NG", "PK", "BD", "VN"])

    total_value = order.get("total_value", 0)

    if total_value > high_value:
        flags.append(f"HIGH_VALUE: ${total_value:.2f} > ${high_value:.2f} threshold")

    if total_value < 0.5:
        flags.append(f"SUSPICIOUS_LOW: ${total_value:.2f} < $0.50 threshold")

    for item in order.get("line_items", []):
        qty = item.get("quantity", 0)
        if qty >= bulk_qty:
            flags.append(f"BULK_ORDER: {item.get('product', 'unknown')} qty={qty} >= {bulk_qty}")

    country = order.get("shipping_country", "")
    if country in risk_countries:
        flags.append(f"RISK_COUNTRY: {country}")

    return flags


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_summary(orders: list[dict], anomalies: dict[str, list[str]], dry_run: bool) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# 📦 Shopify Order Monitor — Daily Summary",
        f"**Generated:** {now}",
        f"**Mode:** {'DRY RUN' if dry_run else 'LIVE'}",
        "",
        "## Overview",
        f"- Total orders checked: **{len(orders)}**",
        f"- Orders with anomalies: **{len(anomalies)}**",
        f"- Clean orders: **{len(orders) - len(anomalies)}**",
        "",
        "---",
        "",
    ]

    if anomalies:
        lines.append("## 🚨 Flagged Orders")
        lines.append("")
        for oid, flags in anomalies.items():
            order = next((o for o in orders if o["id"] == oid), {})
            lines.append(f"### Order `{oid}` — {order.get('customer_name', 'Unknown')}")
            lines.append(f"- **Value:** ${order.get('total_value', 0):.2f}")
            lines.append(f"- **Country:** {order.get('shipping_country', 'N/A')}")
            lines.append(f"- **Flags:**")
            for f in flags:
                lines.append(f"  - ⚠️  {f}")
            lines.append("")
    else:
        lines.append("## ✅ No Anomalies Detected")
        lines.append("")

    lines += [
        "---",
        "",
        "## Order Details",
        "",
    ]
    for o in orders:
        flag_str = " 🚨" if o["id"] in anomalies else ""
        lines.append(
            f"- `{o['id']}` — {o['customer_name']} — "
            f"${o['total_value']:.2f} — {o['shipping_country']}{flag_str}"
        )

    total_revenue = sum(o["total_value"] for o in orders if o["id"] not in anomalies)
    flagged_revenue = sum(
        o["total_value"] for o in orders if o["id"] in anomalies
    )
    lines += [
        "",
        "---",
        "",
        "## Revenue Summary",
        f"- Clean orders revenue: **${total_revenue:.2f}**",
        f"- Flagged orders value: **${flagged_revenue:.2f}**",
        f"- Total processed: **${total_revenue + flagged_revenue:.2f}**",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Notification stubs
# ---------------------------------------------------------------------------

def send_slack_notification(webhook_url: str, message: str) -> dict:
    """Send notification to Slack via webhook. Stub for production."""
    if not webhook_url:
        return {"status": "skipped", "reason": "no webhook configured"}
    # In production: requests.post(webhook_url, json={"text": message})
    return {"status": "simulated", "message": "Slack notification sent"}


def send_email_notification(recipients: list[str], subject: str, body: str) -> dict:
    """Send email notification. Stub for production."""
    if not recipients:
        return {"status": "skipped", "reason": "no recipients configured"}
    # In production: smtplib or SendGrid API
    return {"status": "simulated", "message": f"Email sent to {', '.join(recipients)}"}


# ---------------------------------------------------------------------------
# Main monitor logic
# ---------------------------------------------------------------------------

def run_monitor(config: dict, dry_run: bool) -> dict:
    """Run the order monitoring pass."""
    print(f"\n📦 Shopify Order Monitor")
    print(f"   Store: {config.get('shopify_store_url', 'not configured')}")
    print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"   Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    orders = SIMULATED_ORDERS
    anomalies: dict[str, list[str]] = {}

    for order in orders:
        flags = check_anomalies(order, config)
        if flags:
            anomalies[order["id"]] = flags
            for f in flags:
                print(f"   🚨 {order['id']}: {f}")
        else:
            print(f"   ✅ {order['id']}: Clean — {order['customer_name']} (${order['total_value']:.2f})")

    print(f"\n   Summary: {len(orders)} orders, {len(anomalies)} flagged")

    # Generate report
    report = generate_summary(orders, anomalies, dry_run)

    # Save report
    report_path = PROJECT_ROOT / "data" / "shopify_daily_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"   📄 Report saved: {report_path}")

    # Send notifications (simulated)
    slack_webhook = config.get("slack_webhook", "")
    if anomalies:
        slack_result = send_slack_notification(
            slack_webhook,
            f"🚨 Shopify Monitor: {len(anomalies)} anomalous orders detected",
        )
        print(f"   📨 Slack: {slack_result['status']}")

    email_result = send_email_notification(
        config.get("email_recipients", []),
        "Shopify Order Monitor — Daily Summary",
        report,
    )
    print(f"   📨 Email: {email_result['status']}")

    # Log to database
    log_activity(
        "order_monitor_run",
        f"{len(orders)} orders checked",
        "completed",
        f"Flagged: {len(anomalies)}, Mode: {'dry_run' if dry_run else 'live'}",
    )

    return {
        "orders_checked": len(orders),
        "anomalies_found": len(anomalies),
        "details": anomalies,
        "report": report,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shopify_order_monitor",
        description="Shopify Order Monitor — Detect anomalous orders and send daily summaries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python src/agentkit/templates/shopify_order_monitor/agent.py --dry-run
  python src/agentkit/templates/shopify_order_monitor/agent.py --config my_config.yaml
  python src/agentkit/templates/shopify_order_monitor/agent.py --dry-run --json
""",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without sending notifications (default mode)",
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

    dry_run = True  # Safe default — always dry-run unless explicitly overridden
    if not args.dry_run and "--live" in sys.argv:
        dry_run = False

    result = run_monitor(config, dry_run)

    if args.output_json:
        print(json.dumps(result, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()

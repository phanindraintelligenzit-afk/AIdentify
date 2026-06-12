"""Weekly Business Report — Template for AgentsFactory.

Pulls simulated data from multiple business sources, generates a formatted
markdown report, saves to a dated file, and logs all activity.

Usage:
    python src/agentkit/templates/weekly_business_report/agent.py --dry-run
    python src/agentkit/templates/weekly_business_report/agent.py --config my_config.yaml
    python src/agentkit/templates/weekly_business_report/agent.py --dry-run --json

All activity is logged to agent_activity table in agentsfactory_metrics.db.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import yaml  # type: ignore

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "agentsfactory_metrics.db"
AGENT_NAME = "weekly_business_report"

# ---------------------------------------------------------------------------
# Simulated data sources (replace with real API/DB queries in production)
# ---------------------------------------------------------------------------

def get_orders_data() -> dict:
    """Simulated orders data."""
    return {
        "total_orders": 342,
        "total_orders_prev_week": 298,
        "avg_order_value": 67.50,
        "avg_order_value_prev_week": 62.30,
        "status_breakdown": {
            "completed": 289,
            "processing": 31,
            "refunded": 12,
            "cancelled": 10,
        },
        "top_products": [
            {"name": "Widget Pro", "units": 156, "revenue": 8940.00},
            {"name": "Gadget Mini", "units": 98, "revenue": 4410.00},
            {"name": "Starter Bundle", "units": 67, "revenue": 3350.00},
            {"name": "Pro License", "units": 45, "revenue": 4500.00},
            {"name": "Support Add-on", "units": 38, "revenue": 1900.00},
        ],
    }


def get_revenue_data() -> dict:
    """Simulated revenue data."""
    return {
        "weekly_revenue": 23085.00,
        "prev_week_revenue": 18565.40,
        "daily_revenue": {
            "Mon": 3120.00,
            "Tue": 3450.00,
            "Wed": 2980.00,
            "Thu": 3890.00,
            "Fri": 4210.00,
            "Sat": 2890.00,
            "Sun": 2545.00,
        },
        "top_revenue_day": ("Fri", 4210.00),
    }


def get_customers_data() -> dict:
    """Simulated customer data."""
    return {
        "total_customers": 1247,
        "new_customers": 89,
        "returning_customers": 253,
        "top_customers": [
            {"name": "Alice Johnson", "orders": 12, "total_spent": 2340.00},
            {"name": "Bob Smith", "orders": 8, "total_spent": 1890.00},
            {"name": "Priya Patel", "orders": 7, "total_spent": 1560.00},
            {"name": "David Kim", "orders": 6, "total_spent": 1230.00},
        ],
        "geo_distribution": {
            "US": 58,
            "CA": 14,
            "UK": 11,
            "DE": 7,
            "IN": 5,
            "Other": 5,
        },
    }


def get_content_data() -> dict:
    """Simulated content performance data."""
    return {
        "total_page_views": 12450,
        "prev_week_page_views": 10230,
        "engagement_rate": 0.042,
        "prev_engagement_rate": 0.038,
        "top_content": [
            {"title": "Getting Started Guide", "views": 3200, "avg_time": "4:32"},
            {"title": "API Documentation", "views": 2890, "avg_time": "6:15"},
            {"title": "Pricing Comparison", "views": 2100, "avg_time": "3:45"},
            {"title": "Case Study: TechScale", "views": 1870, "avg_time": "5:10"},
            {"title": "Release Notes v2.5", "views": 1450, "avg_time": "2:55"},
        ],
    }


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
# Report generation
# ---------------------------------------------------------------------------

def pct_change(current: float, previous: float) -> str:
    if previous == 0:
        return "N/A"
    change = ((current - previous) / previous) * 100
    sign = "+" if change >= 0 else ""
    emoji = "📈" if change >= 0 else "📉"
    return f"{emoji} {sign}{change:.1f}%"


def generate_report(data_sources: dict, dry_run: bool) -> str:
    """Generate the full markdown report."""
    now = datetime.utcnow()
    week_start = (now - timedelta(days=now.weekday())).strftime("%B %d")
    week_end = (now - timedelta(days=now.weekday()) + timedelta(days=6)).strftime("%B %d, %Y")

    lines = [
        f"# 📊 Weekly Business Report",
        f"**Week:** {week_start} – {week_end}",
        f"**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Mode:** {'DRY RUN' if dry_run else 'LIVE'}",
        "",
        "---",
        "",
    ]

    # Orders Summary
    if data_sources.get("orders"):
        orders = get_orders_data()
        lines += [
            "## 📦 Orders Summary",
            "",
            f"| Metric | This Week | Last Week | Change |",
            f"|--------|-----------|-----------|--------|",
            f"| Total Orders | **{orders['total_orders']}** | {orders['total_orders_prev_week']} | {pct_change(orders['total_orders'], orders['total_orders_prev_week'])} |",
            f"| Avg Order Value | **${orders['avg_order_value']:.2f}** | ${orders['avg_order_value_prev_week']:.2f} | {pct_change(orders['avg_order_value'], orders['avg_order_value_prev_week'])} |",
            "",
            "### Order Status Breakdown",
            "",
        ]
        for status, count in orders["status_breakdown"].items():
            pct = (count / orders["total_orders"]) * 100
            lines.append(f"- **{status.capitalize()}**: {count} ({pct:.1f}%)")

        lines += [
            "",
            "### Top Products",
            "",
            "| Product | Units Sold | Revenue |",
            "|---------|-----------|---------|",
        ]
        for p in orders["top_products"]:
            lines.append(f"| {p['name']} | {p['units']} | ${p['revenue']:,.2f} |")
        lines.append("")

    # Revenue
    if data_sources.get("revenue"):
        rev = get_revenue_data()
        lines += [
            "---",
            "",
            "## 💰 Revenue",
            "",
            f"- **Weekly Revenue:** **${rev['weekly_revenue']:,.2f}**",
            f"- **Previous Week:** ${rev['prev_week_revenue']:,.2f} ({pct_change(rev['weekly_revenue'], rev['prev_week_revenue'])})",
            f"- **Top Day:** {rev['top_revenue_day'][0]} (${rev['top_revenue_day'][1]:,.2f})",
            "",
            "### Daily Breakdown",
            "",
            "| Day | Revenue |",
            "|-----|---------|",
        ]
        for day, amount in rev["daily_revenue"].items():
            bar = "█" * int(amount / 500)
            lines.append(f"| {day} | ${amount:>8,.2f} {bar} |")
        lines.append("")

    # Customer Insights
    if data_sources.get("customers"):
        cust = get_customers_data()
        lines += [
            "---",
            "",
            "## 👥 Customer Insights",
            "",
            f"- **Total Customers:** {cust['total_customers']:,}",
            f"- **New This Week:** {cust['new_customers']}",
            f"- **Returning This Week:** {cust['returning_customers']}",
            "",
            "### Top Customers",
            "",
            "| Customer | Orders | Total Spent |",
            "|----------|--------|-------------|",
        ]
        for c in cust["top_customers"]:
            lines.append(f"| {c['name']} | {c['orders']} | ${c['total_spent']:,.2f} |")

        lines += [
            "",
            "### Geographic Distribution",
            "",
            "| Region | Share |",
            "|--------|-------|",
        ]
        for region, share in cust["geo_distribution"].items():
            bar = "▓" * int(share / 2)
            lines.append(f"| {region} | {share}% {bar} |")
        lines.append("")

    # Content Performance
    if data_sources.get("content"):
        content = get_content_data()
        lines += [
            "---",
            "",
            "## 📝 Content Performance",
            "",
            f"- **Total Page Views:** {content['total_page_views']:,} ({pct_change(content['total_page_views'], content['prev_week_page_views'])})",
            f"- **Engagement Rate:** {content['engagement_rate']:.1%} ({pct_change(content['engagement_rate'], content['prev_engagement_rate'])})",
            "",
            "### Top Content",
            "",
            "| Title | Views | Avg Time |",
            "|-------|-------|----------|",
        ]
        for c in content["top_content"]:
            lines.append(f"| {c['title']} | {c['views']:,} | {c['avg_time']} |")
        lines.append("")

    lines += [
        "---",
        "",
        f"*Report generated by AgentsFactory — {AGENT_NAME}*",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main report logic
# ---------------------------------------------------------------------------

def run_report(config: dict, dry_run: bool) -> dict:
    """Generate the weekly business report."""
    print(f"\n📊 Weekly Business Report")
    print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"   Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    data_sources = config.get("data_sources", {"orders": True, "revenue": True, "customers": True, "content": True})
    output_dir = PROJECT_ROOT / config.get("report_output_dir", "data/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    active_sources = [k for k, v in data_sources.items() if v]
    print(f"   Active data sources: {', '.join(active_sources)}")

    report = generate_report(data_sources, dry_run)

    # Save report
    now = datetime.utcnow()
    report_filename = f"weekly_report_{now.strftime('%Y%m%d')}.md"
    report_path = output_dir / report_filename

    if not dry_run:
        report_path.write_text(report, encoding="utf-8")
        print(f"   📄 Report saved: {report_path}")
    else:
        print(f"   📄 Report preview (dry run, not saved):")
        print(f"      Would save to: {report_path}")

    # Print a preview
    preview_lines = report.split("\n")[:20]
    for line in preview_lines:
        print(f"   {line}")
    print(f"   ... ({len(report.splitlines())} total lines)")

    log_activity(
        "weekly_report_generated",
        str(report_path),
        "completed",
        f"Sources: {', '.join(active_sources)}, "
        f"Lines: {len(report.splitlines())}, "
        f"Mode: {'dry_run' if dry_run else 'live'}",
    )

    return {
        "report_path": str(report_path),
        "data_sources": active_sources,
        "lines": len(report.splitlines()),
        "report": report,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="weekly_business_report",
        description="Weekly Business Report — Generate formatted markdown reports from business data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python src/agentkit/templates/weekly_business_report/agent.py --dry-run
  python src/agentkit/templates/weekly_business_report/agent.py --config my_config.yaml
  python src/agentkit/templates/weekly_business_report/agent.py --dry-run --json
""",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate report without saving to disk (default mode)",
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

    result = run_report(config, dry_run)

    if args.output_json:
        print(json.dumps(result, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()

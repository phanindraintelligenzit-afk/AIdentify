"""
CLI entry point for the Audit Report Generator.

Usage:
    python -m compliance report --type daily
    python -m compliance report --type daily --date 2026-06-21 --format html
    python -m compliance report --type weekly --week-start 2026-06-16
    python -m compliance report --type incident --incident-id INC-001 --rule-id RULE-001
    python -m compliance report --type daily --output report.md

Can be cron-triggered:
    # Daily at 06:00 UTC
    0 6 * * * cd /path/to/project && python -m compliance report --type daily

    # Weekly on Monday at 07:00 UTC
    0 7 * * 1 cd /path/to/project && python -m compliance report --type weekly
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone

from compliance.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


def _default_db_path() -> str:
    """Resolve the default audit database path."""
    # Check common locations
    candidates = [
        Path(__file__).parent.parent.parent / "audit_events.db",
        Path(__file__).parent.parent / "audit_events.db",
        Path.cwd() / "audit_events.db",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    # Fallback: project root
    return str(Path(__file__).parent.parent.parent / "audit_events.db")


def cmd_daily(args: argparse.Namespace) -> str:
    gen = ReportGenerator(db_path=args.db_path)
    return gen.generate_daily(
        date=args.date,
        output_format=args.format,
    )


def cmd_weekly(args: argparse.Namespace) -> str:
    gen = ReportGenerator(db_path=args.db_path)
    return gen.generate_weekly(
        week_start=args.week_start,
        output_format=args.format,
    )


def cmd_incident(args: argparse.Namespace) -> str:
    gen = ReportGenerator(db_path=args.db_path)
    return gen.generate_incident(
        incident_id=args.incident_id,
        rule_id=args.rule_id,
        start_date=args.start_date,
        end_date=args.end_date,
        severity=args.severity,
        output_format=args.format,
    )


def main():
    parser = argparse.ArgumentParser(
        prog="compliance report",
        description="Generate compliance reports from audit events.",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=_default_db_path(),
        help="Path to the SQLite audit database (default: auto-detect).",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "html"],
        default="markdown",
        help="Output format: markdown (email/Slack) or html (dashboard). Default: markdown.",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file path. If not specified, prints to stdout.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging.",
    )

    subparsers = parser.add_subparsers(dest="report_type", help="Report type.")

    # Daily
    daily_parser = subparsers.add_parser("daily", help="Daily compliance summary.")
    daily_parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Report date (YYYY-MM-DD). Default: today.",
    )

    # Weekly
    weekly_parser = subparsers.add_parser("weekly", help="Weekly compliance digest.")
    weekly_parser.add_argument(
        "--week-start",
        type=str,
        default=None,
        help="Week start date (YYYY-MM-DD, Monday). Default: current week.",
    )

    # Incident
    incident_parser = subparsers.add_parser("incident", help="Incident report.")
    incident_parser.add_argument(
        "--incident-id",
        type=str,
        required=True,
        help="Unique incident identifier (e.g., INC-001).",
    )
    incident_parser.add_argument(
        "--rule-id",
        type=str,
        default=None,
        help="Rule ID that triggered the incident (e.g., RULE-001).",
    )
    incident_parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Start date for event lookup (YYYY-MM-DD). Default: 7 days ago.",
    )
    incident_parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="End date for event lookup (YYYY-MM-DD). Default: today.",
    )
    incident_parser.add_argument(
        "--severity",
        type=str,
        default="high",
        choices=["info", "low", "medium", "high", "critical"],
        help="Incident severity. Default: high.",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if not args.report_type:
        parser.print_help()
        sys.exit(1)

    # Dispatch
    dispatch = {
        "daily": cmd_daily,
        "weekly": cmd_weekly,
        "incident": cmd_incident,
    }

    handler = dispatch.get(args.report_type)
    if not handler:
        parser.print_help()
        sys.exit(1)

    try:
        report = handler(args)
    except FileNotFoundError as e:
        logger.error(f"Database not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        sys.exit(1)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        logger.info(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()

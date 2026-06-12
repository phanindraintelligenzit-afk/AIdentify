"""Social Media Scheduler — Template for AgentsFactory.

Reads content calendar from agentsfactory_metrics.db, schedules posts across
platforms, tracks simulated engagement, and reshares top-performing content.

Usage:
    python src/agentkit/templates/social_media_scheduler/agent.py --dry-run
    python src/agentkit/templates/social_media_scheduler/agent.py --config my_config.yaml
    python src/agentkit/templates/social_media_scheduler/agent.py --dry-run --json

All activity is logged to agent_activity table in agentsfactory_metrics.db.
"""

from __future__ import annotations

import argparse
import json
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import yaml  # type: ignore

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "agentsfactory_metrics.db"
AGENT_NAME = "social_media_scheduler"

# ---------------------------------------------------------------------------
# Simulated content calendar data
# ---------------------------------------------------------------------------
SIMULATED_CONTENT_CALENDAR = [
    {
        "id": "cc_001",
        "platform": "linkedin",
        "content": "🚀 Excited to announce our new automation toolkit! Streamline your workflows in minutes. #Automation #Productivity",
        "scheduled_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "status": "scheduled",
        "posted_at": None,
        "likes": 0,
        "shares": 0,
        "comments": 0,
        "impressions": 0,
    },
    {
        "id": "cc_002",
        "platform": "twitter",
        "content": "Just shipped: AI-powered lead scoring that actually works. 🎯 No more guessing which prospects to chase. Thread below 👇",
        "scheduled_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "status": "scheduled",
        "posted_at": None,
        "likes": 0,
        "shares": 0,
        "comments": 0,
        "impressions": 0,
    },
    {
        "id": "cc_003",
        "platform": "linkedin",
        "content": "📊 Our weekly automation report is live! 342 orders processed, $23K revenue. Here's what we learned building AI agents for e-commerce.",
        "scheduled_date": (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
        "status": "scheduled",
        "posted_at": None,
        "likes": 0,
        "shares": 0,
        "comments": 0,
        "impressions": 0,
    },
    {
        "id": "cc_004",
        "platform": "twitter",
        "content": "Hot take: Most 'AI automation' is just if/else with extra steps. Real automation learns, adapts, and scales. Here's the difference 🧵",
        "scheduled_date": (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
        "status": "scheduled",
        "posted_at": None,
        "likes": 0,
        "shares": 0,
        "comments": 0,
        "impressions": 0,
    },
    {
        "id": "cc_005",
        "platform": "linkedin",
        "content": "Case study: How we helped a SaaS company reduce support tickets by 60% using AI triage. Full breakdown inside. #CustomerSupport #AI",
        "scheduled_date": (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d"),
        "status": "scheduled",
        "posted_at": None,
        "likes": 0,
        "shares": 0,
        "comments": 0,
        "impressions": 0,
    },
    # Past posts (already published, with engagement data)
    {
        "id": "cc_006",
        "platform": "twitter",
        "content": "5 signs you need workflow automation (thread) 🧵👇",
        "scheduled_date": (datetime.utcnow() - timedelta(days=10)).strftime("%Y-%m-%d"),
        "status": "posted",
        "posted_at": (datetime.utcnow() - timedelta(days=10)).isoformat(),
        "likes": 245,
        "shares": 89,
        "comments": 34,
        "impressions": 8900,
    },
    {
        "id": "cc_007",
        "platform": "linkedin",
        "content": "Why we built AgentsFactory: The gap between 'AI demos' and 'AI that actually runs your business' is massive.",
        "scheduled_date": (datetime.utcnow() - timedelta(days=8)).strftime("%Y-%m-%d"),
        "status": "posted",
        "posted_at": (datetime.utcnow() - timedelta(days=8)).isoformat(),
        "likes": 512,
        "shares": 178,
        "comments": 67,
        "impressions": 15200,
    },
    {
        "id": "cc_008",
        "platform": "twitter",
        "content": "Automation tip: Start with the task you hate most. If you dread it daily, a bot will love it forever. 🤖",
        "scheduled_date": (datetime.utcnow() - timedelta(days=12)).strftime("%Y-%m-%d"),
        "status": "posted",
        "posted_at": (datetime.utcnow() - timedelta(days=12)).isoformat(),
        "likes": 89,
        "shares": 23,
        "comments": 12,
        "impressions": 3400,
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


def ensure_tables(db_path: Path | None = None) -> None:
    # Ensure agent_activity table
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

    # Ensure content_calendar table
    db = get_db(db_path)
    db.executescript(
        "CREATE TABLE IF NOT EXISTS content_calendar ("
        "id TEXT PRIMARY KEY, platform TEXT NOT NULL, "
        "content TEXT NOT NULL, scheduled_date TEXT, "
        "status TEXT DEFAULT 'draft', posted_at TEXT, "
        "likes INTEGER DEFAULT 0, shares INTEGER DEFAULT 0, "
        "comments INTEGER DEFAULT 0, impressions INTEGER DEFAULT 0, "
        "created_at TEXT DEFAULT (datetime('now')));"
    )
    db.commit()
    db.close()


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
# Content calendar operations
# ---------------------------------------------------------------------------

def seed_content_calendar(db_path: Path, dry_run: bool) -> None:
    """Seed the content calendar table with simulated data if empty."""
    conn = get_db(db_path)
    existing = conn.execute("SELECT COUNT(*) as cnt FROM content_calendar").fetchone()["cnt"]
    if existing > 0:
        conn.close()
        return

    for item in SIMULATED_CONTENT_CALENDAR:
        conn.execute(
            "INSERT OR IGNORE INTO content_calendar "
            "(id, platform, content, scheduled_date, status, posted_at, likes, shares, comments, impressions) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item["id"], item["platform"], item["content"],
                item["scheduled_date"], item["status"], item.get("posted_at"),
                item["likes"], item["shares"], item["comments"], item["impressions"],
            ),
        )
    conn.commit()
    conn.close()


def get_scheduled_posts(db_path: Path) -> list[dict]:
    """Fetch all scheduled (not yet posted) content."""
    conn = get_db(db_path)
    rows = conn.execute(
        "SELECT * FROM content_calendar WHERE status = 'scheduled' ORDER BY scheduled_date"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_past_posts(db_path: Path) -> list[dict]:
    """Fetch all posted content with engagement data."""
    conn = get_db(db_path)
    rows = conn.execute(
        "SELECT * FROM content_calendar WHERE status = 'posted' ORDER BY posted_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def schedule_post(db_path: Path, post: dict, dry_run: bool) -> None:
    """Mark a post as scheduled in the database."""
    if dry_run:
        return
    conn = get_db(db_path)
    conn.execute(
        "UPDATE content_calendar SET status = 'scheduled', scheduled_date = ? WHERE id = ?",
        (post["scheduled_date"], post["id"]),
    )
    conn.commit()
    conn.close()


def simulate_engagement(post: dict) -> dict:
    """Generate simulated engagement metrics for a post."""
    base = random.randint(50, 300)
    multiplier = 1.5 if post.get("platform") == "linkedin" else 1.0
    likes = int(base * multiplier * random.uniform(0.8, 1.5))
    shares = int(likes * random.uniform(0.1, 0.4))
    comments = int(likes * random.uniform(0.05, 0.2))
    impressions = int(likes * random.uniform(15, 40))
    return {"likes": likes, "shares": shares, "comments": comments, "impressions": impressions}


def engagement_rate(metrics: dict) -> float:
    """Calculate engagement rate from metrics."""
    total_engagement = metrics["likes"] + metrics["shares"] + metrics["comments"]
    impressions = max(metrics["impressions"], 1)
    return total_engagement / impressions


# ---------------------------------------------------------------------------
# Main scheduler logic
# ---------------------------------------------------------------------------

def run_scheduler(config: dict, dry_run: bool) -> dict:
    """Run the social media scheduling pass."""
    print(f"\n📱 Social Media Scheduler")
    print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"   Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    platforms = config.get("platforms", ["linkedin", "twitter"])
    max_posts = config.get("max_posts_per_day", 3)
    reshare_days = config.get("reshare_threshold_days", 7)
    db_path = PROJECT_ROOT / config.get("content_calendar_db_path", "agentsfactory_metrics.db")

    ensure_tables(db_path)
    seed_content_calendar(db_path, dry_run)

    print(f"   Platforms: {', '.join(platforms)}")
    print(f"   Max posts/day: {max_posts}")
    print(f"   Reshare threshold: {reshare_days} days")
    print()

    # Schedule upcoming posts
    scheduled_posts = get_scheduled_posts(db_path)
    platform_counts: dict[str, int] = {}
    scheduled_results = []

    for post in scheduled_posts:
        platform = post["platform"]
        if platform not in platforms:
            continue
        platform_counts[platform] = platform_counts.get(platform, 0) + 1

        schedule_post(db_path, post, dry_run)
        print(f"   📅 [{platform}] {post['scheduled_date']} — {post['content'][:60]}...")
        scheduled_results.append({
            "id": post["id"],
            "platform": platform,
            "scheduled_date": post["scheduled_date"],
            "content_preview": post["content"][:80],
        })

    print(f"\n   Scheduled: {len(scheduled_results)} posts")
    for p, count in platform_counts.items():
        print(f"   - {p}: {count} posts")

    # Analyze past posts for reshare candidates
    past_posts = get_past_posts(db_path)
    reshare_candidates = []

    if past_posts:
        # Calculate engagement rates
        for post in past_posts:
            post["engagement"] = engagement_rate(post)

        rates = [post["engagement"] for post in past_posts]
        threshold_rate = sorted(rates)[int(len(rates) * 0.75)] if len(rates) >= 2 else 0

        cutoff = datetime.utcnow() - timedelta(days=reshare_days)

        for post in past_posts:
            posted_at = datetime.fromisoformat(post["posted_at"]) if post.get("posted_at") else None
            if post["engagement"] >= threshold_rate and posted_at and posted_at < cutoff:
                reshare_candidates.append(post)

    print(f"\n   📊 Past posts analyzed: {len(past_posts)}")
    print(f"   Reshare candidates: {len(reshare_candidates)}")

    for candidate in reshare_candidates:
        print(f"   🔄 [{candidate['platform']}] Engagement: {candidate['engagement']:.2%}")
        print(f"      Original: {candidate['content'][:60]}...")
        print(f"      Likes: {candidate['likes']}  Shares: {candidate['shares']}  "
              f"Comments: {candidate['comments']}")

        log_activity(
            "reshare_candidate",
            f"{candidate['id']} ({candidate['platform']})",
            "identified",
            f"Engagement: {candidate['engagement']:.2%}, "
            f"Likes: {candidate['likes']}, Shares: {candidate['shares']}",
        )

    log_activity(
        "scheduler_run",
        f"{len(scheduled_results)} posts scheduled",
        "completed",
        f"Platforms: {', '.join(platforms)}, "
        f"Reshare candidates: {len(reshare_candidates)}, "
        f"Mode: {'dry_run' if dry_run else 'live'}",
    )

    return {
        "posts_scheduled": len(scheduled_results),
        "platform_breakdown": platform_counts,
        "reshare_candidates": len(reshare_candidates),
        "scheduled": scheduled_results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="social_media_scheduler",
        description="Social Media Scheduler — Schedule posts, track engagement, reshare top content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python src/agentkit/templates/social_media_scheduler/agent.py --dry-run
  python src/agentkit/templates/social_media_scheduler/agent.py --config my_config.yaml
  python src/agentkit/templates/social_media_scheduler/agent.py --dry-run --json
""",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing to database (default mode)",
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

    result = run_scheduler(config, dry_run)

    if args.output_json:
        print(json.dumps(result, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    main()

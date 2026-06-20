"""Content Calendar — deduplication + queue tracker for AgentsFactory.

Ensures content_calendar table exists, generates a weekly queue with
pillar/platform rotation, deduplicates against recent posts, and
provides CLI access to the calendar.

Usage:
    python scripts/content_calendar.py --action generate --days 7
    python scripts/content_calendar.py --action next
    python scripts/content_calendar.py --action list [--limit 20]
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# --------------------------------------------------------------------------- paths ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src" / "agents"))

import sqlite3

DB_PATH = PROJECT_ROOT / "agentsfactory_metrics.db"

# --------------------------------------------------------------------------- platform / pillar config ----------------------------------------------------------

PILLARS = (
    "case_study",
    "behind_scenes",
    "tips_tutorial",
    "social_proof",
    "industry_insight",
    "personal_story",
)

# Platform rotation: weekdays get linkedin + twitter; instagram and facebook are extra variants
PLATFORM_SCHEDULE = {
    0: ["linkedin", "twitter"],                      # Monday
    1: ["linkedin", "twitter"],                      # Tuesday
    2: ["linkedin", "twitter", "instagram"],         # Wednesday
    3: ["linkedin", "twitter"],                      # Thursday
    4: ["linkedin", "twitter", "facebook"],          # Friday
    5: ["linkedin"],                                 # Saturday
    6: ["twitter"],                                  # Sunday
}

TOPICS_BY_PILLAR = {
    "case_study": "client automation results",
    "behind_scenes": "building AgentsFactory",
    "tips_tutorial": "AI workflow tips",
    "social_proof": "client success stories",
    "industry_insight": "automation industry trends",
    "personal_story": "founder journey",
}


# --------------------------------------------------------------------------- DB helpers -----------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def ensure_tables() -> None:
    """Create content_calendar (and agent_activity) if missing."""
    conn = get_db()
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS content_calendar ("
        "id TEXT PRIMARY KEY, title TEXT NOT NULL, platform TEXT DEFAULT 'linkedin', "
        "status TEXT DEFAULT 'draft', scheduled_at TEXT, published_at TEXT, "
        "engagement_score REAL DEFAULT 0, notes TEXT DEFAULT '', "
        "created_at TEXT DEFAULT (datetime('now')));"
        ""
        "CREATE TABLE IF NOT EXISTS agent_activity ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, agent_name TEXT NOT NULL, "
        "action TEXT NOT NULL, target TEXT DEFAULT '', "
        "status TEXT DEFAULT 'completed', details TEXT DEFAULT '', "
        "created_at TEXT DEFAULT (datetime('now')));"
    )
    conn.commit()
    conn.close()


# --------------------------------------------------------------------------- core functions -------------------------------------------------------------------

def get_recent_posts(days: int = 30) -> list[dict]:
    """Return list of {title, platform} dicts for posts in the last N days."""
    ensure_tables()
    since = (datetime.now() - timedelta(days=days)).isoformat()
    conn = get_db()
    rows = conn.execute(
        "SELECT title, platform FROM content_calendar WHERE created_at >= ? ORDER BY created_at DESC",
        (since,),
    ).fetchall()
    conn.close()
    return [{"title": r["title"], "platform": r["platform"]} for r in rows]


def is_duplicate(title: str, platform: str, days: int = 30) -> bool:
    """Check if similar content (substring match on title) was posted recently on the same platform."""
    recent = get_recent_posts(days=days)
    title_lower = title.lower()
    for post in recent:
        if post["platform"] != platform:
            continue
        # Substring overlap: either direction
        existing_lower = post["title"].lower()
        if title_lower in existing_lower or existing_lower in title_lower:
            return True
    return False


def record_post(title: str, platform: str, status: str = "draft", notes: str = "") -> str:
    """Insert a content piece into content_calendar. Returns the new row id."""
    ensure_tables()
    content_id = f"cc_{uuid.uuid4().hex[:12]}"
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO content_calendar (id, title, platform, status, notes) "
        "VALUES (?, ?, ?, ?, ?)",
        (content_id, title, platform, status, notes),
    )
    conn.commit()
    conn.close()
    return content_id


def generate_weekly_queue(days: int = 7, dry_run: bool = False) -> list[dict]:
    """Generate 2 posts/day × N days, rotating pillars across platforms, with dedup.

    Returns list of generated content-piece dicts.
    """
    ensure_tables()
    sys.path.insert(0, str(PROJECT_ROOT / "src" / "agents"))
    from content_writer import generate_content, derive_title  # type: ignore[import]

    results = []
    pillar_idx = 0
    total_posts = 0
    dupes_skipped = 0

    for day_offset in range(days):
        date = datetime.now() + timedelta(days=day_offset)
        weekday = date.weekday()
        platforms = PLATFORM_SCHEDULE.get(weekday, ["linkedin"])

        # Two posting slots per day: morning & afternoon
        for slot in range(2):
            pillar = PILLARS[(pillar_idx + day_offset + slot) % len(PILLARS)]
            # Pick primary platform for this slot
            platform = platforms[slot % len(platforms)]
            topic = TOPICS_BY_PILLAR.get(pillar, pillar)

            # Use the same title format as content_writer so dedup matches what's saved
            index = day_offset * 2 + slot
            title = derive_title(pillar, platform, topic, index)

            notes_dict = {
                "pillar": pillar,
                "platform": platform,
                "topic": topic,
                "slot": "AM" if slot == 0 else "PM",
                "generated_at": datetime.now().isoformat(),
            }

            if is_duplicate(title, platform, days=30):
                dupes_skipped += 1
                results.append({
                    "title": title,
                    "platform": platform,
                    "pillar": pillar,
                    "status": "skipped_duplicate",
                    "notes": json.dumps(notes_dict),
                })
                continue

            # Generate via content_writer (saves to DB itself)
            if not dry_run:
                try:
                    generated = generate_content(
                        pillar=pillar,
                        platform=platform,
                        topic=topic,
                        count=1,
                        dry_run=False,
                    )
                    if generated:
                        piece = generated[0]
                        piece["slot"] = "AM" if slot == 0 else "PM"
                        results.append(piece)
                        total_posts += 1
                    else:
                        results.append({
                            "title": title,
                            "platform": platform,
                            "pillar": pillar,
                            "status": "empty",
                            "notes": json.dumps(notes_dict),
                        })
                except FileNotFoundError:
                    # Template missing — record a placeholder so we still track it
                    cid = record_post(title, platform, "pending_template", json.dumps(notes_dict))
                    results.append({
                        "id": cid,
                        "title": title,
                        "platform": platform,
                        "pillar": pillar,
                        "status": "pending_template",
                        "notes": json.dumps(notes_dict),
                    })
                    total_posts += 1
            else:
                results.append({
                    "title": title,
                    "platform": platform,
                    "pillar": pillar,
                    "status": "preview",
                    "notes": json.dumps(notes_dict),
                })
                total_posts += 1

    print(f"\n📊 Queue generation summary:")
    print(f"   Days          : {days}")
    print(f"   Platforms/day : 2 (varies by weekday)")
    print(f"   Created       : {total_posts}")
    print(f"   Dedup skipped : {dupes_skipped}")
    print(f"   Total entries : {len(results)}")

    return results


def get_next_post() -> dict | None:
    """Return the next unpublished (draft) post from the calendar, oldest first."""
    ensure_tables()
    conn = get_db()
    row = conn.execute(
        "SELECT id, title, platform, status, scheduled_at, notes, created_at "
        "FROM content_calendar WHERE status = 'draft' ORDER BY created_at ASC LIMIT 1"
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def list_posts(limit: int = 20) -> list[dict]:
    """List the most recent posts in the calendar."""
    ensure_tables()
    conn = get_db()
    rows = conn.execute(
        "SELECT id, title, platform, status, scheduled_at, created_at "
        "FROM content_calendar ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------- CLI -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="content_calendar",
        description="Content Calendar — dedup + queue tracker for AgentsFactory",
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["generate", "next", "list"],
        help="Action to perform",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to generate (default: 7)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Max rows for --action list (default: 20)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without saving (only for --action generate)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output as JSON",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.action == "generate":
        print(f"🗓️  Generating content queue for {args.days} day(s)...")
        print(f"   Pillars  : {', '.join(PILLARS)}")
        print(f"   Dry run  : {args.dry_run}")
        print()
        results = generate_weekly_queue(days=args.days, dry_run=args.dry_run)
        if args.output_json:
            print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
        else:
            saved = sum(1 for r in results if r.get("status") in ("draft", "pending_template"))
            skipped = sum(1 for r in results if r.get("status") == "skipped_duplicate")
            preview = sum(1 for r in results if r.get("status") == "preview")
            print(f"\n✅ Done: {len(results)} entries | {saved} saved | {skipped} dedup-skipped | {preview} preview")

    elif args.action == "next":
        post = get_next_post()
        if post is None:
            print("No unpublished posts in the calendar.")
            return
        if args.output_json:
            print(json.dumps(post, indent=2, ensure_ascii=False, default=str))
        else:
            print(f"📌 Next post:")
            print(f"   ID       : {post['id']}")
            print(f"   Title    : {post['title']}")
            print(f"   Platform : {post['platform']}")
            print(f"   Status   : {post['status']}")
            print(f"   Created  : {post['created_at']}")

    elif args.action == "list":
        posts = list_posts(limit=args.limit)
        if not posts:
            print("Content calendar is empty.")
            return
        if args.output_json:
            print(json.dumps(posts, indent=2, ensure_ascii=False, default=str))
        else:
            print(f"📋 Content calendar (last {len(posts)} entries):")
            print(f"{'ID':<16} {'Platform':<12} {'Status':<10} {'Created':<22} {'Title'}")
            print("-" * 100)
            for p in posts:
                print(f"{p['id']:<16} {p['platform']:<12} {p['status']:<10} {p['created_at']:<22} {p['title']}")


if __name__ == "__main__":
    main()

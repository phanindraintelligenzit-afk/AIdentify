"""
AgentsFactory Weekly Social Analytics Report.
Fetches last 7 days of posts from Ocoya, computes metrics,
compares week-over-week, posts report to Slack.

Usage:
    python scripts/weekly_social_report.py           # generate + post
    python scripts/weekly_social_report.py --dry-run  # print only
    python scripts/weekly_social_report.py --days 14  # custom window
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── project paths ──────────────────────────────────────────────
PROJECT_ROOT = Path("C:/Users/Admin/Projects/AgentsFactory")
OUTPUT_DIR  = PROJECT_ROOT / "output"
sys.path.insert(0, str(PROJECT_ROOT / "src/agents"))

# ── load .env so OCOYA_API_KEY / SLACK_BOT_TOKEN are available ─
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL_ID", "C0BBP317H7G")

# ── Ocoya profile IDs (imported from existing client) ──────────
try:
    from ocoya_client import (
        list_posts,
        LINKEDIN_PROFILE_ID,
        TWITTER_PROFILE_ID,
        INSTAGRAM_PROFILE_ID,
        FACEBOOK_PROFILE_ID,
    )
except ImportError as exc:
    print(f"❌ Cannot import ocoya_client: {exc}")
    sys.exit(1)

PROFILE_NAME_MAP = {
    LINKEDIN_PROFILE_ID:  "LinkedIn",
    TWITTER_PROFILE_ID:   "Twitter",
    INSTAGRAM_PROFILE_ID: "Instagram",
    FACEBOOK_PROFILE_ID:  "Facebook",
}

# ── Slack helper (inline — no dependency on slack_alert.py) ────
def _slack_post(text: str) -> bool:
    token = os.environ.get("SLACK_BOT_TOKEN", "")
    if not token:
        print("  ⚠️  SLACK_BOT_TOKEN not set — skipping Slack post")
        return False
    try:
        body = json.dumps({"channel": SLACK_CHANNEL, "text": text}).encode("utf-8")
        req  = urllib.request.Request(
            "https://slack.com/api/chat.postMessage", data=body, method="POST"
        )
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                return True
            print(f"  ⚠️  Slack API error: {data.get('error', 'unknown')}")
            return False
    except Exception as exc:
        print(f"  ⚠️  Slack post failed: {exc}")
        return False


# ── data collection ────────────────────────────────────────────
def fetch_posts(days: int = 7) -> list:
    """Fetch all POSTED posts from Ocoya, filter to last `days` days."""
    try:
        all_posts = list_posts(status="POSTED", limit=100)
    except Exception as exc:
        print(f"⚠️  Ocoya list_posts failed: {exc}")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = []
    for p in all_posts:
        created_raw = p.get("createdAt", "")
        if not created_raw:
            continue
        try:
            created = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
            if created >= cutoff:
                recent.append(p)
        except (ValueError, TypeError):
            continue
    return recent


def fetch_previous_period_posts(days: int = 7) -> list:
    """Fetch POSTED posts from the previous `days`-day window (for WoW)."""
    try:
        all_posts = list_posts(status="POSTED", limit=100)
    except Exception as exc:
        print(f"⚠️  Ocoya list_posts failed: {exc}")
        return []

    now = datetime.now(timezone.utc)
    prev_start = now - timedelta(days=days * 2)
    prev_end   = now - timedelta(days=days)
    posts = []
    for p in all_posts:
        created_raw = p.get("createdAt", "")
        if not created_raw:
            continue
        try:
            created = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
            if prev_start <= created < prev_end:
                posts.append(p)
        except (ValueError, TypeError):
            continue
    return posts


def _profile_name(profile_id: str) -> str:
    return PROFILE_NAME_MAP.get(profile_id, profile_id[:8])


def _engagement_total(post: dict) -> int:
    """Sum likes + comments + shares from post data (best-effort)."""
    eng = post.get("engagement") or post.get("stats") or {}
    if isinstance(eng, dict):
        return (
            eng.get("likes", 0)
            + eng.get("comments", 0)
            + eng.get("shares", 0)
            + eng.get("impressions", 0) // 100  # weight impressions lower
        )
    return 0


def _post_caption(post: dict) -> str:
    return (
        post.get("caption", "")
        or post.get("text", "")
        or post.get("content", "")
        or "(no text)"
    )[:80]


def analyse(posts: list) -> dict:
    """Return per-platform metrics dict."""
    by_platform: dict[str, list] = {}
    for p in posts:
        for prof in (p.get("socialProfiles") or []):
            pid = prof.get("id", "unknown")
            by_platform.setdefault(pid, []).append(p)

    result = {}
    for pid, plist in by_platform.items():
        name = _profile_name(pid)
        total_eng  = sum(_engagement_total(p) for p in plist)
        engaged    = sum(1 for p in plist if _engagement_total(p) > 0)
        best       = max(plist, key=_engagement_total, default=None)
        result[name] = {
            "posts":        len(plist),
            "total_eng":    total_eng,
            "avg_eng":      round(total_eng / len(plist), 1) if plist else 0,
            "engaged":      engaged,
            "best_post":    _post_caption(best) if best else "N/A",
            "best_eng":     _engagement_total(best) if best else 0,
        }
    return result


# ── formatting ─────────────────────────────────────────────────
def format_report(current: dict, previous: dict, days: int) -> str:
    week_start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%b %d")
    week_end   = datetime.now(timezone.utc).strftime("%b %d, %Y")
    lines = [f"📊 *AgentsFactory Social Report — {week_start} → {week_end}*\n"]

    all_platforms = sorted(set(list(current.keys()) + list(previous.keys())))

    if not all_platforms:
        lines.append("_No posts found in either period._")
        return "\n".join(lines)

    total_posts_cur = sum(v["posts"] for v in current.values())
    total_eng_cur   = sum(v["total_eng"] for v in current.values())
    total_posts_pre = sum(v["posts"] for v in previous.values())
    total_eng_pre   = sum(v["total_eng"] for v in previous.values())

    for platform in all_platforms:
        cur = current.get(platform, {})
        pre = previous.get(platform, {})
        if not cur and not pre:
            continue

        posts_cur = cur.get("posts", 0)
        avg_cur   = cur.get("avg_eng", 0)
        best_post = cur.get("best_post", "N/A")
        best_eng  = cur.get("best_eng", 0)

        posts_pre = pre.get("posts", 0)

        # WoW delta
        if posts_pre > 0:
            delta_pct = round((posts_cur - posts_pre) / posts_pre * 100)
            delta_str = f"{'📈' if delta_pct >= 0 else '📉'} {delta_pct:+d}% vs last week"
        else:
            delta_str = "🆕 first week" if posts_cur > 0 else ""

        lines.append(f"*{platform}* — {posts_cur} posts, avg {avg_cur} eng/post  {delta_str}")
        if best_post != "N/A":
            lines.append(f"  🏆 Best: \"{best_post}\" — {best_eng} eng")
        lines.append("")

    # Overall WoW
    if total_posts_pre > 0:
        total_delta = round((total_posts_cur - total_posts_pre) / total_posts_pre * 100)
        eng_delta   = (
            round((total_eng_cur - total_eng_pre) / total_eng_pre * 100)
            if total_eng_pre > 0
            else 0
        )
        lines.append(
            f"*Overall*: {total_posts_cur} posts ({total_delta:+d}% WoW), "
            f"{total_eng_cur} total eng ({eng_delta:+d}% WoW)"
        )
    else:
        lines.append(f"*Overall*: {total_posts_cur} posts, {total_eng_cur} total eng")

    # Auto-insight
    insight = _generate_insight(current, previous)
    if insight:
        lines.append(f"\n💡 *Insight*: {insight}")

    return "\n".join(lines)


def _generate_insight(current: dict, previous: dict) -> str:
    """Generate a simple insight based on the data."""
    if not current:
        return "No posts this week — check if cron jobs are running."

    # Find best performing platform
    best_platform = max(current.items(), key=lambda x: x[1].get("avg_eng", 0), default=None)
    worst_platform = min(current.items(), key=lambda x: x[1].get("avg_eng", 0), default=None)

    if best_platform and best_platform[1]["posts"] > 0:
        name, data = best_platform
        if data["avg_eng"] > 0:
            return f"{name} had the highest engagement ({data['avg_eng']} avg). Consider posting more there."

    total = sum(v["posts"] for v in current.values())
    if total < 4:
        return "Low post volume this week. Aim for 2+ posts/day across platforms."

    return "Posting consistently. Track which content pillars get the most engagement."


# ── main ───────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="AgentsFactory Weekly Social Report")
    parser.add_argument("--days", type=int, default=7, help="Number of days to report (default: 7)")
    parser.add_argument("--dry-run", action="store_true", help="Print report without posting to Slack")
    args = parser.parse_args()

    days = args.days
    print(f"=== AgentsFactory Social Report (last {days} days) ===\n")

    print("Fetching current period posts...")
    cur_posts = fetch_posts(days)
    print(f"  Found {len(cur_posts)} posts")

    print("Fetching previous period posts (for WoW)...")
    pre_posts = fetch_previous_period_posts(days)
    print(f"  Found {len(pre_posts)} posts\n")

    current  = analyse(cur_posts)
    previous = analyse(pre_posts)

    report = format_report(current, previous, days)
    print(report)

    # Save JSON
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rf = OUTPUT_DIR / f"social_report_{today}.json"
    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(rf, "w", encoding="utf-8") as f:
        json.dump(
            {
                "date":     today,
                "days":     days,
                "current":  current,
                "previous": previous,
                "report":   report,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"\nReport saved: {rf}")

    if not args.dry_run:
        print("\nPosting to Slack...")
        if _slack_post(report):
            print("✅ Posted to Slack")
        else:
            print("⚠️  Slack post failed — report saved locally")
    else:
        print("\n(dry run — not posting to Slack)")


if __name__ == "__main__":
    main()

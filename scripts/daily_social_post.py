"""
AgentsFactory Daily Social Post — direct execution, no LLM.
Posts to LinkedIn, Twitter, Instagram, Facebook via Ocoya.
Uses scheduled_at (3 min ahead) so Ocoya auto-publishes.
Cleans up old drafts. Verifies live status after 5 min.
"""
import json, os, sys, time, random, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path("C:/Users/Admin/Projects/AgentsFactory")
OUTPUT_DIR  = PROJECT_ROOT / "output"
sys.path.insert(0, str(PROJECT_ROOT / "src/agents"))

from ocoya_client import (
    post_to_linkedin, post_to_twitter, post_to_facebook, create_post,
    list_posts, delete_post, INSTAGRAM_PROFILE_ID,
    LINKEDIN_PROFILE_ID, TWITTER_PROFILE_ID, FACEBOOK_PROFILE_ID,
)

# Slack alerts
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from slack_alert import send_alert, format_error_alert

INSTAGRAM_MEDIA = [
    "https://phanindraintelligenzit-afk.github.io/AgentsFactory/social-assets/01_brand_welcome.png",
    "https://phanindraintelligenzit-afk.github.io/AgentsFactory/social-assets/04_services_overview.png",
    "https://phanindraintelligenzit-afk.github.io/AgentsFactory/social-assets/05_what_are_agents.png",
    "https://phanindraintelligenzit-afk.github.io/AgentsFactory/social-assets/07_testimonial.png",
    "https://phanindraintelligenzit-afk.github.io/AgentsFactory/social-assets/10_cta_dm.png",
]

POSTS = [
    {
        "linkedin": "We shipped AgentsFactory: working outreach, live social posting, and DPI-LS Scoring Engine as next priority.",
        "twitter": "AgentsFactory shipped: outreach + social posting live. Next: DPI-LS Scoring Engine.\n\n#BuildingInPublic #AIAgents",
        "instagram": "AgentsFactory shipped: outreach + social posting live. Next: DPI-LS Scoring Engine.",
        "facebook": "AgentsFactory shipped: outreach and social posting now live. Next: DPI-LS Scoring Engine.",
    },
    {
        "linkedin": "Clients don't want 'AI agents.' They want answers. AgentsFactory maps automation to real operations.",
        "twitter": "Hot take: clients don't want 'AI agents.' They want answers. Outcome first, tech second.\n\n#AIAgents #BuildingInPublic",
        "instagram": "Clients don't want 'AI agents.' They want answers. AgentsFactory maps automation to real operations.",
        "facebook": "Pivoted from generic AI promises to client-specific automation. Clients want answers, not 'AI agents.'",
    },
]


def _get_calendar_post() -> dict | None:
    """Try to get the next post from the content calendar. Returns None if empty."""
    try:
        # Import from sibling scripts directory
        scripts_dir = PROJECT_ROOT / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        from content_calendar import get_next_post  # type: ignore[import]
        post = get_next_post()
        if post is None:
            return None
        title = post.get("title", "")
        platform = post.get("platform", "linkedin")
        # Build a platform map from the calendar entry title
        # The calendar stores one platform per entry, so we adapt the title for each network
        return {
            "linkedin": f"{title}\n\n#AgentsFactory #BuildingInPublic",
            "twitter": f"{title}\n\n#AgentsFactory #BuildingInPublic",
            "instagram": title,
            "facebook": title,
        }
    except Exception as e:
        print(f"  ⚠️  Calendar lookup failed: {e}")
        return None

def adapt_twitter(caption):
    caption = caption.replace("→","->").replace("✅","✓").replace("💡","").replace("🤖","").replace("🚀","").replace("👇","")
    if len(caption) > 270:
        t = caption[:270]
        cut = max(t.rfind('.'), t.rfind('\n'))
        caption = t[:cut+1] if cut > 100 else t + "..."
    return caption

def clean_drafts():
    try:
        all_posts = list_posts(limit=100)
        drafts = [p for p in all_posts if p.get("status") == "DRAFT"]
        for d in drafts:
            delete_post(d["id"])
        return len(drafts)
    except Exception:
        return 0

def _retry_api(fn, *args, retries=3, delay=5, **kwargs):
    """Call an Ocoya API function with retry logic. Returns result or last exception."""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_err = e
            print(f"    ⚠️  Attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
    raise last_err


def do_post():
    # Dedup: check if we already posted today
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    existing = list_posts(status="POSTED", limit=50)
    already_posted = set()
    for p in existing:
        if p.get("createdAt", "").startswith(today):
            for profile in (p.get("socialProfiles") or []):
                already_posted.add(profile.get("id"))

    # Try calendar first, fall back to hardcoded posts
    calendar_post = _get_calendar_post()
    if calendar_post is not None:
        post_set = calendar_post
        print("  📅 Using post from content calendar")
    else:
        post_set = random.choice(POSTS)
        print("  📋 Using fallback hardcoded post")
    schedule_at = (datetime.now(timezone.utc) + timedelta(minutes=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    results = {}

    for platform, fn, pid in [
        ("linkedin", post_to_linkedin, LINKEDIN_PROFILE_ID),
        ("twitter", post_to_twitter, TWITTER_PROFILE_ID),
        ("facebook", post_to_facebook, FACEBOOK_PROFILE_ID),
    ]:
        if pid in already_posted:
            results[platform] = {"id": None, "status": "skipped", "error": "Already posted today"}
            print(f"  {platform}: SKIP (already posted today)")
            continue
        try:
            text = adapt_twitter(post_set[platform]) if platform == "twitter" else post_set[platform]
            r = _retry_api(fn, text, scheduled_at=schedule_at)
            pid = r.get("id") or r.get("postGroupId")
            results[platform] = {"id": pid, "status": "scheduled", "error": None}
            print(f"  {platform}: {pid} (scheduled)")
        except Exception as e:
            results[platform] = {"id": None, "status": "error", "error": str(e)}
            print(f"  {platform} FAIL: {e}")

    # Instagram needs media
    try:
        media = random.choice(INSTAGRAM_MEDIA)
        r = _retry_api(create_post, post_set["instagram"], [INSTAGRAM_PROFILE_ID], [media], schedule_at)
        pid = r.get("id") or r.get("postGroupId")
        results["instagram"] = {"id": pid, "status": "scheduled", "error": None}
        print(f"  instagram: {pid} (scheduled)")
    except Exception as e:
        results["instagram"] = {"id": None, "status": "error", "error": str(e)}
        print(f"  instagram FAIL: {e}")

    return results

def verify_live(results, wait=0.5):
    print(f"\nWaiting {wait}min...")
    time.sleep(wait * 60)
    posted_ids = {p["id"] for p in list_posts(status="POSTED", limit=100)}
    for platform, res in results.items():
        pid = res.get("id")
        if pid and pid in posted_ids:
            res["verified"] = "LIVE"
            print(f"  ✓ {platform}: LIVE")
        elif pid:
            res["verified"] = "PENDING"
            print(f"  ⏳ {platform}: not yet")
        else:
            res["verified"] = "FAILED"
            print(f"  ✗ {platform}: {res.get('error')}")
    return results

def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"=== AgentsFactory Social Post — {today} ===\n")

    try:
        n = clean_drafts()
        print(f"Cleaned {n} drafts\n")

        print("Posting (scheduled 3min ahead)...")
        results = do_post()

        results = verify_live(results)

        # Always write results JSON (even on partial failure)
        rf = OUTPUT_DIR / f"social_results_{today}.json"
        with open(rf, "w") as f:
            json.dump({"date": today, "results": results}, f, indent=2)
        print(f"\nResults: {rf}")

        # Build summary for Slack
        scheduled = sum(1 for r in results.values() if r.get("status") == "scheduled")
        skipped = sum(1 for r in results.values() if r.get("status") == "skipped")
        errors = sum(1 for r in results.values() if r.get("status") == "error")
        platforms = ", ".join(results.keys())
        status_emoji = "✅" if errors == 0 else "⚠️"
        summary = (
            f"{status_emoji} *Daily Social Post — {today}*\n"
            f"Platforms: {platforms}\n"
            f"Scheduled: {scheduled} | Skipped: {skipped} | Errors: {errors}"
        )
        send_alert("C0BBP317H7G", summary)

    except Exception as e:
        rf = OUTPUT_DIR / f"social_results_{today}.json"
        try:
            with open(rf, "w") as f:
                json.dump({"date": today, "results": {}, "fatal_error": str(e)}, f, indent=2)
        except Exception:
            pass
        alert_text = format_error_alert("daily_social_post.py", str(e), f"Date: {today}")
        send_alert("C0BBP317H7G", alert_text)
        print(f"\n❌ Fatal error: {e}")

if __name__ == "__main__":
    main()

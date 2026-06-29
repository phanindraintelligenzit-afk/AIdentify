#!/usr/bin/env python3
"""
Social Poster for AIdentify — replaces Ocaya.

Uses Twitter/X API v2 for direct posting (Phani has X Premium).
For LinkedIn, Instagram, Facebook — outputs drafts to files for manual posting
until Buffer/Later API is integrated.

Usage:
    python3 scripts/social_poster.py --project ai-competitive-intelligence-agent
    python3 scripts/social_poster.py --all-unpublished
    python3 scripts/social_poster.py --draft-only --project ai-competitive-intelligence-agent
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
PROJECTS_JSON = PROJECT_ROOT / "docs" / "data" / "projects.json"
POSTED_TRACKING = SCRIPT_DIR / "posted_projects.json"
DRAFTS_DIR = SCRIPT_DIR / "social_drafts"
DRAFTS_DIR.mkdir(exist_ok=True)

IST = timezone(timedelta(hours=5, minutes=30))
MARKETPLACE_URL = "https://phanindraintelligenzit-afk.github.io/AIdentify/docs/marketplace.html"


def load_projects():
    with open(PROJECTS_JSON) as f:
        return json.load(f).get("projects", [])


def load_posted():
    if POSTED_TRACKING.exists():
        return json.loads(POSTED_TRACKING.read_text())
    return {"posted": [], "last_run": None}


def save_posted(data):
    data["last_run"] = datetime.now(IST).isoformat()
    POSTED_TRACKING.write_text(json.dumps(data, indent=2))


def find_unposted(projects, posted_data):
    posted_ids = {p["id"] for p in posted_data.get("posted", [])}
    return [p for p in projects if p["id"] not in posted_ids]


def generate_post_content(project) -> dict:
    """Generate social media content for a project."""
    name = project["name"]
    desc = project.get("description", "")
    gh_url = project.get("github_url", "")
    agents_list = project.get("agents_list", [])
    num_agents = project.get("agents", len(agents_list))

    # Twitter/X post (280 char limit)
    twitter = (
        f"Just built and open-sourced: {name}\n\n"
        f"{desc[:100]}{'...' if len(desc) > 100 else ''}\n\n"
        f"🔗 {gh_url}\n\n"
        f"Built entirely by the AIdentify agent swarm. No humans touched the code."
    )
    if len(twitter) > 280:
        twitter = (
            f"Just built and open-sourced: {name}\n\n"
            f"{desc[:80]}{'...' if len(desc) > 80 else ''}\n\n"
            f"🔗 {gh_url}\n\n"
            f"Built entirely by the AIdentify agent swarm."
        )

    # LinkedIn post (longer form, 3000 char limit)
    linkedin = (
        f"We just open-sourced {name}.\n\n"
        f"{desc}\n\n"
        f"{num_agents} AI agents working together:\n"
    )
    for agent in agents_list:
        linkedin += f"• {agent}\n"
    linkedin += (
        f"\nAll built autonomously by the AIdentify agent swarm.\n\n"
        f"GitHub: {gh_url}\n"
        f"Marketplace: {MARKETPLACE_URL}"
    )

    # Instagram (visual + caption)
    instagram = (
        f"🤖 Just built: {name}\n\n"
        f"{desc[:150]}{'...' if len(desc) > 150 else ''}\n\n"
        f"Includes {num_agents} AI agents working in parallel.\n"
        f"Full source code is free on GitHub.\n\n"
        f"Link in bio → {gh_url}\n\n"
        f"#ai #opensource #automation"
    )

    # Facebook (similar to LinkedIn but shorter)
    facebook = (
        f"Open-sourcing {name} today.\n\n"
        f"{desc}\n\n"
        f"This project was built entirely by AI agents at AIdentify — "
        f"an autonomous AI agency. {num_agents} agents researched, coded, tested, and published it.\n\n"
        f"GitHub: {gh_url}\n"
        f"Marketplace: {MARKETPLACE_URL}"
    )

    return {
        "twitter": twitter,
        "linkedin": linkedin,
        "instagram": instagram,
        "facebook": facebook,
    }


def post_to_twitter(content: str, media_url: str = None) -> dict:
    """
    Post to Twitter/X using API v2.
    Requires TWITTER_BEARER_TOKEN, TWITTER_API_KEY, TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET env vars.
    """
    try:
        import tweepy
    except ImportError:
        return {"success": False, "error": "tweepy not installed. Run: pip install tweepy"}

    api_key = os.environ.get("TWITTER_API_KEY", "")
    api_secret = os.environ.get("TWITTER_API_SECRET", "")
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN", "")
    access_secret = os.environ.get("TWITTER_ACCESS_SECRET", "")

    if not all([api_key, api_secret, access_token, access_secret]):
        return {"success": False, "error": "Twitter credentials not configured. Set TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET env vars."}

    try:
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
        )

        # Handle media upload if provided
        media_ids = None
        if media_url:
            # For media, we need API v1.1
            auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
            api = tweepy.API(auth)
            import requests
            response = requests.get(media_url)
            temp_path = "/tmp/twitter_media.png"
            with open(temp_path, "wb") as f:
                f.write(response.content)
            media = api.media_upload(temp_path)
            media_ids = [media.media_id]

        response = client.create_tweet(text=content, media_ids=media_ids)
        return {"success": True, "id": response.data["id"]}
    except Exception as e:
        return {"success": False, "error": str(e)}


def save_draft(project_id: str, content: dict):
    """Save drafts to files for manual posting."""
    project_drafts = DRAFTS_DIR / project_id
    project_drafts.mkdir(exist_ok=True)

    for platform, text in content.items():
        draft_file = project_drafts / f"{platform}.txt"
        draft_file.write_text(text)
        print(f"  ✏️  Draft saved: {draft_file}")

    return project_drafts


def post_project(project: dict, dry_run: bool = False, post_twitter: bool = False) -> dict:
    """Post about a project on social media."""
    name = project["name"]
    project_id = project["id"]
    posts = generate_post_content(project)

    results = {"project": name, "id": project_id}

    print(f"\n📱 Social posting for: {name}")

    if dry_run:
        print("  [DRY RUN — no actual posting]")
        for platform, content in posts.items():
            print(f"\n  --- {platform.upper()} ({len(content)} chars) ---")
            print(f"  {content[:120]}...")
        results["dry_run"] = True
        results["drafts_dir"] = str(save_draft(project_id, posts))
        return results

    # Twitter/X — direct API post (if credentials available and post_twitter flag)
    if post_twitter:
        print("  🐦 Posting to Twitter/X...")
        twitter_result = post_to_twitter(posts["twitter"])
        results["twitter"] = twitter_result
        if twitter_result.get("success"):
            print(f"  ✅ Twitter: posted (ID: {twitter_result.get('id')})")
        else:
            print(f"  ❌ Twitter: {twitter_result.get('error')}")
            # Fall back to draft
            results["twitter"]["fallback"] = "draft"

    # LinkedIn, Instagram, Facebook — draft only for now
    for platform in ["linkedin", "instagram", "facebook"]:
        print(f"  📝 {platform}: draft saved (auto-posting not yet configured)")

    results["drafts_dir"] = str(save_draft(project_id, posts))
    return results


def post_all_unpublished(dry_run: bool = False, post_twitter: bool = False):
    """Post about all unpublished projects."""
    projects = load_projects()
    posted_data = load_posted()
    unposted = find_unposted(projects, posted_data)

    print(f"\n🚀 {len(unposted)} projects to post about")

    all_results = []
    for project in unposted:
        result = post_project(project, dry_run=dry_run, post_twitter=post_twitter)
        all_results.append(result)

        # Track as posted
        posted_data["posted"].append({
            "id": project["id"],
            "name": project["name"],
            "posted_at": datetime.now(IST).isoformat(),
            "platforms": result.get("platforms", ["draft"]),
        })

    save_posted(posted_data)
    print(f"\n✅ Done. {len(all_results)} projects posted/drafted.")
    print(f"📁 Drafts in: {DRAFTS_DIR}")
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIdentify Social Poster (replaces Ocaya)")
    parser.add_argument("--project", help="Post about a specific project by ID")
    parser.add_argument("--all-unpublished", action="store_true", help="Post about all new projects")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be posted")
    parser.add_argument("--post-twitter", action="store_true", help="Actually post to Twitter (requires creds)")
    parser.add_argument("--draft-only", action="store_true", help="Only save drafts, don't post anywhere")
    args = parser.parse_args()

    if args.project:
        projects = load_projects()
        project = next((p for p in projects if p["id"] == args.project), None)
        if not project:
            print(f"ERROR: Project '{args.project}' not found")
            print(f"Available: {[p['id'] for p in projects[:5]]}...")
            sys.exit(1)
        post_project(project, dry_run=args.dry_run, post_twitter=args.post_twitter)
    elif args.all_unpublished:
        post_all_unpublished(dry_run=args.dry_run, post_twitter=args.post_twitter)
    elif args.draft_only:
        if args.project:
            projects = load_projects()
            project = next((p for p in projects if p["id"] == args.project), None)
            if project:
                posts = generate_post_content(project)
                save_draft(project["id"], posts)
        else:
            print("--draft-only requires --project or use --all-unpublished")
    else:
        # Default: show drafts for unposted projects
        post_all_unpublished(dry_run=True)

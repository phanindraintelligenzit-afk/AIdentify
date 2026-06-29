#!/usr/bin/env python3
"""
Social Poster for AIdentify — uses Ocoya API.

Posts to Twitter/X, LinkedIn, Instagram, Facebook via Ocoya.
Fallback: saves drafts to files for manual posting.

Usage:
    python3 scripts/social_poster.py --project ai-competitive-intelligence-agent
    python3 scripts/social_poster.py --all-unpublished
    python3 scripts/social_poster.py --draft-only
    python3 scripts/social_poster.py --post --project ai-competitive-intelligence-agent
"""

import argparse
import json
import ssl
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
PROJECTS_JSON = PROJECT_ROOT / "docs" / "data" / "projects.json"
POSTED_TRACKING = SCRIPT_DIR / "posted_projects.json"
DRAFTS_DIR = SCRIPT_DIR / "social_drafts"
DRAFTS_DIR.mkdir(exist_ok=True)

IST = timezone(timedelta(hours=5, minutes=30))
MARKETPLACE_URL = "https://phanindraintelligenzit-afk.github.io/AIdentify/docs/marketplace.html"

# Ocoya config
OCOYA_BASE = "https://www.app.ocoya.com/api/_public/v1"
OCOYA_KEY = "dc835ba5-a773-4aa1-b2f5-7e1ed318c5b9"
OCOYA_WORKSPACE = "clapmus480dwb5vzyghnv5dku"

PROFILE_IDS = {
    "twitter": "cmdftz3un001870rrzbjc8o4",
    "linkedin": "cll7ytoyz002wl70fnxk0tjwr",
    "instagram": "cmdftzne6005l1hrgeacfi8sx",
    "facebook": "cmdftypmk005e1hrg1b7ow01b",
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


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


def generate_post_content(project: dict) -> dict:
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

    # LinkedIn post
    linkedin = f"We just open-sourced {name}.\n\n{desc}\n\n{num_agents} AI agents working together:\n"
    for agent in agents_list:
        linkedin += f"• {agent}\n"
    linkedin += (
        f"\nAll built autonomously by the AIdentify agent swarm.\n\n"
        f"GitHub: {gh_url}\nMarketplace: {MARKETPLACE_URL}"
    )

    # Instagram
    instagram = (
        f"🤖 Just built: {name}\n\n"
        f"{desc[:150]}{'...' if len(desc) > 150 else ''}\n\n"
        f"Includes {num_agents} AI agents working in parallel.\n"
        f"Full source code is free on GitHub.\n\n"
        f"Link in bio → {gh_url}"
    )

    # Facebook
    facebook = (
        f"Open-sourcing {name} today.\n\n{desc}\n\n"
        f"This project was built entirely by AI agents at AIdentify — "
        f"an autonomous AI agency. {num_agents} agents researched, coded, tested, and published it.\n\n"
        f"GitHub: {gh_url}\nMarketplace: {MARKETPLACE_URL}"
    )

    return {"twitter": twitter, "linkedin": linkedin, "instagram": instagram, "facebook": facebook}


def post_to_ocoya(platform: str, content: str, hours_from_now: int = 2) -> dict:
    """Post to a platform via Ocoya API."""
    profile_id = PROFILE_IDS[platform]
    post_time = (datetime.now(IST) + timedelta(hours=hours_from_now)).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = {
        "caption": content,
        "profileIds": [profile_id],
        "scheduledAt": post_time,
    }

    data = json.dumps(payload).encode()
    url = f"{OCOYA_BASE}/post?workspaceId={OCOYA_WORKSPACE}"
    req = urllib.request.Request(url, data=data, headers={
        "X-API-Key": OCOYA_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }, method="POST")

    try:
        resp = urllib.request.urlopen(req, timeout=15, context=SSL_CTX)
        result = json.loads(resp.read().decode())
        return {"success": True, "postGroupId": result.get("postGroupId"), "scheduledAt": post_time}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return {"success": False, "http_code": e.code, "error": error_body}
    except Exception as e:
        return {"success": False, "error": str(e)}


def save_draft(project_id: str, content: dict):
    """Save drafts to files for manual posting."""
    project_drafts = DRAFTS_DIR / project_id
    project_drafts.mkdir(exist_ok=True)
    for platform, text in content.items():
        draft_file = project_drafts / f"{platform}.txt"
        draft_file.write_text(text)
    return project_drafts


def post_project(project: dict, dry_run: bool = False, post: bool = False) -> dict:
    """Post about a project on all social platforms."""
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

    if post:
        # Post to all platforms via Ocoya
        for platform in ["twitter", "linkedin", "instagram", "facebook"]:
            print(f"  📤 Posting to {platform}...")
            result = post_to_ocaya(platform, posts[platform])
            results[platform] = result
            if result.get("success"):
                print(f"  ✅ {platform}: Scheduled (ID: {result.get('postGroupId')})")
            else:
                print(f"  ❌ {platform}: {result.get('error', result.get('http_code', 'unknown'))}")
                # Save draft as fallback
                save_draft(project_id, {platform: posts[platform]})
    else:
        # Draft only
        for platform in ["twitter", "linkedin", "instagram", "facebook"]:
            print(f"  📝 {platform}: draft saved")
        results["drafts_dir"] = str(save_draft(project_id, posts))

    return results


def post_all(dry_run: bool = False, post: bool = False):
    """Post about all unpublished projects."""
    projects = load_projects()
    posted_data = load_posted()
    unposted = find_unposted(projects, posted_data)

    print(f"\n🚀 {len(unposted)} projects to post about")

    all_results = []
    for project in unposted:
        result = post_project(project, dry_run=dry_run, post=post)
        all_results.append(result)
        posted_data["posted"].append({
            "id": project["id"],
            "name": project["name"],
            "posted_at": datetime.now(IST).isoformat(),
        })

    save_posted(posted_data)
    print(f"\n✅ Done. {len(all_results)} projects processed.")
    print(f"📁 Drafts in: {DRAFTS_DIR}")
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIdentify Social Poster (Ocoya)")
    parser.add_argument("--project", help="Post about a specific project by ID")
    parser.add_argument("--all-unpublished", action="store_true", help="Post about all new projects")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be posted")
    parser.add_argument("--post", action="store_true", help="Actually post via Ocoya")
    parser.add_argument("--draft-only", action="store_true", help="Only save drafts")
    args = parser.parse_args()

    if args.project:
        projects = load_projects()
        project = next((p for p in projects if p["id"] == args.project), None)
        if not project:
            print(f"ERROR: Project '{args.project}' not found")
            sys.exit(1)
        post_project(project, dry_run=args.dry_run, post=args.post)
    elif args.all_unpublished:
        post_all(dry_run=args.dry_run, post=args.post)
    else:
        post_all(dry_run=True)

#!/usr/bin/env python3
"""
Marketplace Auto-Sync
Scans marketplace/listings/ for published projects not yet in docs/data/projects.json,
adds them, commits, and pushes.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LISTINGS_DIR = REPO_ROOT / "marketplace" / "listings"
PROJECTS_JSON = REPO_ROOT / "docs" / "data" / "projects.json"

CATEGORY_ICONS = {
    "security": "🔐",
    "healthcare": "🏥",
    "realestate": "🏠",
    "ecommerce": "🛒",
    "legal": "⚖️",
    "hr": "👥",
    "marketing": "🎯",
    "finance": "💰",
    "devops": "⚙️",
    "other": "📦",
}


def git(*args, check=True):
    result = subprocess.run(
        ["git"] + list(args),
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=check,
    )
    return result


def load_projects():
    with open(PROJECTS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def save_projects(data):
    with open(PROJECTS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def listing_to_project(listing):
    """Convert a listing.json to a projects.json entry."""
    l = listing["listing"]
    cat = l.get("category", "other")
    tags = l.get("tags", [])[:4]  # cap at 4 tags for card display
    icon = CATEGORY_ICONS.get(cat, CATEGORY_ICONS["other"])
    gh_url = l.get("source_url", "")

    # Derive monetization string
    pricing = l.get("pricing", {})
    if pricing.get("model") == "free_tier_with_enterprise":
        monetization = f"Free repo ({pricing.get('free', 'MIT')}) + Enterprise pricing"
    else:
        monetization = "Free repo + setup available"

    return {
        "id": l["slug"],
        "name": l["title"],
        "description": l.get("tagline", l.get("description", ""))[:160],
        "category": cat,
        "icon": icon,
        "tags": tags,
        "agents": 4,
        "github_url": gh_url,
        "stars": 0,
        "forks": 0,
        "language": "Python",
        "monetization": monetization,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def find_published_listings():
    """Walk marketplace/listings/ and return all listing.json dicts with status=published."""
    listings = []
    if not LISTINGS_DIR.exists():
        return listings
    for subdir in sorted(LISTINGS_DIR.iterdir()):
        listing_file = subdir / "listing.json"
        if listing_file.exists():
            with open(listing_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("listing", {}).get("status") == "published":
                listings.append(data)
    return listings


def sync():
    print("🔍 Scanning marketplace/listings/ for published projects...")

    listings = find_published_listings()
    if not listings:
        print("No published listings found.")
        return

    projects_data = load_projects()
    existing_ids = {p["id"] for p in projects_data["projects"]}

    new_projects = []
    for listing in listings:
        slug = listing["listing"]["slug"]
        if slug in existing_ids:
            print(f"  ✓ {slug} — already in projects.json")
            continue
        project = listing_to_project(listing)
        new_projects.append(project)
        print(f"  + {slug} — NEW, adding to projects.json")

    if not new_projects:
        print("All listings already synced. Nothing to do.")
        return

    # Add new projects
    projects_data["projects"].extend(new_projects)
    projects_data["total_projects"] = len(projects_data["projects"])
    projects_data["generated_at"] = datetime.now(timezone.utc).isoformat()
    save_projects(projects_data)
    print(f"\n✅ Added {len(new_projects)} project(s) to projects.json")

    # Commit and push
    # Get current branch
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    current_branch = result.stdout.strip() or "main"

    git("add", "docs/data/projects.json")
    git("commit", "-m", f"feat: sync {len(new_projects)} new marketplace listing(s) to projects.json")
    git("push", "origin", current_branch)
    print(f"🚀 Pushed to {current_branch}.")

    # Deploy to gh-pages (force push current branch as gh-pages since docs/ is the site root)
    git("push", "origin", f"{current_branch}:gh-pages", "--force")
    print("🚀 Pushed to gh-pages — live site will update within ~2 min.")


if __name__ == "__main__":
    sync()
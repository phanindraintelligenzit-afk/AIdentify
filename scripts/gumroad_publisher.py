#!/usr/bin/env python3
"""Gumroad Product Publisher for AIdentify Marketplace.

Creates and publishes Gumroad products for each AI agent project.
Supports free + paid tiers (pay-what-you-want for free repos, fixed price for setup services).

Usage:
    python3 gumroad_publisher.py --list          # List all Gumroad products
    python3 gumroad_publisher.py --all           # Publish all unpublished projects
    python3 gumroad_publisher.py --project ID    # Publish a specific project by ID
    python3 gumroad_publisher.py --create        # Create products for all (dry run)
"""

import json
import os
import re
import sys
import urllib.request
import urllib.parse
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Config — token loaded from file (create scripts/.gumroad_token with the token)
_SCRIPT_DIR = Path(__file__).resolve().parent
_TOKEN_FILE = _SCRIPT_DIR / ".gumroad_token"
GUMROAD_TOKEN = _TOKEN_FILE.read_text().strip() if _TOKEN_FILE.exists() else ""
GUMROAD_SECRET = "vAQ8pGne5Qv9i2z4urmdTuef-xGAhyzm-OrOvhdxAA4"  # Not used for API v2
API_BASE = "https://api.gumroad.com/v2"
MARKETPLACE_DIR = Path(__file__).resolve().parent.parent
PROJECTS_JSON = MARKETPLACE_DIR / "docs" / "data" / "projects.json"
STATE_FILE = MARKETPLACE_DIR / "scripts" / "gumroad_state.json"

# Product templates by category
CATEGORY_TEMPLATES = {
    "healthcare": {
        "subtitle": "AI agent team that automates healthcare workflows",
        "tags": ["automation", "AI", "healthcare"],
    },
    "marketing": {
        "subtitle": "AI agent team that handles marketing automation",
        "tags": ["automation", "AI", "marketing"],
    },
    "legal": {
        "subtitle": "AI agent team that automates legal & compliance",
        "tags": ["automation", "AI", "legal"],
    },
    "security": {
        "subtitle": "AI agent security & governance layer",
        "tags": ["automation", "AI", "security"],
    },
    "productivity": {
        "subtitle": "AI agent team that handles operations",
        "tags": ["automation", "AI", "productivity"],
    },
    "finance": {
        "subtitle": "AI agent team that automates finance workflows",
        "tags": ["automation", "AI", "finance"],
    },
    "other": {
        "subtitle": "AI agent automation solution",
        "tags": ["automation", "AI"],
    },
}


def gumroad_request(method, endpoint, data=None):
    """Make a Gumroad API request."""
    url = f"{API_BASE}{endpoint}"
    if data is not None:
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {GUMROAD_TOKEN}")
    else:
        req = urllib.request.Request(url, method=method)
        req.add_header("Authorization", f"Bearer {GUMROAD_TOKEN}")

    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read().decode()), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        try:
            error_data = json.loads(body)
            return error_data, e.code
        except:
            return {"success": False, "error": body}, e.code


def load_state():
    """Load publishing state."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"products": {}}


def save_state(state):
    """Save publishing state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_projects():
    """Load projects from marketplace JSON."""
    if not PROJECTS_JSON.exists():
        print(f"ERROR: {PROJECTS_JSON} not found")
        return []
    data = json.loads(PROJECTS_JSON.read_text())
    return data.get("projects", [])


def slug_to_product_name(slug):
    """Convert slug to a nice product name."""
    return slug.replace("-", " ").title()


def create_product(project):
    """Create a Gumroad product for a project."""
    cat = project.get("category", "other")
    template = CATEGORY_TEMPLATES.get(cat, CATEGORY_TEMPLATES["other"])
    name = project["name"]
    slug = project["id"]
    gh_url = project.get("github_url", "")
    monetization = project.get("monetization", "Free repo + setup available")

    # Build description
    description = f"""{project.get('description', '')}

--
This project was built entirely by AI agents at AIdentify — an autonomous AI agency.

What you get:
• Full source code (Python, multi-agent pipeline)
• Tests, CI/CD, Dockerfile
• Documentation and setup guides
• MIT open-source license

Want it customized for your business? Select the "Done-for-You Setup" tier.

Built by AIdentify agent swarm 🤖
Marketplace: https://phanindraintelligenzit-afk.github.io/AIdentify/docs/marketplace.html
"""

    # Determine pricing from monetization string
    # Default: free repo + $2000 setup fee
    price_cents = 0  # Free tier (pay what you want minimum)
    customizable_price = True

    # Check if there's a setup price mentioned
    setup_match = re.search(r'\$?(\d+)[K]-?(\d+)?[K]?.*setup', monetization, re.IGNORECASE)
    if setup_match:
        min_price = int(setup_match.group(1))
        if min_price >= 10:
            # Price in thousands, convert to dollars for setup tier
            setup_price_cents = min_price * 100 * 100  # $2000 = 200000 cents
        else:
            setup_price_cents = min_price * 100
    else:
        setup_price_cents = 20000  # Default $2000 setup

    product_data = {
        "name": name,
        "description": description,
        "price": price_cents,  # 0 = free/pay-what-you-want
        "currency": "usd",
        "url": gh_url or f"https://phanindraintelligenzit-afk.github.io/AIdentify/docs/marketplace.html",
        "purchase_email_required": True,
        "customizable_price": customizable_price,
        "tags": template["tags"],
        "taxonomy_id": 266,  # Software
    }

    result, status = gumroad_request("POST", "/products", product_data)

    if result.get("success"):
        product = result["product"]
        print(f"  ✅ Created: {name}")
        print(f"     URL: {product.get('short_url', 'N/A')}")
        print(f"     ID: {product.get('id', 'N/A')}")
        return product
    else:
        print(f"  ❌ Failed to create {name}: {result}")
        return None


def add_tier(product_id, name, price_cents, description=""):
    """Add a paid tier to a product."""
    tier_data = {
        "product_id": product_id,
        "name": name,
        "price": price_cents,
        "currency": "usd",
        "description": description,
    }
    result, status = gumroad_request("POST", f"/products/{product_id}/variants", tier_data)
    if result.get("success"):
        print(f"  ✅ Added tier: {name} (${price_cents/100:.0f})")
        return result
    else:
        print(f"  ⚠️ Tier add result: {result}")
        return result


def publish_product(product_id):
    """Publish a product (make it publicly visible)."""
    result, status = gumroad_request("PUT", f"/products/{product_id}", {"published": True})
    if result.get("success"):
        print(f"  ✅ Published!")
        return True
    else:
        print(f"  ⚠️ Publish result: {result}")
        return False


def list_products():
    """List all Gumroad products."""
    result, status = gumroad_request("GET", "/products")
    if result.get("success"):
        products = result.get("products", [])
        print(f"\n📦 {len(products)} Gumroad products:\n")
        for p in products:
            status_icon = "🟢" if p.get("published") else "⚪"
            price = p.get("formatted_price", "?")
            print(f"  {status_icon} {p['name']} — {price} — {p.get('short_url', 'no URL')}")
            print(f"     ID: {p['id']} | Sales: {p.get('sales_count', 0)} | ${p.get('sales_usd_cents', 0)/100:.0f} earned")
        return products
    else:
        print(f"ERROR: {result}")
        return []


def publish_all(dry_run=False):
    """Publish all marketplace projects to Gumroad."""
    projects = load_projects()
    state = load_state()

    print(f"\n🚀 Publishing {len(projects)} projects to Gumroad...\n")

    for project in projects:
        slug = project["id"]
        name = project["name"]

        # Skip if already published
        if slug in state["products"]:
            existing = state["products"][slug]
            print(f"  ⏭️  Skipping {name} (already exists: {existing.get('url', '?')})")
            continue

        print(f"\n📋 Publishing: {name}")

        if dry_run:
            print(f"  [DRY RUN] Would create product for {name}")
            continue

        # Create product
        result = create_product(project)
        if not result:
            continue

        product_id = result["id"]

        # Add paid tier
        monetization = project.get("monetization", "")
        setup_match = re.search(r'\$?(\d+)[K]?', monetization)
        if setup_match:
            setup_k = int(setup_match.group(1))
            setup_cents = setup_k * 100 * 100 if setup_k < 100 else setup_k * 100
        else:
            setup_cents = 20000  # Default $200

        add_tier(
            product_id,
            f"Done-for-You Setup — {name}",
            setup_cents,
            f"We set up {name} for your business. Includes customization, deployment, integrations, and 30 days support."
        )

        # Publish
        publish_product(product_id)

        # Save state
        state["products"][slug] = {
            "id": product_id,
            "name": name,
            "url": result.get("short_url", ""),
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        save_state(state)

    print(f"\n✅ Done! {len(state['products'])} projects on Gumroad.")
    return state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gumroad Publisher for AIdentify")
    parser.add_argument("--list", action="store_true", help="List all products")
    parser.add_argument("--all", action="store_true", help="Publish all projects")
    parser.add_argument("--create", action="store_true", help="Dry run — show what would be created")
    args = parser.parse_args()

    if args.list:
        list_products()
    elif args.all:
        publish_all()
    elif args.create:
        publish_all(dry_run=True)
    else:
        # Default: list then offer to publish
        products = list_products()
        if not products:
            print("\nNo products yet. Run with --all to publish all projects.")
        elif args.all:
            publish_all()
        else:
            print("\nRun with --all to publish all projects, --list to view existing.")

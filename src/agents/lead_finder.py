"""Lead Finder subagent for AgentsFactory.

Searches for potential clients across multiple sources and populates the leads database.

Usage:
    python src/agents/lead_finder.py --source linkedin --limit 20
    python src/agents/lead_finder.py --source twitter --limit 10 --dry-run
    python src/agents/lead_finder.py --source reddit --limit 15
    python src/agents/lead_finder.py --source google_maps --limit 25
    python src/agents/lead_finder.py --source all --limit 50
    python src/agents/lead_finder.py --source all --limit 50 --dry-run --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import uuid
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # C:\Users\Admin\Projects\AgentsFactory
DB_PATH = PROJECT_ROOT / "agentsfactory_metrics.db"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Search queries per source
LINKEDIN_QUERIES = [
    "e-commerce founder India",
    "e-commerce founder United States",
    "Shopify store owner India",
    "Shopify store owner United States",
    "SaaS founder India",
    "SaaS founder United States",
    "small business owner India automation",
    "small business owner United States automation",
]

TWITTER_QUERIES = [
    "hiring operations manager automation",
    "struggling with manual work automation",
    "need help with automation business",
    "too much manual work business",
    "looking for automation solutions",
    "hire virtual assistant operations",
    "automate my business processes",
]

REDDIT_QUERIES = [
    "site:reddit.com/r/ecommerce automation help",
    "site:reddit.com/r/smallbusiness automate",
    "site:reddit.com/r/shopify automation",
    "site:reddit.com/r/SaaS operations help",
    "site:reddit.com/r/ecommerce hiring operations",
    "site:reddit.com/r/smallbusiness manual work",
]

GOOGLE_MAPS_QUERIES = [
    "dentists in Hyderabad contact",
    "dentists in Bangalore contact",
    "gyms in Hyderabad contact",
    "gyms in Bangalore contact",
    "restaurants in Hyderabad contact",
    "restaurants in Bangalore contact",
    "salons in Hyderabad contact",
    "salons in Bangalore contact",
]

# Pain keywords that boost lead score
PAIN_KEYWORDS = [
    "manual", "struggling", "overwhelmed", "hiring", "help needed",
    "automate", "automation", "too much work", "can't keep up",
    "bottleneck", "time-consuming", "repetitive", "tedious",
    "need help", "looking for solution", "frustrated",
    "waste of time", "inefficient", "streamline", "optimize",
]

# Target persona keywords
PERSONA_KEYWORDS = {
    "ecommerce": [
        "ecommerce", "e-commerce", "shopify", "store", "shop",
        "selling online", "product", "dropshipping", "woocommerce",
    ],
    "saas": [
        "saas", "software", "platform", "app", "subscription",
        "b2b", "b2c", "tech startup",
    ],
    "local_business": [
        "local", "clinic", "gym", "restaurant", "salon", "dental",
        "dentist", "fitness", "spa", "hotel", "cafe",
    ],
}


# ---------------------------------------------------------------------------
# HTML stripping helper
# ---------------------------------------------------------------------------

class _Stripper(HTMLParser):
    """Minimal HTML tag stripper."""
    def __init__(self):
        super().__init__()
        self.result: list[str] = []

    def handle_data(self, data: str) -> None:
        self.result.append(data)

    def get_text(self) -> str:
        return " ".join(self.result).strip()


def strip_html(html: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    s = _Stripper()
    try:
        s.feed(html)
        return re.sub(r"\s+", " ", s.get_text()).strip()
    except Exception:
        return re.sub(r"<[^>]+>", "", html).strip()


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def ensure_tables() -> None:
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS leads ("
        "id TEXT PRIMARY KEY, name TEXT, company TEXT, email TEXT, "
        "phone TEXT, source TEXT DEFAULT 'inbound', stage TEXT DEFAULT 'new', "
        "score INTEGER DEFAULT 0, notes TEXT DEFAULT '', "
        "created_at TEXT DEFAULT (datetime('now')), "
        "updated_at TEXT DEFAULT (datetime('now')));"
        ""
        "CREATE TABLE IF NOT EXISTS agent_activity ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, agent_name TEXT NOT NULL, "
        "action TEXT NOT NULL, target TEXT DEFAULT '', "
        "status TEXT DEFAULT 'completed', details TEXT DEFAULT '', "
        "created_at TEXT DEFAULT (datetime('now')));"
    )
    conn.commit()
    conn.close()


def lead_exists(email: str = "", name: str = "", company: str = "") -> bool:
    """Check if a lead already exists in the database."""
    conn = get_db()
    if email:
        row = conn.execute("SELECT 1 FROM leads WHERE email = ?", (email,)).fetchone()
        if row:
            conn.close()
            return True
    if name and company:
        row = conn.execute(
            "SELECT 1 FROM leads WHERE name = ? AND company = ?",
            (name, company),
        ).fetchone()
        if row:
            conn.close()
            return True
    conn.close()
    return False


def insert_lead(lead: dict) -> bool:
    """Insert a lead into the database. Returns True if inserted, False if duplicate."""
    if lead_exists(
        email=lead.get("email", ""),
        name=lead.get("name", ""),
        company=lead.get("company", ""),
    ):
        return False

    lead_id = f"lead_{uuid.uuid4().hex[:12]}"
    conn = get_db()
    conn.execute(
        "INSERT INTO leads (id, name, company, email, phone, source, stage, score, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, 'new', ?, ?)",
        (
            lead_id,
            lead.get("name", ""),
            lead.get("company", ""),
            lead.get("email", ""),
            lead.get("phone", ""),
            lead.get("source", "unknown"),
            lead.get("score", 0),
            lead.get("notes", ""),
        ),
    )
    conn.commit()
    conn.close()
    return True


def log_activity(
    action: str,
    target: str = "",
    status: str = "completed",
    details: str = "",
) -> None:
    """Log agent activity to the database."""
    conn = get_db()
    conn.execute(
        "INSERT INTO agent_activity (agent_name, action, target, status, details) "
        "VALUES (?, ?, ?, ?, ?)",
        ("lead_finder", action, target, status, details),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

def score_lead(lead: dict) -> int:
    """
    Score a lead from 0-100 based on:
    - Persona match (0-40 points)
    - Pain signals (0-30 points)
    - Engagement/activity signals (0-15 points)
    - Source quality (0-15 points)
    """
    score = 0
    text = " ".join(
        str(lead.get(k, ""))
        for k in ("name", "company", "notes", "title")
    ).lower()

    # --- Persona match (0-40) ---
    best_persona = 0
    for persona, keywords in PERSONA_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text)
        if matches:
            best_persona = max(best_persona, min(matches * 10, 40))
    score += best_persona

    # --- Pain signals (0-30) ---
    pain_count = sum(1 for kw in PAIN_KEYWORDS if kw in text)
    score += min(pain_count * 6, 30)

    # --- Source quality (0-15) ---
    source_quality = {
        "linkedin": 12,
        "twitter": 10,
        "reddit": 8,
        "google_maps": 10,
    }
    score += source_quality.get(lead.get("source", ""), 5)

    # --- Engagement signals (0-15) ---
    if lead.get("email"):
        score += 5
    if lead.get("phone"):
        score += 3
    if lead.get("company"):
        score += 4
    if len(lead.get("notes", "")) > 50:
        score += 3

    return min(score, 100)


# ---------------------------------------------------------------------------
# Web search helper
# ---------------------------------------------------------------------------

def fetch_html(url: str, timeout: int = 15) -> str:
    """Fetch HTML from a URL with standard headers."""
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def search_bing(query: str) -> tuple[list[str], list[str]]:
    """
    Search Bing and return (titles, snippets).
    Uses the HTML version to avoid JS challenges.
    """
    url = f"https://www.bing.com/search?q={quote_plus(query)}"
    try:
        html = fetch_html(url)
    except Exception:
        return [], []

    # Extract result titles and snippets from Bing HTML
    titles: list[str] = []
    snippets: list[str] = []

    # Bing results are in <li class="b_algo"> blocks
    for block in re.findall(r'<li class="b_algo">(.*?)</li>', html, re.DOTALL):
        title_match = re.search(r'<a[^>]+href="[^"]+"[^>]*>(.*?)</a>', block, re.DOTALL)
        if title_match:
            titles.append(strip_html(title_match.group(1)))
        else:
            titles.append("")

        # Snippet is usually in <p> or <div class="b_caption">
        snip_match = re.search(r'<p>(.*?)</p>', block, re.DOTALL)
        if not snip_match:
            snip_match = re.search(
                r'<div class="b_caption">(.*?)</div>', block, re.DOTALL
            )
        snippets.append(strip_html(snip_match.group(1)) if snip_match else "")

    return titles, snippets


def search_ddg(query: str) -> tuple[list[str], list[str]]:
    """
    Search DuckDuckGo HTML and return (titles, snippets).
    """
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        html = fetch_html(url)
    except Exception:
        return [], []

    titles: list[str] = []
    snippets: list[str] = []

    result_blocks = re.findall(
        r'<a rel="nofollow" class="result__a" href="[^"]+">(.*?)</a>',
        html,
        re.DOTALL,
    )
    snippet_blocks = re.findall(
        r'<a rel="nofollow" class="result__snippet"[^>]*>(.*?)</a>',
        html,
        re.DOTALL,
    )

    for i, raw_title in enumerate(result_blocks):
        titles.append(strip_html(raw_title))
        snip = strip_html(snippet_blocks[i]) if i < len(snippet_blocks) else ""
        snippets.append(snip)

    return titles, snippets


def search(query: str) -> tuple[list[str], list[str]]:
    """Try multiple search engines, return first successful result."""
    for engine_fn in (search_bing, search_ddg):
        try:
            titles, snippets = engine_fn(query)
            if titles:
                return titles, snippets
        except Exception:
            continue
    return [], []


# ---------------------------------------------------------------------------
# Source: LinkedIn
# ---------------------------------------------------------------------------

def search_linkedin(limit: int = 20, dry_run: bool = False) -> list[dict]:
    """Search for LinkedIn profiles of potential leads."""
    leads: list[dict] = []
    seen: set[str] = set()

    for query in LINKEDIN_QUERIES:
        if len(leads) >= limit:
            break

        titles, snippets = search(f"site:linkedin.com/in {query}")
        time.sleep(0.8)

        for i, title in enumerate(titles):
            if len(leads) >= limit:
                break
            if not title or "linkedin" not in title.lower():
                # Check snippet for linkedin URL
                snip = snippets[i] if i < len(snippets) else ""
                if "linkedin.com/in" not in snip.lower():
                    continue

            # Parse name from title: "Name - Title - Company | LinkedIn"
            name = title.split(" - ")[0].strip() if " - " in title else title
            company = ""
            if " - " in title:
                parts = title.split(" - ")
                if len(parts) >= 3:
                    company = parts[-2].strip()
                elif len(parts) == 2:
                    company = parts[1].strip().replace(" | LinkedIn", "")

            key = f"{name}|{company}".lower()
            if key in seen or not name:
                continue
            seen.add(key)

            snip = snippets[i] if i < len(snippets) else ""
            lead = {
                "name": name,
                "company": company,
                "email": "",
                "phone": "",
                "source": "linkedin",
                "notes": f"LinkedIn: {title}. {snip[:200]}",
                "_title": title,
            }
            lead["score"] = score_lead(lead)
            leads.append(lead)

    return leads[:limit]


# ---------------------------------------------------------------------------
# Source: Twitter/X
# ---------------------------------------------------------------------------

def search_twitter(limit: int = 20, dry_run: bool = False) -> list[dict]:
    """Search for people posting about automation needs on Twitter/X."""
    leads: list[dict] = []
    seen: set[str] = set()

    for query in TWITTER_QUERIES:
        if len(leads) >= limit:
            break

        titles, snippets = search(f"site:twitter.com {query}")
        time.sleep(0.8)

        for i, title in enumerate(titles):
            if len(leads) >= limit:
                break
            if not title:
                continue

            snip = snippets[i] if i < len(snippets) else ""
            key = title.lower()
            if key in seen:
                continue
            seen.add(key)

            lead = {
                "name": title[:50],
                "company": "",
                "email": "",
                "phone": "",
                "source": "twitter",
                "notes": f"Twitter post: {snip[:300]}",
                "_title": title,
            }
            lead["score"] = score_lead(lead)
            leads.append(lead)

    return leads[:limit]


# ---------------------------------------------------------------------------
# Source: Reddit
# ---------------------------------------------------------------------------

def search_reddit(limit: int = 20, dry_run: bool = False) -> list[dict]:
    """Scan Reddit for people asking for help."""
    leads: list[dict] = []
    seen: set[str] = set()

    for query in REDDIT_QUERIES:
        if len(leads) >= limit:
            break

        titles, snippets = search(query)
        time.sleep(0.8)

        for i, title in enumerate(titles):
            if len(leads) >= limit:
                break
            if not title:
                continue

            snip = snippets[i] if i < len(snippets) else ""
            key = title.lower()
            if key in seen:
                continue
            seen.add(key)

            lead = {
                "name": f"Reddit: {title[:40]}",
                "company": "",
                "email": "",
                "phone": "",
                "source": "reddit",
                "notes": f"Reddit post: {title}. {snip[:200]}",
                "_title": title,
            }
            lead["score"] = score_lead(lead)
            leads.append(lead)

    return leads[:limit]


# ---------------------------------------------------------------------------
# Source: Google Maps / Local Business
# ---------------------------------------------------------------------------

def search_google_maps(limit: int = 20, dry_run: bool = False) -> list[dict]:
    """Search for local businesses in Hyderabad and Bangalore."""
    leads: list[dict] = []
    seen: set[str] = set()

    for query in GOOGLE_MAPS_QUERIES:
        if len(leads) >= limit:
            break

        titles, snippets = search(f"{query} email phone")
        time.sleep(0.8)

        for i, title in enumerate(titles):
            if len(leads) >= limit:
                break
            if not title:
                continue

            snip = snippets[i] if i < len(snippets) else ""

            # Extract email
            email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", snip)
            email = email_match.group(0) if email_match else ""

            # Extract phone
            phone_match = re.search(r"[\+]?[\d\s\-\(\)]{7,}", snip)
            phone = phone_match.group(0).strip() if phone_match else ""

            key = title.lower()
            if key in seen:
                continue
            seen.add(key)

            lead = {
                "name": title.split(" - ")[0].strip() if " - " in title else title,
                "company": title,
                "email": email,
                "phone": phone,
                "source": "google_maps",
                "notes": f"Local business: {query}. {snip[:200]}",
                "_title": title,
            }
            lead["score"] = score_lead(lead)
            leads.append(lead)

    return leads[:limit]


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def display_leads_table(leads: list[dict]) -> None:
    """Display leads in a compact table format."""
    if not leads:
        print("\n  No leads found.\n")
        return

    print(f"\n{'─'*100}")
    print(
        f"  {'#':<4} {'Name':<25} {'Company':<25} "
        f"{'Source':<12} {'Score':<8} {'Email':<20}"
    )
    print(f"{'─'*100}")

    for i, lead in enumerate(leads, 1):
        name = lead["name"][:24]
        company = (lead.get("company") or "")[:24]
        source = lead["source"][:11]
        score = f"{lead['score']}/100"
        email = (lead.get("email") or "")[:19]
        print(f"  {i:<4} {name:<25} {company:<25} {source:<12} {score:<8} {email:<20}")

    print(f"{'─'*100}")
    print(f"  Total: {len(leads)} leads\n")


def display_leads_detailed(leads: list[dict]) -> None:
    """Pretty-print leads with full details."""
    if not leads:
        print("\n  No leads found.\n")
        return

    print(f"\n{'='*80}")
    print(f"  Found {len(leads)} lead(s)")
    print(f"{'='*80}")

    for i, lead in enumerate(leads, 1):
        score_bar = "█" * (lead["score"] // 10) + "░" * (10 - lead["score"] // 10)
        print(f"\n  [{i}] {lead['name']}")
        print(f"      Company:  {lead.get('company', 'N/A')}")
        print(f"      Email:    {lead.get('email', 'N/A')}")
        print(f"      Phone:    {lead.get('phone', 'N/A')}")
        print(f"      Source:   {lead['source']}")
        print(f"      Score:    [{score_bar}] {lead['score']}/100")
        notes = lead.get("notes", "")[:120]
        print(f"      Notes:    {notes}")

    print(f"\n{'='*80}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="AgentsFactory Lead Finder — Find potential clients",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/agents/lead_finder.py --source linkedin --limit 20
  python src/agents/lead_finder.py --source twitter --limit 10 --dry-run
  python src/agents/lead_finder.py --source reddit --limit 15
  python src/agents/lead_finder.py --source google_maps --limit 25
  python src/agents/lead_finder.py --source all --limit 50 --dry-run
  python src/agents/lead_finder.py --source all --limit 50 --dry-run --json
        """,
    )
    parser.add_argument(
        "--source",
        choices=["linkedin", "twitter", "reddit", "google_maps", "all"],
        default="all",
        help="Lead source to search (default: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of leads to find (default: 20)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print leads without inserting into database",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=0,
        help="Minimum lead score to include (0-100, default: 0)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output leads as JSON",
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed lead info instead of table",
    )

    args = parser.parse_args()

    ensure_tables()

    print(f"\n🔍 AgentsFactory Lead Finder")
    print(f"   Source:    {args.source}")
    print(f"   Limit:     {args.limit}")
    print(f"   Dry run:   {args.dry_run}")
    print(f"   Min score: {args.min_score}")
    print()

    source_map = {
        "linkedin": search_linkedin,
        "twitter": search_twitter,
        "reddit": search_reddit,
        "google_maps": search_google_maps,
    }

    all_leads: list[dict] = []

    if args.source == "all":
        per_source_limit = max(args.limit // 4, 5)
        for src_name, src_func in source_map.items():
            print(f"  → Searching {src_name} (limit: {per_source_limit})...")
            try:
                found = src_func(limit=per_source_limit, dry_run=args.dry_run)
                all_leads.extend(found)
                print(f"    Found {len(found)} leads from {src_name}")
            except Exception as e:
                print(f"    [ERROR] {src_name} search failed: {e}")
    else:
        print(f"  → Searching {args.source} (limit: {args.limit})...")
        try:
            all_leads = source_map[args.source](
                limit=args.limit, dry_run=args.dry_run
            )
            print(f"    Found {len(all_leads)} leads")
        except Exception as e:
            print(f"    [ERROR] {args.source} search failed: {e}")

    # Filter by min score
    if args.min_score > 0:
        all_leads = [l for l in all_leads if l["score"] >= args.min_score]

    # Sort by score descending
    all_leads.sort(key=lambda x: x["score"], reverse=True)

    # Output
    if args.json:
        output = [
            {k: v for k, v in lead.items() if k != "_title"}
            for lead in all_leads
        ]
        print(json.dumps(output, indent=2))
    elif args.detailed:
        display_leads_detailed(all_leads)
    else:
        display_leads_table(all_leads)

    # Insert into database (unless dry-run)
    if not args.dry_run and all_leads:
        inserted = 0
        skipped = 0
        for lead in all_leads:
            lead.pop("_title", None)
            if insert_lead(lead):
                inserted += 1
            else:
                skipped += 1

        print(f"📊 Database update:")
        print(f"   Inserted: {inserted} new leads")
        print(f"   Skipped:  {skipped} duplicates")

        log_activity(
            action="lead_search",
            target=args.source,
            status="completed",
            details=(
                f"Found {len(all_leads)} leads, inserted {inserted}, "
                f"skipped {skipped} duplicates. Source: {args.source}"
            ),
        )
        print(f"   Activity logged.")
    elif args.dry_run:
        print(f"🏃 Dry run — no database changes made.")
        log_activity(
            action="lead_search_dry_run",
            target=args.source,
            status="completed",
            details=(
                f"Dry run: found {len(all_leads)} leads from {args.source}. "
                f"No DB changes."
            ),
        )

    print(f"\n✅ Lead Finder complete.\n")


if __name__ == "__main__":
    main()

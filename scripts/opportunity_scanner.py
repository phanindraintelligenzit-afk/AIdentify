#!/usr/bin/env python3
"""AIdentify Business Opportunity Scanner — Daily Morning Edition.

Fetches opportunities from multiple sources, scores them, and outputs
a clean morning briefing for Phani.

Usage:
    python opportunity_scanner.py           # Full scan + briefing
    python opportunity_scanner.py --json    # Raw JSON output
    python opportunity_scanner.py --quick   # Quick summary only

Sources:
    - Hacker News (Ask HN, Show HN, Top)
    - dev.to (automation/business tags)
    - GitHub Trending (Python)
    - Lobste.rs
    - Reddit (r/startups, r/SaaS, r/sideproject)
    - Indie Hackers
    - Product Hunt
    - DuckDuckGo
    - OpenRouter LLM analysis (optional, --llm flag)
"""

from __future__ import annotations

import json
import os
import re
import socket
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

# Global socket timeout to prevent hangs
socket.setdefaulttimeout(10)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime.now(IST)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Pain keywords that signal business opportunity
PAIN_KEYWORDS = [
    "manual", "struggling", "overwhelmed", "hiring", "help needed",
    "automate", "automation", "too much work", "can't keep up",
    "bottleneck", "time-consuming", "repetitive", "tedious",
    "need help", "looking for solution", "frustrated",
    "waste of time", "inefficient", "streamline", "optimize",
    "no tool", "no solution", "expensive", "affordable",
    "scaling", "growth", "revenue", "profit", "ROI",
]

# High-value business opportunity keywords
OPPORTUNITY_KEYWORDS = [
    "AI agent", "LLM", "automation", "workflow", "SaaS",
    "no-code", "low-code", "API", "integration", "bot",
    "scraping", "monitoring", "analytics", "dashboard",
    "lead gen", "outreach", "CRM", "email marketing",
    "compliance", "audit", "security", "observability",
]

# Target industries
INDUSTRIES = {
    "healthcare": ["healthcare", "medical", "pharma", "clinical", "HIPAA", "EHR", "patient"],
    "ecommerce": ["ecommerce", "e-commerce", "shopify", "store", "product", "dropshipping"],
    "legal": ["legal", "law", "contract", "compliance", "GDPR", "SOC2"],
    "hr": ["HR", "hiring", "recruiting", "onboarding", "resume", "candidate"],
    "finance": ["finance", "accounting", "reconciliation", "invoice", "payment", "SOX"],
    "marketing": ["marketing", "content", "SEO", "social media", "analytics", "outreach"],
    "devtools": ["developer", "CI/CD", "deployment", "monitoring", "observability", "DevOps"],
    "realestate": ["real estate", "property", "listing", "brokerage", "lead"],
}


# ---------------------------------------------------------------------------
# HTML stripping helper
# ---------------------------------------------------------------------------

class _Stripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result: list[str] = []

    def handle_data(self, data: str) -> None:
        self.result.append(data)

    def get_text(self) -> str:
        return " ".join(self.result).strip()


def strip_html(html: str) -> str:
    s = _Stripper()
    try:
        s.feed(html)
        return re.sub(r"\s+", " ", s.get_text()).strip()
    except Exception:
        return re.sub(r"<[^>]+>", "", html).strip()


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def fetch_url(url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


# ---------------------------------------------------------------------------
# Source: Hacker News (Ask HN)
# ---------------------------------------------------------------------------

def fetch_hn_ask(limit: int = 25) -> list[dict]:
    """Fetch top Ask HN stories — goldmine for pain points."""
    url = "https://hacker-news.firebaseio.com/v0/askstories.json"
    try:
        raw = fetch_url(url)
        ids = json.loads(raw)
    except Exception:
        return []

    results = []
    for story_id in ids[:limit]:
        try:
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            raw_item = fetch_url(item_url)
            item = json.loads(raw_item)
            if not item or item.get("type") != "story" or not item.get("title"):
                continue
            title = item["title"]
            # Only Ask HN posts (start with "Ask HN:")
            if not title.startswith("Ask HN:"):
                continue
            text = item.get("text", "")[:800]
            results.append({
                "source": "hackernews",
                "title": title.replace("Ask HN: ", ""),
                "url": f"https://news.ycombinator.com/item?id={story_id}",
                "score": item.get("score", 0),
                "comments": item.get("descendants", 0),
                "text": strip_html(text),
                "author": item.get("by", ""),
            })
        except Exception:
            continue
    return results


def fetch_hn_show(limit: int = 15) -> list[dict]:
    """Fetch top Show HN stories — product launches & ideas."""
    url = "https://hacker-news.firebaseio.com/v0/showstories.json"
    try:
        raw = fetch_url(url)
        ids = json.loads(raw)
    except Exception:
        return []

    results = []
    for story_id in ids[:limit]:
        try:
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            raw_item = fetch_url(item_url)
            item = json.loads(raw_item)
            if not item or item.get("type") != "story" or not item.get("title"):
                continue
            title = item["title"]
            if not title.startswith("Show HN:"):
                continue
            text = item.get("text", "")[:800]
            results.append({
                "source": "hackernews",
                "title": title.replace("Show HN: ", ""),
                "url": item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
                "score": item.get("score", 0),
                "comments": item.get("descendants", 0),
                "text": strip_html(text),
                "author": item.get("by", ""),
            })
        except Exception:
            continue
    return results


# ---------------------------------------------------------------------------
# Source: dev.to
# ---------------------------------------------------------------------------

def fetch_devto(tag: str = "automation", per_page: int = 15) -> list[dict]:
    """Fetch recent dev.to articles for automation/business trends."""
    url = f"https://dev.to/api/articles?tag={tag}&per_page={per_page}&top=7"
    try:
        raw = fetch_url(url)
        data = json.loads(raw)
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        results.append({
            "source": "devto",
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "reactions": item.get("positive_reactions_count", 0),
            "comments": item.get("comments_count", 0),
            "tags": item.get("tag_list", []),
            "author": item.get("user", {}).get("name", ""),
            "text": item.get("description", "")[:500],
        })
    return results


# ---------------------------------------------------------------------------
# Source: GitHub Trending (Python)
# ---------------------------------------------------------------------------

def fetch_github_trending(limit: int = 15) -> list[dict]:
    """Scrape GitHub trending Python repos for product ideas."""
    url = "https://github.com/trending/python?since=daily"
    try:
        html = fetch_url(url)
    except Exception:
        return []

    results = []
    # Parse repo cards
    repo_blocks = re.findall(
        r'<h2 class="h3 lh-condensed">.*?<a href="(/[^"]+)"[^>]*>\s*([^<]*?)\s*/\s*([^<]*?)\s*</a>',
        html,
        re.DOTALL,
    )

    for match in repo_blocks[:limit]:
        path, owner, name = match
        repo_name = f"{owner.strip()}/{name.strip()}"
        results.append({
            "source": "github",
            "title": repo_name,
            "url": f"https://github.com{path}",
            "stars": 0,  # Would need more parsing
            "text": f"Trending Python repo: {repo_name}",
        })

    # Fallback: simpler regex if the above doesn't match
    if not results:
        links = re.findall(r'href="(/[^"]+/[^"]+)"[^>]*class="[^"]*Link[^"]*"', html)
        seen = set()
        for link in links[:limit]:
            parts = link.strip("/").split("/")
            if len(parts) == 2 and link not in seen:
                seen.add(link)
                results.append({
                    "source": "github",
                    "title": f"{parts[0]}/{parts[1]}",
                    "url": f"https://github.com{link}",
                    "stars": 0,
                    "text": f"Trending Python repo: {parts[0]}/{parts[1]}",
                })

    return results


# ---------------------------------------------------------------------------
# Source: DuckDuckGo HTML search for "AI automation business ideas"
# ---------------------------------------------------------------------------

def search_ddg(query: str, limit: int = 10) -> list[dict]:
    """Search DuckDuckGo HTML for business opportunities."""
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        html = fetch_url(url)
    except Exception:
        return []

    results = []
    titles = re.findall(
        r'<a rel="nofollow" class="result__a" href="[^"]+">(.*?)</a>',
        html, re.DOTALL,
    )
    snippets = re.findall(
        r'<a rel="nofollow" class="result__snippet"[^>]*>(.*?)</a>',
        html, re.DOTALL,
    )

    for i, raw_title in enumerate(titles[:limit]):
        title = strip_html(raw_title)
        snippet = strip_html(snippets[i]) if i < len(snippets) else ""
        results.append({
            "source": "search",
            "title": title,
            "url": "",
            "text": snippet[:500],
        })

    return results


# ---------------------------------------------------------------------------
# Lobste.rs (API)
# ---------------------------------------------------------------------------

def fetch_lobsters(limit: int = 15) -> list[dict]:
    """Fetch top Lobste.rs stories."""
    try:
        raw = fetch_url("https://lobste.rs/hottest.json")
        data = json.loads(raw)
    except Exception:
        return []

    results = []
    for item in data[:limit]:
        if not isinstance(item, dict):
            continue
        short_id = item.get("short_id", "")
        tags = item.get("tags", [])
        results.append({
            "source": "lobsters",
            "title": item.get("title", ""),
            "url": item.get("url", f"https://lobste.rs/s/{short_id}"),
            "score": item.get("score", 0),
            "comments": item.get("comment_count", 0),
            "tags": tags,
            "text": f"{item.get('title','')} | tags: {', '.join(tags)}",
        })
    return results


# ---------------------------------------------------------------------------
# Reddit (old.reddit JSON, no auth)
# ---------------------------------------------------------------------------

def fetch_reddit(subreddit: str = "startups", limit: int = 20) -> list[dict]:
    url = f"https://old.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    try:
        data = json.loads(fetch_url(url))
    except Exception:
        return []

    results = []
    for post in data.get("data", {}).get("children", []):
        p = post.get("data", {})
        if p.get("stickied"):
            continue
        selftext = p.get("selftext", "")[:600]
        results.append({
            "source": "reddit",
            "title": p.get("title", ""),
            "url": f"https://reddit.com{p.get('permalink', '')}",
            "score": p.get("ups", 0),
            "comments": p.get("num_comments", 0),
            "author": p.get("author", ""),
            "text": selftext or p.get("title", ""),
            "flair": p.get("link_flair_text", ""),
        })
    return results


# ---------------------------------------------------------------------------
# Indie Hackers (HTML scrape)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Hacker News Front Page
# ---------------------------------------------------------------------------

def fetch_hn_top(limit: int = 20) -> list[dict]:
    """Fetch HN top stories (beyond ask/show)."""
    try:
        raw = fetch_url("https://hacker-news.firebaseio.com/v0/topstories.json")
        ids = json.loads(raw)
    except Exception:
        return []

    results = []
    fetched = 0
    for story_id in ids:
        if fetched >= limit:
            break
        try:
            item = json.loads(fetch_url(
                f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"))
            if not item or item.get("type") != "story":
                continue
            title = item.get("title", "")
            # Skip job posts
            if title.startswith("YC") or " is hiring" in title.lower():
                continue
            text = item.get("text", "")[:600]
            # Skip low-engagement link-only posts
            if not text and not title.startswith(("Show HN:", "Ask HN:")):
                if item.get("score", 0) < 30:
                    continue
            results.append({
                "source": "hackernews",
                "title": title,
                "url": item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
                "score": item.get("score", 0),
                "comments": item.get("descendants", 0),
                "text": strip_html(text),
                "author": item.get("by", ""),
            })
            fetched += 1
        except Exception:
            continue
    return results


# ---------------------------------------------------------------------------
# LLM Analysis via OpenRouter (free models)
# ---------------------------------------------------------------------------

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_FREE_MODELS = [
    "qwen/qwen3-coder:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "openai/gpt-oss-120b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
]
_or_api_key: Optional[str] = None


def _get_openrouter_key() -> Optional[str]:
    """Get OpenRouter API key from env or config file."""
    global _or_api_key
    if _or_api_key is not None:
        return _or_api_key
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        _or_api_key = key
        return key
    # Try local config
    cfg = Path(__file__).resolve().parent / "scanner_config.json"
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text())
            _or_api_key = data.get("openrouter_api_key", "")
            if _or_api_key:
                return _or_api_key
        except Exception:
            pass
    return None


def llm_analyze_opportunity(item: dict) -> dict:
    """Analyze a signal using a free OpenRouter LLM.

    Enriches item with llm_score (0-100), llm_analysis (dict), llm_model.
    Falls back silently on any error.
    """
    key = _get_openrouter_key()
    if not key:
        item["llm_score"] = None
        item["llm_analysis"] = "No API key"
        return item

    title = item.get("title", "")
    text = item.get("text", "")[:500]
    source = item.get("source", "")

    prompt = f"""Rate this as a business opportunity for an AI automation agency.

Source: {source}
Title: {title}
Description: {text}

Score 0-100 on (be strict):
- PAIN (0-25): How acute/specific is the problem?
- MARKET (0-25): How many buyers have this problem?
- BUILD (0-25): Can agents solve this in <1 week?
- WTP (0-25): Would they pay $50-500/mo?

Output JSON ONLY (no markdown):
{{"score":N,"pain":"...","market":"...","build":"...","wtp":"...","verdict":"GO|MAYBE|PASS","industry":"one word"}}"""

    payload = {
        "model": OPENROUTER_FREE_MODELS[0],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.3,
    }

    try:
        req = urllib.request.Request(
            f"{OPENROUTER_BASE}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://aidentify.io",
                "X-Title": "AIdentify Scanner",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())

        content = result["choices"][0]["message"]["content"].strip()
        # Strip markdown fences
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        analysis = json.loads(content)
        item["llm_score"] = min(analysis.get("score", 0), 100)
        item["llm_analysis"] = analysis
        item["llm_model"] = OPENROUTER_FREE_MODELS[0]
    except Exception as e:
        item["llm_score"] = None
        item["llm_analysis"] = f"Error: {str(e)[:60]}"
    return item

def score_opportunity(item: dict) -> dict:
    """Score an opportunity from 0-100 based on multiple signals."""
    text = " ".join(str(item.get(k, "")) for k in ("title", "text", "tags" if "tags" in item else "")).lower()
    score = 0
    signals = []

    # Title-only text (for signals that rely on product naming)
    title = str(item.get("title", "")).lower()

    # Short-text boost: when body is thin, rely more on title signals
    body_len = len(text) - len(title)
    is_short_text = body_len < 100

    # Pain signal detection (0-25 points)
    pain_count = sum(1 for kw in PAIN_KEYWORDS if kw.lower() in text)
    pain_score = min(pain_count * 5, 25)
    score += pain_score
    if pain_count >= 2:
        signals.append(f"🔥 {pain_count} pain signals")

    # Product signal — title implies a built solution (0-25 points)
    PRODUCT_SIGNALS = [
        "built", "launched", "released", "open source", "oss",
        "app", "platform", "tool", "framework", "api",
        "agent", "bot", "automation", "saas", "dashboard",
        "alternative", "self-hosted", "gateway", "router",
    ]
    product_count = sum(1 for kw in PRODUCT_SIGNALS if kw in title)
    # For short-text items, product signals in title are very strong
    product_mult = 6 if is_short_text else 5
    product_score = min(product_count * product_mult, 25)
    score += product_score
    if product_count >= 2:
        signals.append(f"🚀 {product_count} product signals")
    elif product_count >= 1 and is_short_text:
        signals.append(f"🚀 {product_count} product signal (title)")

    # Opportunity keyword match (0-20 points)
    opp_count = sum(1 for kw in OPPORTUNITY_KEYWORDS if kw.lower() in text)
    opp_score = min(opp_count * 4, 20)
    score += opp_score
    if opp_count >= 2:
        signals.append(f"💡 {opp_count} opportunity keywords")

    # Industry match (0-15 points)
    matched_industries = []
    for industry, keywords in INDUSTRIES.items():
        if any(kw.lower() in text for kw in keywords):
            matched_industries.append(industry)
    industry_score = min(len(matched_industries) * 7, 15)
    score += industry_score
    if matched_industries:
        signals.append(f"🏭 Industries: {', '.join(matched_industries[:3])}")

    # Engagement signals (0-15 points) — strong signal of market demand
    engagement = 0
    if item.get("score", 0) > 20:
        engagement += 3
    if item.get("score", 0) > 50:
        engagement += 2
    if item.get("score", 0) > 100:
        engagement += 3
    if item.get("comments", 0) > 10:
        engagement += 3
    if item.get("comments", 0) > 50:
        engagement += 2
    if item.get("reactions", 0) > 5:
        engagement += 2
    engagement = min(engagement, 15)
    score += engagement
    if engagement >= 5:
        signals.append("📈 High engagement")

    # Source quality (0-10 points)
    source_quality = {
        "hackernews": 8,
        "github": 10,
        "devto": 6,
        "search": 4,
    }
    score += source_quality.get(item.get("source", ""), 3)

    item["opportunity_score"] = min(score, 100)
    item["signals"] = signals
    return item


# ---------------------------------------------------------------------------
# Briefing Generator
# ---------------------------------------------------------------------------

def generate_briefing(opportunities: list[dict]) -> str:
    """Generate a clean morning briefing from scored opportunities."""
    # Sort by score descending
    opportunities.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)

    # Filter to meaningful opportunities (score >= 20)
    top_opps = [o for o in opportunities if o.get("opportunity_score", 0) >= 20]
    if not top_opps:
        top_opps = opportunities[:5]  # Show top 5 even if low score

    # Limit to top 10
    top_opps = top_opps[:10]

    date_str = NOW.strftime("%A, %B %d, %Y")
    time_str = NOW.strftime("%I:%M %p IST")

    lines = [
        "🔭 **AIdentify — Business Opportunity Scanner**",
        f"📅 {date_str} — {time_str}",
        "",
        f"Scanned {len(opportunities)} signals → **{len(top_opps)} opportunities** found",
        "",
        "---",
        "",
    ]

    for i, opp in enumerate(top_opps, 1):
        score = opp.get("opportunity_score", 0)
        # Score emoji
        if score >= 60:
            score_icon = "🟢"
        elif score >= 40:
            score_icon = "🟡"
        else:
            score_icon = "🟠"

        title = opp.get("title", "Untitled")
        url = opp.get("url", "")
        source = opp.get("source", "unknown")
        source_icon = {
            "hackernews": "📰 HN",
            "github": "🐙 GitHub",
            "devto": "💻 dev.to",
            "search": "🔍 Web",
        }.get(source, f"📌 {source}")

        lines.append(f"**{i}. {score_icon} [{score}/100] {title}**")
        lines.append(f"   {source_icon}")

        if url:
            lines.append(f"   🔗 {url}")

        # Signals
        signals = opp.get("signals", [])
        if signals:
            lines.append(f"   {' | '.join(signals)}")

        # Snippet
        text = opp.get("text", "").strip()
        if text:
            # Truncate to ~150 chars
            snippet = text[:150] + "..." if len(text) > 150 else text
            lines.append(f"   > {snippet}")

        lines.append("")

    # Footer
    lines += [
        "---",
        "",
        "💡 **Next step:** Pick an opportunity and say `build [number]` to start the full pipeline.",
        "   Pipeline: SCOUT → DISCUSS → SELECT → BUILD → PUBLISH",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_scan(enable_llm: bool = False, enable_js: bool = False) -> tuple[list[dict], str]:
    """Run the full scan and return (opportunities, briefing_text).

    Args:
        enable_llm: If True, analyze top signals with OpenRouter free model.
        fast: If True, only scan 3 high-speed sources.
    """
    all_items: list[dict] = []

    # 1. Hacker News — Ask HN
    print("📰 Scanning Hacker News (Ask HN)...", file=sys.stderr)
    all_items.extend(fetch_hn_ask(limit=25))
    print("📰 Scanning Hacker News (Show HN)...", file=sys.stderr)
    all_items.extend(fetch_hn_show(limit=15))
    print("📰 Scanning HN Top...", file=sys.stderr)
    all_items.extend(fetch_hn_top(limit=20))
    print("💻 Scanning dev.to...", file=sys.stderr)
    all_items.extend(fetch_devto("automation", per_page=15))
    print("🐙 Scanning GitHub Trending...", file=sys.stderr)
    all_items.extend(fetch_github_trending(limit=15))
    print("🦞 Scanning Lobste.rs...", file=sys.stderr)
    all_items.extend(fetch_lobsters(limit=15))
    print("👽 Scanning Reddit...", file=sys.stderr)
    all_items.extend(fetch_reddit("startups", limit=20))
    all_items.extend(fetch_reddit("SaaS", limit=15))
    all_items.extend(fetch_reddit("sideproject", limit=15))

    # 8-9. JS-rendered sources (Chrome headless via CDP)
    if enable_js:
        print("🎩 Scanning Indie Hackers (Chrome)...", file=sys.stderr)
        try:
            from js_renderer import fetch_indiehackers_chrome, fetch_producthunt_chrome, fetch_reddit_chrome, stop_chrome
            # All three share one Chrome instance (started on first call)
            ih_items = fetch_indiehackers_chrome(limit=10)
            print(f"   Found {len(ih_items)} IH posts", file=sys.stderr)
            all_items.extend(ih_items)

            print("🚀 Scanning Product Hunt (Chrome)...", file=sys.stderr)
            ph_items = fetch_producthunt_chrome(limit=10)
            print(f"   Found {len(ph_items)} PH launches", file=sys.stderr)
            all_items.extend(ph_items)

            # Reddit via Chrome (fallback if urllib was blocked)
            print("👽 Scanning Reddit (Chrome)...", file=sys.stderr)
            rd_chrome = fetch_reddit_chrome("startups", limit=15)
            print(f"   Found {len(rd_chrome)} Reddit posts", file=sys.stderr)
            all_items.extend(rd_chrome)

            stop_chrome()
        except ImportError:
            print("JS", "js_renderer.py not available — skipping Chrome sources", file=sys.stderr)
        except Exception as e:
            print("JS", f"Chrome rendering failed: {str(e)[:80]}", file=sys.stderr)
            try:
                stop_chrome()
            except Exception:
                pass

    # 10. DuckDuckGo search
    print("🔍 Searching for AI automation opportunities...", file=sys.stderr)
    ddg_items = search_ddg("AI automation business ideas 2026", limit=10)
    print(f"   Found {len(ddg_items)} search results", file=sys.stderr)
    all_items.extend(ddg_items)

    # 11. AI Tool Discovery Sites
    print("🔬 Scanning AI tool sites...", file=sys.stderr)
    from tool_scanner import (
        fetch_futuretools_newest,
        fetch_appsumo_new, fetch_futurepedia_recent,
        analyze_tool,
    )
    tool_items = []
    tool_items.extend(fetch_futuretools_newest(limit=10))
    tool_items.extend(fetch_appsumo_new(limit=8))
    tool_items.extend(fetch_futurepedia_recent(limit=8))
    print(f"   Found {len(tool_items)} tools from discovery sites", file=sys.stderr)

    # Analyze each tool (score + feasibility)
    for item in tool_items:
        analyze_tool(item)
        # Boost score if AppSumo has ratings (real market validation)
        if item.get("reviews", 0) > 50 and item.get("rating", 0) >= 4.5:
            item["opportunity_score"] = min(item.get("opportunity_score", 30) + 10, 100)
            item["signals"].append(f"🔥 {item['reviews']} reviews @ {item['rating']}★")

    all_items.extend(tool_items)

    # Deduplicate by URL
    seen_urls: set[str] = set()
    deduped = []
    for item in all_items:
        url = item.get("url", "") or item.get("hn_url", "")
        source = item.get("source", "")
        # For listing-page sources, use title hash for dedup instead of URL
        if source in ("indiehackers", "producthunt", "reddit", "search"):
            dedup_key = f"{source}:{item.get('title', '')[:60]}"
        else:
            dedup_key = url
        if dedup_key and dedup_key in seen_urls:
            continue
        if dedup_key:
            seen_urls.add(dedup_key)
        deduped.append(item)
    all_items = deduped

    # Score everything
    print(f"\n🎯 Scoring {len(all_items)} items...", file=sys.stderr)
    for item in all_items:
        score_opportunity(item)

    # Optional: LLM analysis on top candidates
    if enable_llm:
        candidates = sorted(all_items, key=lambda x: x.get("opportunity_score", 0), reverse=True)[:10]
        print(f"\n🤖 LLM analysis on top {len(candidates)} candidates...", file=sys.stderr)
        for item in candidates:
            llm_analyze_opportunity(item)
            # Blend LLM score with rule-based score
            if item.get("llm_score") is not None:
                blended = int(item["opportunity_score"] * 0.5 + item["llm_score"] * 0.5)
                item["opportunity_score"] = min(blended, 100)
                item["signals"].append(f"🤖 LLM: {item['llm_score']}")

    # Generate briefing
    briefing = generate_briefing(all_items)

    return all_items, briefing


def main():
    args = sys.argv[1:]
    enable_llm = "--llm" in args
    enable_js = "--js" in args

    if "--json" in args:
        opportunities, _ = run_scan(enable_llm=enable_llm, enable_js=enable_js)
        print(json.dumps(opportunities, indent=2, ensure_ascii=False))
    elif "--quick" in args:
        opportunities, briefing = run_scan(enable_llm=enable_llm, enable_js=enable_js)
        opportunities.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)
        for i, opp in enumerate(opportunities[:5], 1):
            score = opp.get("opportunity_score", 0)
            title = opp.get("title", "Untitled")
            print(f"{i}. [{score}/100] {title}")
    else:
        _, briefing = run_scan(enable_llm=enable_llm, enable_js=enable_js)
        print(briefing)


if __name__ == "__main__":
    main()

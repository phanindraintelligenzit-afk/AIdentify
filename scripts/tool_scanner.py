"""Scanner agents for AI tool discovery sites.

Fetches trending/new tools from:
- FutureTools.io (4000+ tools with categories, upvotes)
- AppSumo (launch deals with ratings/reviews)
- Futurepedia.io (trending categories, recently added)

Each tool gets scored on our existing 0-100 scale and includes review mining.
You'll provide pre-generated images matching the tool name + dimensions.
"""
import re
import urllib.request
from html.parser import HTMLParser
from typing import Optional

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


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
        return re.sub(r"<[^>]+>", " ", html).strip()


def fetch_url(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _use_chrome(url: str) -> Optional[str]:
    """Fallback to Chrome rendering for JS-blocked sites."""
    try:
        from js_renderer import start_chrome, get_ws_url, cdp_send, stop_chrome
        import time
        start_chrome()
        ws = get_ws_url()
        cdp_send(ws, "Page.enable")
        cdp_send(ws, "Page.navigate", {"url": url})
        time.sleep(5)
        result = cdp_send(ws, "Runtime.evaluate", {
            "expression": "document.body.innerText",
            "returnByValue": True,
        })
        html = result["result"]["result"]["value"]
        stop_chrome()
        return html
    except Exception:
        return None


def _fetch_with_fallback(url: str, use_chrome: bool = True) -> str:
    """Fetch URL, fall back to Chrome if blocked."""
    html = fetch_url(url, timeout=20)
    if ("Just a moment" in html or len(html) < 3000) and use_chrome:
        chrome_html = _use_chrome(url)
        if chrome_html and len(chrome_html) > len(html):
            return chrome_html
    return html


# ─── FutureTools.io ───────────────────────────────────────────────────

def fetch_futuretools_newest(limit: int = 10) -> list[dict]:
    """Fetch newest tools from FutureTools.io."""
    try:
        html = _fetch_with_fallback("https://futuretools.io/")
    except Exception:
        return []

    results = []
    # Parse tool cards from inner text
    tool_links = re.findall(r'href="(/tools/[^"]*)"[^>]*>([^<]{10,150})</a>', html)
    for path, title in tool_links[:limit]:
        clean_title = strip_html(title)
        if len(clean_title) < 5:
            continue
        results.append({
            "source": "futuretools",
            "title": clean_title,
            "url": f"https://futuretools.io{path}",
            "category": "",
            "pricing": "",
            "text": f"AI tool on FutureTools: {clean_title}",
        })
    return results


# ─── AppSumo ──────────────────────────────────────────────────────────

def fetch_appsumo_new(limit: int = 10) -> list[dict]:
    """Fetch new AppSumo deals with ratings and reviews."""
    try:
        html = fetch_url("https://appsumo.com/", timeout=20)
    except Exception:
        return []

    results = []

    # Parse deal cards with title, description, rating, reviews
    deal_blocks = re.findall(
        r'<h3[^>]*>(.*?)</h3>.*?<p[^>]*class="[^"]*(?:description|tagline)[^"]*"[^>]*>(.*?)</p>.*?<span[^>]*class="[^"]*rating[^"]*"[^>]*>([\d.]+).*?<span[^>]*class="[^"]*review[^"]*"[^>]*>(\d+)',
        html, re.DOTALL,
    )

    if not deal_blocks:
        # Fallback: extract deal titles
        titles = re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)
        for raw_title in titles[:limit]:
            title = strip_html(raw_title)
            if len(title) < 5:
                continue
            results.append({
                "source": "appsumo",
                "title": title,
                "url": "https://appsumo.com",
                "text": f"AppSumo deal: {title}",
                "category": "appsumo-deal",
            })
    else:
        for raw_title, raw_desc, rating, reviews in deal_blocks[:limit]:
            title = strip_html(raw_title)
            desc = strip_html(raw_desc)
            if len(title) < 5:
                continue
            results.append({
                "source": "appsumo",
                "title": title,
                "url": "https://appsumo.com",
                "text": f"{title} ({rating}★, {reviews} reviews) — {desc}",
                "category": "appsumo-deal",
                "rating": float(rating),
                "reviews": int(reviews),
            })

    return results


# ─── Futurepedia ──────────────────────────────────────────────────────

def fetch_futurepedia_recent(limit: int = 10) -> list[dict]:
    """Fetch recently added tools from Futurepedia."""
    try:
        html = _fetch_with_fallback("https://www.futurepedia.io")
    except Exception:
        return []

    results = []
    tool_areas = re.findall(
        r'href="(/tools/[^"]*)"[^>]*>.*?<h[23][^>]*>(.*?)</h[23]>.*?>([^<]{20,300})<',
        html, re.DOTALL,
    )

    if not tool_areas:
        tool_links = re.findall(r'href="(/tools/[^"]*)"[^>]*>([^<]{10,120})</a>', html)
        for path, title in tool_links[:limit]:
            clean = strip_html(title)
            if len(clean) < 5:
                continue
            results.append({
                "source": "futurepedia",
                "title": clean,
                "url": f"https://www.futurepedia.io{path}",
                "text": f"Futurepedia: {clean}",
            })
    else:
        for path, title, snippet in tool_areas[:limit]:
            clean_title = strip_html(title)
            clean_snippet = strip_html(snippet)
            if len(clean_title) < 5:
                continue
            results.append({
                "source": "futurepedia",
                "title": clean_title,
                "url": f"https://www.futurepedia.io{path}",
                "text": f"{clean_title}: {clean_snippet}",
            })

    return results


# ─── Tool Analyzer ────────────────────────────────────────────────────

def analyze_tool(tool: dict) -> dict:
    """Analyze a tool from AI discovery sites.

    Scores the tool and assesses if we can replicate/enhance it with our agents.
    """
    title = tool.get("title", "").lower()
    text = tool.get("text", "").lower()

    score = 30  # Base for being on a curated site

    # Engagement signals
    reviews = tool.get("reviews", 0)
    rating = tool.get("rating", 0)
    if reviews > 100:
        score += 15
    elif reviews > 50:
        score += 10
    elif reviews > 10:
        score += 5

    if rating >= 4.5:
        score += 15
    elif rating >= 4.0:
        score += 10
    elif rating >= 3.5:
        score += 5

    # Category relevance
    ai_categories = [
        "automation", "agents", "productivity", "research",
        "marketing", "seo", "writing", "analytics", "video",
    ]
    if any(cat in text for cat in ai_categories):
        score += 10

    # Trending signals
    if any(w in title for w in ["ai", "agent", "automation", "gpt", "llm"]):
        score += 8

    tool["analysis_score"] = min(score, 100)
    tool["replication_feasibility"] = _assess_replication(text, title)
    tool["customer_sentiment"] = _extract_sentiment(text)

    return tool


def _assess_replication(text: str, title: str) -> str:
    """Assess if we can replicate this tool with our agent system."""
    easy_keywords = ["writing", "content", "email", "social", "research",
                      "summary", "blog", "seo", "calendar", "schedule"]
    if any(k in title or k in text for k in easy_keywords):
        return "HIGH — Can build with our content + research agents"

    medium_keywords = ["analytics", "automation", "lead", "crm",
                        "invoice", "workflow", "reporting"]
    if any(k in title or k in text for k in medium_keywords):
        return "MEDIUM — Requires integration work (API connections)"

    hard_keywords = ["image", "video", "3d", "code", "image gen",
                      "animation", "design", "music", "audio"]
    if any(k in title or k in text for k in hard_keywords):
        return "LOW — Specialized domain, needs significant development"

    return "MEDIUM — Feasible with multi-agent approach"


def _extract_sentiment(text: str) -> str:
    """Extract positive/negative sentiment signals."""
    positive_words = ["love", "amazing", "best", "great", "perfect", "easy",
                      "powerful", "save time", "recommend", "worth"]
    negative_words = ["expensive", "limited", "buggy", "slow", "complex",
                      "disappointed", "overpriced", "confusing"]

    pos_count = sum(1 for w in positive_words if w in text)
    neg_count = sum(1 for w in negative_words if w in text)

    if pos_count > neg_count + 2:
        return "POSITIVE — Strong customer satisfaction"
    elif pos_count > neg_count:
        return "MOSTLY POSITIVE — Some minor complaints"
    elif neg_count > pos_count:
        return "MIXED — Has notable pain points to solve"
    return "NEUTRAL — Not enough reviews to determine"

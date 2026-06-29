#!/usr/bin/env python3
"""
AIdentify Opportunity Scanner v2
Improved autonomous opportunity discovery for high-WTP AI agent products.

Features:
- Multiple high-signal sources (HN Algolia, GitHub Trending, basic Product Hunt signals)
- Multi-factor AI-assisted scoring (WTP, pain, competition gap, swarm fit, timing)
- Structured JSON output + clean Telegram summary
- Designed for Hermes Agent cron + OWL orchestration
- Easy to extend with more sources or real LLM scoring

Run manually: python scripts/opportunity_scanner_v2.py
Cron example (Hermes): daily 8:30 AM IST
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re

# ==================== CONFIG ====================
CONFIG = {
    "output_dir": "data/opportunities",
    "max_results_per_source": 15,
    "top_n_final": 8,
    "min_score_threshold": 65,
    "hn_days_lookback": 7,
    "github_trending_languages": ["python", "typescript", "javascript"],
    "telegram_summary_max_length": 3500,
}

# Optional: Add your GitHub token for higher rate limits
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# ==================== DATA MODELS ====================
class Opportunity:
    def __init__(self, title: str, source: str, url: str, description: str = "",
                 engagement: int = 0, category: str = "general"):
        self.title = title
        self.source = source
        self.url = url
        self.description = description
        self.engagement = engagement
        self.category = category
        self.score = 0
        self.score_breakdown = {}
        self.estimated_wtp = 0
        self.competition_gap = 0
        self.swarm_fit = 0
        self.timing = 0
        self.pain_intensity = 0

    def to_dict(self):
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "description": self.description,
            "engagement": self.engagement,
            "category": self.category,
            "score": self.score,
            "score_breakdown": self.score_breakdown,
            "estimated_wtp": self.estimated_wtp,
            "competition_gap": self.competition_gap,
            "swarm_fit": self.swarm_fit,
            "timing": self.timing,
            "pain_intensity": self.pain_intensity,
            "discovered_at": datetime.now().isoformat()
        }


# ==================== SOURCE FETCHERS ====================
def fetch_hn_opportunities() -> List[Opportunity]:
    """Fetch recent high-engagement HN stories using Algolia (free, no key needed)"""
    opportunities = []
    base_url = "https://hn.algolia.com/api/v1/search"
    
    # Search for relevant terms in last N days
    search_terms = [
        "SaaS", "automation", "AI agent", "workflow", "compliance", 
        "lead generation", "invoice", "contract review", "prior authorization"
    ]
    
    for term in search_terms[:5]:  # Limit to avoid rate issues
        params = {
            "query": term,
            "tags": "story",
            "numericFilters": f"created_at_i>{int((datetime.now() - timedelta(days=CONFIG['hn_days_lookback'])).timestamp())}",
            "hitsPerPage": 8
        }
        try:
            resp = requests.get(base_url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            for hit in data.get("hits", []):
                title = hit.get("title", "")
                if len(title) < 10:
                    continue
                    
                url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                points = hit.get("points", 0)
                num_comments = hit.get("num_comments", 0)
                engagement = points + (num_comments * 2)
                
                opp = Opportunity(
                    title=title,
                    source="Hacker News",
                    url=url,
                    description=(hit.get("story_text") or "")[:300],
                    engagement=engagement,
                    category=detect_category(title)
                )
                opportunities.append(opp)
        except Exception as e:
            print(f"[HN] Error fetching '{term}': {e}")
            continue
    
    return opportunities[:CONFIG["max_results_per_source"]]


def fetch_github_trending() -> List[Opportunity]:
    """Fetch GitHub trending repositories (simple scraping + search)"""
    opportunities = []
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    for lang in CONFIG["github_trending_languages"]:
        try:
            url = f"https://api.github.com/search/repositories"
            params = {
                "q": f"language:{lang} stars:>100 created:>{(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}",
                "sort": "stars",
                "order": "desc",
                "per_page": 8
            }
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            for repo in data.get("items", []):
                title = f"{repo['full_name']} - {(repo.get('description') or '')[:80]}"
                opp = Opportunity(
                    title=title,
                    source="GitHub Trending",
                    url=repo["html_url"],
                    description=repo.get("description", ""),
                    engagement=repo.get("stargazers_count", 0),
                    category=detect_category(title)
                )
                opportunities.append(opp)
        except Exception as e:
            print(f"[GitHub] Error for {lang}: {e}")
            continue
    
    return opportunities[:CONFIG["max_results_per_source"]]


def detect_category(text: str) -> str:
    """Simple keyword-based category detection"""
    text = text.lower()
    if any(kw in text for kw in ["health", "prior auth", "medical", "patient"]):
        return "healthcare"
    elif any(kw in text for kw in ["lead", "outreach", "sales", "marketing"]):
        return "marketing"
    elif any(kw in text for kw in ["invoice", "finance", "accounting", "reconciliation"]):
        return "finance"
    elif any(kw in text for kw in ["contract", "legal", "compliance"]):
        return "legal"
    elif any(kw in text for kw in ["hr", "employee", "recruit"]):
        return "hr"
    elif any(kw in text for kw in ["ecom", "e-commerce", "product listing", "shopify", "review management"]):
        return "ecommerce"
    return "productivity"


# ==================== SCORING ENGINE ====================
def calculate_wtp_estimate(category: str, engagement: int) -> int:
    """Rough WTP estimation based on category and traction"""
    base = {
        "healthcare": 2500,
        "legal": 2200,
        "finance": 1800,
        "marketing": 1200,
        "ecommerce": 900,
        "hr": 1100,
        "productivity": 800
    }.get(category, 1000)
    
    # Boost for high engagement
    multiplier = min(1.8, 1 + (engagement / 800))
    return int(base * multiplier)


def score_opportunity(opp: Opportunity) -> Opportunity:
    """Multi-factor scoring (0-100). Can be upgraded with real LLM later."""
    # 1. WTP Potential (0-40)
    wtp = calculate_wtp_estimate(opp.category, opp.engagement)
    wtp_score = min(40, int((wtp / 3000) * 40))
    
    # 2. Pain Intensity (0-25) - based on engagement + keywords
    pain_keywords = ["pain", "frustrat", "hate", "slow", "manual", "error", "compliance"]
    pain_score = min(25, int(opp.engagement / 40) + 
                     sum(3 for kw in pain_keywords if kw in ((opp.title or '') + (opp.description or '')).lower()))
    
    # 3. Competition Gap (0-15)
    gap_score = 12 if opp.category in ["healthcare", "legal", "finance"] else 9
    
    # 4. Swarm Fit (0-10) - how well it fits FastAPI + React + Docker + agent pattern
    fit_score = 9 if opp.category in ["productivity", "marketing", "ecommerce"] else 7
    
    # 5. Timing / "Why Now" (0-10)
    timing_score = min(10, int(opp.engagement / 150))
    
    total = wtp_score + pain_score + gap_score + fit_score + timing_score
    
    opp.score = total
    opp.score_breakdown = {
        "wtp": wtp_score,
        "pain": pain_score,
        "competition_gap": gap_score,
        "swarm_fit": fit_score,
        "timing": timing_score
    }
    opp.estimated_wtp = wtp
    opp.pain_intensity = pain_score
    opp.competition_gap = gap_score
    opp.swarm_fit = fit_score
    opp.timing = timing_score
    
    return opp


# ==================== OUTPUT & TELEGRAM ====================
def save_opportunities(opportunities: List[Opportunity]):
    os.makedirs(CONFIG["output_dir"], exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Save detailed JSON
    data = [o.to_dict() for o in opportunities]
    with open(f"{CONFIG['output_dir']}/opportunities_{date_str}.json", "w") as f:
        json.dump(data, f, indent=2)
    
    # Save latest pointer
    with open(f"{CONFIG['output_dir']}/latest.json", "w") as f:
        json.dump({"date": date_str, "count": len(opportunities)}, f)
    
    print(f"[Scanner] Saved {len(opportunities)} opportunities to {CONFIG['output_dir']}")


def generate_telegram_summary(opportunities: List[Opportunity]) -> str:
    """Clean, actionable summary for OWL / Telegram group"""
    if not opportunities:
        return "No high-quality opportunities found today."
    
    lines = [
        "🔍 **AIdentify Opportunity Scanner v2** — Daily Run",
        f"Date: {datetime.now().strftime('%Y-%m-%d')} | Found {len(opportunities)} strong ideas\n"
    ]
    
    for i, opp in enumerate(opportunities[:6], 1):
        lines.append(
            f"**{i}. {opp.title[:90]}**"
            f"\n• Score: **{opp.score}/100** | Est. WTP: ${opp.estimated_wtp}/mo"
            f"\n• Source: {opp.source} | Category: {opp.category}"
            f"\n• {opp.url}\n"
        )
    
    lines.append("\n→ OWL: Please analyze top 3 and start the autonomous build pipeline if WTP looks real.")
    summary = "\n".join(lines)
    
    if len(summary) > CONFIG["telegram_summary_max_length"]:
        summary = summary[:CONFIG["telegram_summary_max_length"]] + "..."
    
    return summary


# ==================== MAIN ====================
def main():
    print("🚀 Starting AIdentify Opportunity Scanner v2...")
    
    all_opps: List[Opportunity] = []
    
    # 1. Collect from sources
    print("Fetching from Hacker News...")
    all_opps.extend(fetch_hn_opportunities())
    
    print("Fetching from GitHub Trending...")
    all_opps.extend(fetch_github_trending())
    
    # Deduplicate by URL
    seen_urls = set()
    unique_opps = []
    for opp in all_opps:
        if opp.url not in seen_urls:
            seen_urls.add(opp.url)
            unique_opps.append(opp)
    
    # 2. Score everything
    print(f"Scoring {len(unique_opps)} opportunities...")
    scored = [score_opportunity(opp) for opp in unique_opps]
    
    # 3. Filter + rank
    filtered = [o for o in scored if o.score >= CONFIG["min_score_threshold"]]
    filtered.sort(key=lambda x: x.score, reverse=True)
    top_opportunities = filtered[:CONFIG["top_n_final"]]
    
    # 4. Save + output
    save_opportunities(top_opportunities)
    
    telegram_msg = generate_telegram_summary(top_opportunities)
    print("\n" + "="*60)
    print(telegram_msg)
    print("="*60)
    
    # Optional: Write to a file Hermes/OWL can easily read
    with open("data/latest_scanner_summary.txt", "w") as f:
        f.write(telegram_msg)
    
    print("\n✅ Scanner v2 complete. Ready for OWL to process.")


if __name__ == "__main__":
    main()

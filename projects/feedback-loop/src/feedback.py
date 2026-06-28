"""Feedback Loop — tracks project performance and adjusts scoring.

Weekly cron that:
1. Checks GitHub stats (stars, forks, clones, views) for all marketplace projects
2. Identifies which categories/types get traction
3. Adjusts scoring weights in opportunity_scanner.py
4. Generates a feedback report

This closes the loop: build → measure → learn → build better.
"""
import json
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

IST = timezone(timedelta(hours=5, minutes=30))

GITHUB_API = "https://api.github.com"
GITHUB_ORG = "phanindraintelligenzit-afk"

# Path to store feedback data
FEEDBACK_FILE = Path(__file__).resolve().parent / "feedback_data.json"
WEIGHTS_FILE = Path(__file__).resolve().parent / "scoring_weights.json"


def fetch_repo_stats(repo_name: str) -> Optional[dict]:
    """Fetch GitHub stats for a repository."""
    url = f"{GITHUB_API}/repos/{GITHUB_ORG}/{repo_name}"
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AIdentify-Feedback-Loop",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return {
                "name": repo_name,
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "watchers": data.get("subscribers_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "language": data.get("language", ""),
                "topics": data.get("topics", []),
            }
    except Exception as e:
        return {"name": repo_name, "error": str(e)[:60]}


def fetch_traffic_stats(repo_name: str) -> dict:
    """Fetch view/clone traffic stats (requires push access)."""
    url = f"{GITHUB_API}/repos/{GITHUB_ORG}/{repo_name}/traffic/views"
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AIdentify-Feedback-Loop",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return {
                "views": data.get("count", 0),
                "uniques": data.get("uniques", 0),
                "daily": data.get("views", [])[-7:] if data.get("views") else [],
            }
    except Exception:
        return {"views": 0, "uniques": 0, "daily": []}


def get_marketplace_projects() -> list[dict]:
    """Read projects from marketplace data."""
    # Navigate to AIdentify-marketplace/docs/data/projects.json
    # This file can be run from various locations
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "docs" / "data" / "projects.json",  # from projects/feedback-loop/src/
        Path(__file__).resolve().parent.parent.parent / "docs" / "data" / "projects.json",
        Path("C:/Users/Admin/Projects/AIdentify-marketplace/docs/data/projects.json"),
    ]
    for projects_file in candidates:
        if projects_file.exists():
            try:
                data = json.loads(projects_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data.get("projects", [])
                return data if isinstance(data, list) else []
            except Exception:
                continue
    return []


def analyze_performance(stats: list[dict]) -> dict:
    """Analyze which projects perform best."""
    if not stats:
        return {"message": "No stats collected"}

    # Sort by engagement score (stars + forks*2 + watchers)
    for s in stats:
        if "error" not in s:
            s["engagement_score"] = s.get("stars", 0) + s.get("forks", 0) * 2 + s.get("watchers", 0)

    valid = [s for s in stats if "error" not in s]
    valid.sort(key=lambda x: x.get("engagement_score", 0), reverse=True)

    # Category analysis
    categories = {}
    for s in valid:
        cat = s.get("language", "unknown")
        if cat not in categories:
            categories[cat] = {"count": 0, "total_stars": 0, "total_forks": 0}
        categories[cat]["count"] += 1
        categories[cat]["total_stars"] += s.get("stars", 0)
        categories[cat]["total_forks"] += s.get("forks", 0)

    return {
        "total_projects": len(stats),
        "successful_fetches": len(valid),
        "failed_fetches": len(stats) - len(valid),
        "top_performers": valid[:5],
        "needs_attention": [s for s in valid if s.get("stars", 0) == 0][-5:],
        "category_breakdown": categories,
        "total_stars": sum(s.get("stars", 0) for s in valid),
        "total_forks": sum(s.get("forks", 0) for s in valid),
    }


def adjust_scoring_weights(analysis: dict) -> dict:
    """Adjust opportunity scoring weights based on performance.

    If certain categories/languages get more traction, boost similar signals.
    If projects in a category consistently flop, reduce that category's weight.
    """
    weights = load_weights()
    categories = analysis.get("category_breakdown", {})

    # Boost categories with high engagement
    for cat, data in categories.items():
        avg_stars = data["total_stars"] / max(data["count"], 1)
        if avg_stars >= 5:
            weights["category_boosts"][cat] = min(weights["category_boosts"].get(cat, 1.0) + 0.2, 2.0)
        elif avg_stars == 0 and data["count"] >= 2:
            weights["category_boosts"][cat] = max(weights["category_boosts"].get(cat, 1.0) - 0.1, 0.5)

    # Save updated weights
    save_weights(weights)
    return weights


def load_weights() -> dict:
    """Load current scoring weights."""
    if WEIGHTS_FILE.exists():
        try:
            return json.loads(WEIGHTS_FILE.read_text())
        except Exception:
            pass
    return {
        "category_boosts": {},
        "last_updated": "",
        "history": [],
    }


def save_weights(weights: dict):
    """Save scoring weights."""
    weights["last_updated"] = datetime.now(IST).isoformat()
    WEIGHTS_FILE.write_text(json.dumps(weights, indent=2))


def save_feedback_data(stats: list[dict], analysis: dict):
    """Save feedback data for historical tracking."""
    data = {
        "timestamp": datetime.now(IST).isoformat(),
        "stats": stats,
        "analysis": analysis,
    }
    FEEDBACK_FILE.write_text(json.dumps(data, indent=2, default=str))


def generate_report(analysis: dict, weights: dict) -> str:
    """Generate a human-readable feedback report."""
    lines = [
        "📊 AIdentify Feedback Loop Report",
        f"📅 {datetime.now(IST).strftime('%A, %B %d, %Y — %I:%M %p IST')}",
        "",
        f"Total projects tracked: {analysis.get('total_projects', 0)}",
        f"Total stars: ⭐ {analysis.get('total_stars', 0)}",
        f"Total forks: 🔱 {analysis.get('total_forks', 0)}",
        "",
    ]

    # Top performers
    top = analysis.get("top_performers", [])
    if top:
        lines.append("🏆 Top Performers:")
        for i, proj in enumerate(top[:5], 1):
            lines.append(f"  {i}. {proj['name']} — ⭐{proj.get('stars', 0)} 🔱{proj.get('forks', 0)}")
        lines.append("")

    # Needs attention
    attention = analysis.get("needs_attention", [])
    if attention:
        lines.append("⚠️  Needs Attention (0 stars):")
        for proj in attention[:5]:
            lines.append(f"  • {proj['name']}")
        lines.append("")

    # Category breakdown
    cats = analysis.get("category_breakdown", {})
    if cats:
        lines.append("📁 Category Breakdown:")
        for cat, data in sorted(cats.items(), key=lambda x: x[1]["total_stars"], reverse=True):
            avg = data["total_stars"] / max(data["count"], 1)
            boost = weights.get("category_boosts", {}).get(cat, 1.0)
            lines.append(f"  {cat or 'unknown'}: {data['count']} projects, {data['total_stars']} stars (avg {avg:.1f}, boost {boost:.1f}x)")
        lines.append("")

    # Weight adjustments
    boosts = weights.get("category_boosts", {})
    if boosts:
        lines.append("⚖️  Current Scoring Boosts:")
        for cat, boost in sorted(boosts.items(), key=lambda x: x[1], reverse=True):
            indicator = "📈" if boost > 1.0 else "📉" if boost < 1.0 else "➡️"
            lines.append(f"  {indicator} {cat}: {boost:.1f}x")

    return "\n".join(lines)


def run_feedback_loop() -> str:
    """Run the full feedback loop. Returns report text."""
    print("🔄 Starting feedback loop...")

    # 1. Get all marketplace projects
    projects = get_marketplace_projects()
    print(f"  Found {len(projects)} marketplace projects")

    # 2. Fetch GitHub stats for each
    stats = []
    for project in projects:
        # Extract repo name from github_url
        github_url = project.get("github_url", "")
        if not github_url:
            continue
        # Parse owner/repo from URL
        parts = github_url.rstrip("/").split("/")
        if len(parts) >= 2:
            slug = parts[-1]
        else:
            continue
        
        stat = fetch_repo_stats(slug)
        if stat:
            stat["marketplace_name"] = project.get("name", slug)
            stat["category"] = project.get("category", "")
            stats.append(stat)
        print(f"  📦 {slug}: ⭐{stat.get('stars', '?')} (error: {stat.get('error', 'none')[:30]})")

    # 3. Analyze performance
    analysis = analyze_performance(stats)

    # 4. Adjust scoring weights
    weights = adjust_scoring_weights(analysis)

    # 5. Save data
    save_feedback_data(stats, analysis)

    # 6. Generate report
    report = generate_report(analysis, weights)
    print(f"\n{report}")
    return report


if __name__ == "__main__":
    report = run_feedback_loop()

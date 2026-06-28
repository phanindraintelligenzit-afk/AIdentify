"""Trend Researcher Agent — finds video ideas based on niche analysis.

Uses keyword patterns, trending signals, and content gap analysis.
In production, connects to YouTube Data API v3 and Google Trends.
"""
import re
from src.models import VideoIdea

# Content gap patterns — what viewers search for but don't find enough of
CONTENT_GAP_PATTERNS = [
    "how to", "tutorial", "guide", "explained", "review",
    "vs", "comparison", "best", "top", "why", "what is",
    "tips", "mistakes", "beginner", "advanced", "2026"
]

# High-engagement formats
FORMATS = [
    "how-to tutorial",
    "listicle (top N)",
    "comparison / vs",
    "my honest review",
    "explainer / deep dive",
    "challenge / experiment",
    "behind the scenes",
    "reaction / commentary",
    "case study / results",
    "prediction / forecast",
]


def research_niche(niche: str, competitor_titles: list[str] = None) -> list[VideoIdea]:
    """Generate video ideas for a niche.

    Args:
        niche: The channel's topic (e.g., "AI tools", "fitness", "coding")
        competitor_titles: Optional list of competitor video titles for gap analysis
    """
    ideas = []
    base_topics = _expand_niche(niche)

    for i, topic in enumerate(base_topics):
        format_type = FORMATS[i % len(FORMATS)]
        idea = _generate_idea(niche, topic, format_type, i)
        ideas.append(idea)

    # Sort by trending score
    ideas.sort(key=lambda x: x.trending_score, reverse=True)
    return ideas


def _expand_niche(niche: str) -> list[str]:
    """Expand a niche into specific subtopics."""
    templates = [
        f"{niche} for beginners in 2026",
        f"best {niche} tools you're not using",
        f"common {niche} mistakes and how to fix them",
        f"how I use {niche} to [achieve result]",
        f"{niche} vs traditional methods — results",
        f"the truth about {niche} nobody talks about",
        f"my top 5 {niche} recommendations",
        f"how to get started with {niche}",
        f"advanced {niche} techniques",
        f"{niche} trends and predictions",
    ]
    return templates


def _generate_idea(niche: str, topic: str, format_type: str, index: int) -> VideoIdea:
    """Generate a single video idea with scoring."""
    # Calculate trending score based on keyword signals
    score = 50.0  # Base
    topic_lower = topic.lower()

    # Boost for high-engagement keywords
    boost_keywords = ["2026", "best", "how to", "mistakes", "truth", "top", "vs"]
    for kw in boost_keywords:
        if kw in topic_lower:
            score += 8

    # Boost for urgency/timeliness
    if any(w in topic_lower for w in ["now", "today", "2026", "new", "latest"]):
        score += 10

    # Slight randomization for variety (deterministic based on index)
    score += (index * 3) % 15
    score = min(score, 95)

    # Determine search volume / competition
    if score > 70:
        volume = "high"
        competition = "high"
    elif score > 50:
        volume = "medium"
        competition = "medium"
    else:
        volume = "low"
        competition = "low"

    return VideoIdea(
        title=topic.title(),
        niche=niche,
        search_volume=volume,
        competition=competition,
        trending_score=round(score, 1),
        description=f"A {format_type} video about {topic.lower()}",
        target_audience=f"People interested in {niche}",
        estimated_views=_estimate_views(score),
    )


def _estimate_views(score: float) -> str:
    """Rough view estimate based on trending score."""
    if score > 80:
        return "10K-100K"
    elif score > 60:
        return "5K-50K"
    elif score > 40:
        return "1K-10K"
    else:
        return "500-5K"


def find_content_gaps(competitor_titles: list[str], niche: str) -> list[str]:
    """Find topics competitors haven't covered well.

    Analyzes competitor titles for missing angles.
    """
    gaps = []
    covered_topics = set()

    for title in competitor_titles:
        words = set(title.lower().split())
        covered_topics.update(words)

    # Check which gap patterns are underrepresented
    for pattern in CONTENT_GAP_PATTERNS:
        if pattern not in covered_topics:
            gaps.append(f"{pattern} {niche}")

    return gaps[:10]


if __name__ == "__main__":
    ideas = research_niche("AI automation tools")
    for idea in ideas[:5]:
        print(f"  [{idea.trending_score:.0f}/100] {idea.title}")
        print(f"     Volume: {idea.search_volume} | Competition: {idea.competition}")
        print(f"     Est: {idea.estimated_views}")
        print()

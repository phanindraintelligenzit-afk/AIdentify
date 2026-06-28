"""Tests for Trend Researcher agent."""
from src.agents.trend_researcher import research_niche, find_content_gaps


def test_research_niche_returns_ideas():
    ideas = research_niche("AI tools")
    assert len(ideas) > 0
    assert all(isinstance(i.title, str) for i in ideas)
    assert all(len(i.title) > 0 for i in ideas)


def test_research_niche_scoring():
    ideas = research_niche("coding")
    # Should be sorted by trending score (descending)
    scores = [i.trending_score for i in ideas]
    assert scores == sorted(scores, reverse=True)


def test_research_niche_fields_populated():
    ideas = research_niche("fitness")
    for idea in ideas:
        assert idea.niche == "fitness"
        assert idea.search_volume in ("high", "medium", "low")
        assert idea.competition in ("high", "medium", "low")
        assert 0 <= idea.trending_score <= 100
        assert len(idea.description) > 0


def test_find_content_gaps():
    competitors = [
        "How to use AI tools",
        "Best AI tools 2026",
        "AI tools review",
    ]
    gaps = find_content_gaps(competitors, "AI tools")
    assert len(gaps) > 0
    # Should find topics NOT in competitor titles
    assert any("mistake" in g.lower() or "tutorial" in g.lower() for g in gaps)

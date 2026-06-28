"""Tests for SEO Agent."""
from src.models import VideoIdea, Script
from src.agents.seo_agent import generate_seo, generate_thumbnail_brief
from src.agents.script_writer import write_script


def _make_idea() -> VideoIdea:
    return VideoIdea(
        title="AI Tools for Beginners",
        niche="AI tools",
        search_volume="high",
        competition="medium",
        trending_score=75,
        description="Tutorial",
        target_audience="Beginners",
        estimated_views="10K-50K",
    )


def test_generate_seo_returns_5_titles():
    seo = generate_seo(_make_idea(), None)
    assert len(seo.titles) == 5


def test_generate_seo_description_has_timestamps():
    script = write_script(_make_idea())
    seo = generate_seo(_make_idea(), script)
    assert "TIMESTAMPS" in seo.description or "timestamp" in seo.description.lower()


def test_generate_seo_tags():
    seo = generate_seo(_make_idea(), None)
    assert len(seo.tags) >= 10
    # Should include niche-related tags
    assert any("ai" in t.lower() for t in seo.tags)


def test_generate_seo_hashtags():
    seo = generate_seo(_make_idea(), None)
    assert len(seo.hashtags) >= 3
    assert all(h.startswith("#") for h in seo.hashtags)


def test_generate_thumbnail_brief():
    script = write_script(_make_idea())
    brief = generate_thumbnail_brief(_make_idea(), script)
    assert len(brief.main_text) > 0
    assert len(brief.concept) > 20
    assert len(brief.composition) > 20
    # Thumbnail text should be short (3-5 words)
    assert len(brief.main_text.split()) <= 6

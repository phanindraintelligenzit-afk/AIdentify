"""Tests for Script Writer agent."""
from src.models import VideoIdea
from src.agents.script_writer import write_script


def _make_idea() -> VideoIdea:
    return VideoIdea(
        title="AI Tools for Beginners",
        niche="AI tools",
        search_volume="high",
        competition="medium",
        trending_score=75,
        description="Tutorial on AI tools",
        target_audience="Beginners",
        estimated_views="10K-50K",
    )


def test_write_script_structure():
    script = write_script(_make_idea())
    assert len(script.video_id) > 0
    assert len(script.hook) > 20
    assert len(script.intro) > 20
    assert len(script.body) >= 3
    assert len(script.cta) > 10
    assert len(script.outro) > 10


def test_write_script_timestamps():
    script = write_script(_make_idea(), duration_minutes=9)
    timestamps = [s["timestamp"] for s in script.body]
    # Should have sequential timestamps
    assert "0:00" in timestamps[0]
    assert len(timestamps) >= 3


def test_write_script_sections_have_content():
    script = write_script(_make_idea())
    for section in script.body:
        assert "timestamp" in section
        assert "content" in section
        assert "visual" in section
        assert len(section["content"]) > 10


def test_write_script_styles():
    """Different styles should produce different hooks."""
    edu = write_script(_make_idea(), style="educational")
    ent = write_script(_make_idea(), style="entertainment")
    rev = write_script(_make_idea(), style="review")
    # Hooks should differ by style
    assert edu.hook != ent.hook
    assert edu.hook != rev.hook


def test_write_script_cta_has_subscribe():
    script = write_script(_make_idea())
    assert "subscribe" in script.cta.lower() or "like" in script.cta.lower() or "comment" in script.cta.lower()

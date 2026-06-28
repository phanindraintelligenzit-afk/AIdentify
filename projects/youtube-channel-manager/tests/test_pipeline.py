"""Tests for the full content engine pipeline."""
from src.pipeline import run_content_engine, quick_ideas


def test_run_content_engine():
    result = run_content_engine(
        niche="AI automation",
        duration_minutes=8,
        style="educational",
        num_videos=3,
    )
    assert result["niche"] == "AI automation"
    assert len(result["ideas"]) == 3
    assert len(result["scripts"]) == 3
    assert len(result["seo"]) == 3
    assert len(result["thumbnails"]) == 3
    assert "calendar" in result


def test_run_content_engine_ideas_have_scores():
    result = run_content_engine("coding", num_videos=3)
    for idea in result["ideas"]:
        assert "trending_score" in idea
        assert idea["trending_score"] > 0


def test_run_content_engine_scripts_have_hooks():
    result = run_content_engine("fitness", num_videos=2)
    for script in result["scripts"]:
        assert len(script["hook"]) > 20
        assert len(script["body"]) >= 3


def test_run_content_engine_seo_has_titles():
    result = run_content_engine("cooking", num_videos=2)
    for seo in result["seo"]:
        assert len(seo["titles"]) == 5
        assert len(seo["tags"]) >= 10


def test_quick_ideas():
    ideas = quick_ideas("productivity", count=5)
    assert len(ideas) == 5
    assert all("title" in i for i in ideas)

"""Tests for Content Calendar agent."""
from src.models import VideoIdea
from src.agents.content_calendar import create_weekly_plan, generate_content_calendar


def _make_ideas(count: int = 5) -> list[VideoIdea]:
    return [
        VideoIdea(
            title=f"Video idea {i}",
            niche="AI tools",
            search_volume="medium",
            competition="medium",
            trending_score=60 + i,
            description=f"Test video {i}",
            target_audience="Creators",
            estimated_views="5K-10K",
        )
        for i in range(count)
    ]


def test_create_weekly_plan():
    plan = create_weekly_plan("AI tools", _make_ideas())
    assert plan.niche == "AI tools"
    assert len(plan.videos) == 5
    assert len(plan.posting_schedule) == 5
    assert len(plan.content_pillars) >= 3


def test_weekly_plan_has_dates():
    plan = create_weekly_plan("AI tools", _make_ideas())
    for item in plan.posting_schedule:
        assert len(item.date) > 0
        assert item.status == "idea"


def test_weekly_plan_pillars():
    plan = create_weekly_plan("AI tools", _make_ideas())
    assert len(plan.content_pillars) >= 3
    assert len(plan.content_pillars) <= 5


def test_generate_content_calendar():
    plan = create_weekly_plan("AI tools", _make_ideas())
    calendar = generate_content_calendar(plan)
    assert "CONTENT CALENDAR" in calendar
    assert "AI" in calendar or "Ai" in calendar  # title() capitalizes first letter only
    assert "PRODUCTION CHECKLIST" in calendar

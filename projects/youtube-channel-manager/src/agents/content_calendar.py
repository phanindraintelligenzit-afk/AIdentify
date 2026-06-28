"""Content Calendar Agent — schedules and manages weekly content plans."""
from datetime import datetime, timedelta
from src.models import VideoIdea, Script, SEOPackage, ContentCalendarItem, WeeklyPlan


# Optimal posting days (generally Tue-Fri for most niches)
BEST_POST_DAYS = ["Tuesday", "Wednesday", "Thursday", "Friday"]

# Optimal posting times (IST — adjust per audience timezone)
BEST_POST_TIMES = {
    "Tuesday": "10:00 AM",
    "Wednesday": "11:00 AM",
    "Thursday": "10:00 AM",
    "Friday": "9:00 AM",
}


def create_weekly_plan(
    niche: str,
    ideas: list[VideoIdea],
    scripts: list[Script] = None,
    seo_packages: list[SEOPackage] = None,
    start_date: str = None,
) -> WeeklyPlan:
    """Create a full weekly content plan.

    Args:
        niche: Channel niche
        ideas: List of video ideas (from Trend Researcher)
        scripts: Optional pre-written scripts
        seo_packages: Optional pre-generated SEO
        start_date: Start date (YYYY-MM-DD), defaults to next Monday
    """
    if not start_date:
        start_date = _next_monday()

    # Pick top 5 ideas for the week
    top_ideas = ideas[:5]

    # Create content pillars (3-5 themes)
    pillars = _extract_pillars(top_ideas, niche)

    # Build schedule
    schedule = []
    videos = []

    for i, idea in enumerate(top_ideas):
        day_offset = i if i < 4 else 4  # Mon-Fri
        post_date = _add_days(start_date, day_offset)
        day_name = BEST_POST_DAYS[i % len(BEST_POST_DAYS)]
        post_time = BEST_POST_TIMES.get(day_name, "10:00 AM")

        video_id = f"vid_{i+1}_{idea.title[:20].lower().replace(' ', '_')}"

        item = ContentCalendarItem(
            date=f"{post_date} {post_time}",
            video_id=video_id,
            title=idea.title,
            status="idea",
            platform="youtube",
            notes=f"Search volume: {idea.search_volume} | Competition: {idea.competition}",
        )
        schedule.append(item)

        video_entry = {
            "video_id": video_id,
            "idea": idea.model_dump(),
            "script": scripts[i].model_dump() if scripts and i < len(scripts) else None,
            "seo": seo_packages[i].model_dump() if seo_packages and i < len(seo_packages) else None,
            "scheduled": f"{post_date} {post_time}",
        }
        videos.append(video_entry)

    return WeeklyPlan(
        niche=niche,
        week_start=start_date,
        videos=videos,
        posting_schedule=schedule,
        content_pillars=pillars,
    )


def _extract_pillars(ideas: list[VideoIdea], niche: str) -> list[str]:
    """Extract 3-5 content pillars from the week's ideas."""
    pillars = set()
    for idea in ideas:
        title_lower = idea.title.lower()
        if "beginner" in title_lower or "start" in title_lower:
            pillars.add("Beginner Basics")
        if "tool" in title_lower or "best" in title_lower:
            pillars.add("Tool Reviews")
        if "mistake" in title_lower or "wrong" in title_lower:
            pillars.add("Common Mistakes")
        if "advanced" in title_lower or "technique" in title_lower:
            pillars.add("Advanced Strategies")
        if "trend" in title_lower or "2026" in title_lower:
            pillars.add("Industry Trends")

    # Ensure at least 3 pillars
    while len(pillars) < 3:
        defaults = [f"{niche} Tips", f"{niche} Case Studies", f"{niche} News"]
        for d in defaults:
            if len(pillars) >= 3:
                break
            pillars.add(d)

    return list(pillars)[:5]


def _next_monday() -> str:
    """Get the date of next Monday."""
    today = datetime.now()
    days_ahead = 7 - today.weekday()  # Monday is 0
    if days_ahead <= 0:
        days_ahead += 7
    next_monday = today + timedelta(days=days_ahead)
    return next_monday.strftime("%Y-%m-%d")


def _add_days(date_str: str, days: int) -> str:
    """Add days to a date string."""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return (d + timedelta(days=days)).strftime("%Y-%m-%d")


def generate_content_calendar(weekly_plan: WeeklyPlan) -> str:
    """Generate a human-readable content calendar."""
    lines = [
        f"📅 CONTENT CALENDAR — {weekly_plan.niche.title()}",
        f"Week of {weekly_plan.week_start}",
        "",
        f"Content Pillars: {', '.join(weekly_plan.content_pillars)}",
        "",
        "─" * 50,
    ]

    for item in weekly_plan.posting_schedule:
        lines.append(f"\n🎬 {item.date}")
        lines.append(f"   Title: {item.title}")
        lines.append(f"   Status: {item.status}")
        if item.notes:
            lines.append(f"   Notes: {item.notes}")
        lines.append(f"   Platform: {item.platform}")

    lines.extend([
        "",
        "─" * 50,
        "",
        "📋 PRODUCTION CHECKLIST:",
        "  ☐ Script written",
        "  ☐ Filming complete",
        "  ☐ Editing complete",
        "  ☐ Thumbnail created",
        "  ☐ SEO metadata added",
        "  ☐ Scheduled for publish",
        "  ☐ Community post / shorts clipped",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    from src.models import VideoIdea
    ideas = [
        VideoIdea(title=f"Video {i}", niche="AI tools", search_volume="medium",
                  competition="medium", trending_score=60+i, description="Test",
                  target_audience="Creators", estimated_views="5K-10K")
        for i in range(5)
    ]
    plan = create_weekly_plan("AI tools", ideas)
    print(generate_content_calendar(plan))

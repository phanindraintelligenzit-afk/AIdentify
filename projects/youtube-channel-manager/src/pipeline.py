"""YouTube Channel Manager — full content engine pipeline.

Takes a niche and produces a complete weekly content plan:
  Trend Research → Script Writing → SEO → Thumbnail Briefs → Calendar
"""
from src.models import VideoIdea, Script, SEOPackage, WeeklyPlan
from src.agents.trend_researcher import research_niche
from src.agents.script_writer import write_script
from src.agents.seo_agent import generate_seo, generate_thumbnail_brief
from src.agents.content_calendar import create_weekly_plan, generate_content_calendar


def run_content_engine(
    niche: str,
    duration_minutes: int = 8,
    style: str = "educational",
    num_videos: int = 5,
) -> dict:
    """Run the full content engine for a niche.

    Args:
        niche: Channel topic (e.g., "AI tools", "fitness", "coding")
        duration_minutes: Target video length
        style: Video style (educational, entertainment, review, vlog)
        num_videos: Number of videos to plan (default 5 for a week)

    Returns:
        Complete weekly plan with ideas, scripts, SEO, and calendar
    """
    # Step 1: Research trending ideas
    print(f"🔍 Researching niche: {niche}...")
    ideas = research_niche(niche)
    top_ideas = ideas[:num_videos]
    print(f"   Generated {len(top_ideas)} video ideas")

    # Step 2: Write scripts for each idea
    print(f"✍️  Writing scripts ({style} style, {duration_minutes}min)...")
    scripts = []
    for idea in top_ideas:
        script = write_script(idea, duration_minutes=duration_minutes, style=style)
        scripts.append(script)
    print(f"   Wrote {len(scripts)} scripts")

    # Step 3: Generate SEO packages
    print(f"🏷️  Generating SEO metadata...")
    seo_packages = []
    for idea, script in zip(top_ideas, scripts):
        seo = generate_seo(idea, script)
        seo_packages.append(seo)
    print(f"   Generated {len(seo_packages)} SEO packages")

    # Step 4: Generate thumbnail briefs
    print(f"🖼  Creating thumbnail briefs...")
    thumbnail_briefs = []
    for idea, script in zip(top_ideas, scripts):
        brief = generate_thumbnail_brief(idea, script)
        thumbnail_briefs.append(brief)
    print(f"   Created {len(thumbnail_briefs)} thumbnail briefs")

    # Step 5: Build weekly calendar
    print(f"📅 Building content calendar...")
    weekly_plan = create_weekly_plan(
        niche=niche,
        ideas=top_ideas,
        scripts=scripts,
        seo_packages=seo_packages,
    )
    print(f"   Calendar ready: {len(weekly_plan.posting_schedule)} videos scheduled")

    return {
        "niche": niche,
        "ideas": [i.model_dump() for i in top_ideas],
        "scripts": [s.model_dump() for s in scripts],
        "seo": [s.model_dump() for s in seo_packages],
        "thumbnails": [t.model_dump() for t in thumbnail_briefs],
        "calendar": generate_content_calendar(weekly_plan),
        "weekly_plan": weekly_plan.model_dump(),
    }


def quick_ideas(niche: str, count: int = 10) -> list[dict]:
    """Quick video idea generation (no full pipeline)."""
    ideas = research_niche(niche)
    return [i.model_dump() for i in ideas[:count]]


if __name__ == "__main__":
    import json

    print("=" * 60)
    print("  YouTube Channel Manager — Content Engine")
    print("=" * 60)
    print()

    result = run_content_engine(
        niche="AI automation tools",
        duration_minutes=8,
        style="educational",
        num_videos=3,
    )

    print()
    print("=" * 60)
    print("  RESULTS")
    print("=" * 60)

    print("\n🎬 VIDEO IDEAS:")
    for i, idea in enumerate(result["ideas"], 1):
        print(f"  {i}. [{idea['trending_score']:.0f}/100] {idea['title']}")
        print(f"     Volume: {idea['search_volume']} | Est: {idea['estimated_views']}")

    print(f"\n{result['calendar']}")

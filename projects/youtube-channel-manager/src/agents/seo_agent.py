"""SEO Agent — generates titles, descriptions, tags, and thumbnail briefs."""
import re
from typing import Optional
from src.models import VideoIdea, Script, SEOPackage, ThumbnailBrief


def generate_seo(idea: VideoIdea, script: Script) -> SEOPackage:
    """Generate complete SEO package for a video."""
    titles = _generate_titles(idea, script)
    description = _generate_description(idea, script)
    tags = _generate_tags(idea)
    hashtags = _generate_hashtags(idea)
    thumbnail_text = _generate_thumbnail_text(idea, titles[0])

    return SEOPackage(
        titles=titles,
        description=description,
        tags=tags,
        hashtags=hashtags,
        thumbnail_text=thumbnail_text,
    )


def generate_thumbnail_brief(idea: VideoIdea, script: Script,
                              style: str = "clickable") -> ThumbnailBrief:
    """Generate a visual brief for thumbnail creation."""
    return ThumbnailBrief(
        concept=_thumbnail_concept(idea),
        main_text=_thumbnail_text(idea),
        background=_thumbnail_background(idea),
        subject=_thumbnail_subject(idea),
        emotion=_thumbnail_emotion(idea),
        composition=_thumbnail_composition(style),
        reference_style=_thumbnail_reference(idea),
    )


def _generate_titles(idea: VideoIdea, script: Script) -> list[str]:
    """Generate 5 title options using proven YouTube formulas."""
    niche = idea.niche.lower()
    title_base = idea.title

    formulas = [
        # How-to formula
        f"How to Use {idea.niche} (Step-by-Step Tutorial 2026)",
        # Curiosity gap
        f"The {niche} Secret Nobody Talks About",
        # Numbered list
        f"5 {niche} Tools That Changed Everything for Me",
        # Direct benefit
        f"Master {niche} in 2026 — Complete Guide",
        # Controversy / hot take
        f"Stop Using {niche} Wrong (Here's the Right Way)",
    ]

    return formulas


def _generate_description(idea: VideoIdea, script: Optional[Script] = None) -> str:
    """Generate SEO-optimized video description."""
    lines = [
        f"In this video, we cover {idea.title.lower()}.",
        "",
        f"Whether you're new to {idea.niche.lower()} or looking to level up, "
        f"this guide breaks down everything you need to know.",
    ]

    if script and script.body:
        lines.extend(["", "⏱ TIMESTAMPS:"])
        for section in script.body:
            lines.append(f"  {section['timestamp']} — {section['title']}")
    else:
        lines.append("")

    lines.extend([
        "",
        "🔗 LINKS MENTIONED:",
        "  [Tool 1 link]",
        "  [Tool 2 link]",
        "  [Resource link]",
        "",
        "📱 FOLLOW ME:",
        "  Twitter: @yourhandle",
        "  Instagram: @yourhandle",
        "  Website: https://yoursite.com",
        "",
        f"#{idea.niche.replace(' ', '')} #YouTube #Tutorial #2026",
    ])

    return "\n".join(lines)


def _generate_tags(idea: VideoIdea) -> list[str]:
    """Generate relevant tags."""
    niche = idea.niche.lower()
    base_tags = [
        niche,
        f"{niche} tutorial",
        f"{niche} guide",
        f"{niche} 2026",
        f"best {niche}",
        f"how to {niche}",
        f"{niche} for beginners",
        f"{niche} tips",
        f"{niche} review",
        f"{niche} tools",
        "tutorial",
        "guide",
        "2026",
        "how to",
        "tips and tricks",
    ]
    return base_tags[:20]


def _generate_hashtags(idea: VideoIdea) -> list[str]:
    """Generate hashtags for description/social."""
    niche_tag = idea.nickname.replace(" ", "").replace("-", "") if hasattr(idea, 'nickname') else idea.niche.replace(" ", "")
    return [
        f"#{niche_tag}",
        f"#{niche_tag}Tutorial",
        f"#{niche_tag}2026",
        "#YouTubeCreator",
        "#ContentCreator",
        "#VideoTutorial",
    ]


def _generate_thumbnail_text(idea: VideoIdea, best_title: str) -> str:
    """Generate short text overlay for thumbnail (3-5 words max)."""
    # Extract the most compelling part
    if "how to" in best_title.lower():
        return idea.niche.title() + " Guide"
    elif "2026" in best_title:
        return "2026 Guide"
    elif "best" in best_title.lower() or "top" in best_title.lower():
        return "Top Picks"
    elif "secret" in best_title.lower() or "wrong" in best_title.lower():
        return "Do This"
    else:
        return idea.niche.title()


def _thumbnail_concept(idea: VideoIdea) -> str:
    """Describe the thumbnail concept."""
    return (
        f"High-contrast thumbnail showing the result/benefit of {idea.niche.lower()}. "
        f"Face or subject showing emotion (surprise, excitement, or curiosity). "
        f"Bold text overlay. Clean background."
    )


def _thumbnail_text(idea: VideoIdea) -> str:
    """Short text for thumbnail overlay."""
    return _generate_thumbnail_text(idea, idea.title)


def _thumbnail_background(idea: VideoIdea) -> str:
    """Suggest background colors/style."""
    return (
        "Bright, saturated background (yellow, orange, or electric blue). "
        "High contrast with subject. Subtle gradient or solid color. "
        "No clutter — keep focus on subject and text."
    )


def _thumbnail_subject(idea: VideoIdea) -> str:
    """What/who to show in thumbnail."""
    return (
        "Creator's face showing strong emotion (shock, excitement, or determination). "
        "OR a clean product/tool screenshot with a reaction element. "
        "Rule of thirds: subject on left 2/3, text on right 1/3."
    )


def _thumbnail_emotion(idea: VideoIdea) -> str:
    """What feeling to evoke."""
    return (
        "Curiosity + urgency. The viewer should feel like they're missing out "
        "if they don't click. Use facial expression and bold colors to create "
        "FOMO (fear of missing out)."
    )


def _thumbnail_composition(style: str) -> str:
    """Layout description."""
    compositions = {
        "clickable": (
            "Subject face on left (60% width), bold text on right (40%). "
            "Text: 3-5 words max, sans-serif bold font, white with black outline. "
            "Arrow or circle highlighting key element."
        ),
        "minimal": (
            "Clean background, single focal point, small text bottom-third. "
            "Professional, editorial feel."
        ),
        "comparison": (
            "Split screen: before/left vs after/right. "
            "VS in the middle. Clear visual contrast between sides."
        ),
    }
    return compositions.get(style, compositions["clickable"])


def _thumbnail_reference(idea: VideoIdea) -> str:
    """Reference style."""
    return (
        "Style reference: MrBeast (high energy, bold text, bright colors) "
        "meets MKBHD (clean, professional, product-focused). "
        "Adapt to your niche — educational channels should lean cleaner, "
        "entertainment channels can be more chaotic."
    )


if __name__ == "__main__":
    from src.models import VideoIdea
    idea = VideoIdea(
        title="AI Automation Tools for Beginners",
        niche="AI automation",
        search_volume="high",
        competition="medium",
        trending_score=75,
        description="Tutorial",
        target_audience="Beginners",
        estimated_views="10K-50K",
    )
    seo = generate_seo(idea, None)
    print("TITLES:")
    for t in seo.titles:
        print(f"  • {t}")
    print(f"\nTAGS: {', '.join(seo.tags[:8])}")
    print(f"\nTHUMBNAIL TEXT: {seo.thumbnail_text}")

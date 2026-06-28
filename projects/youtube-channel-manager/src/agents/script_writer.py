"""Script Writer Agent — generates full video scripts from ideas.

Produces structured scripts with hooks, timestamps, visual cues, and CTAs.
"""
import uuid
from src.models import VideoIdea, Script


def write_script(idea: VideoIdea, duration_minutes: int = 8,
                 style: str = "educational") -> Script:
    """Generate a full video script from an idea.

    Args:
        idea: The video idea to script
        duration_minutes: Target video length
        style: "educational", "entertainment", "review", "vlog"
    """
    video_id = str(uuid.uuid4())[:8]

    hook = _write_hook(idea, style)
    intro = _write_intro(idea)
    body = _write_body(idea, duration_minutes, style)
    cta = _write_cta(idea)
    outro = _write_outro()

    return Script(
        video_id=video_id,
        title=idea.title,
        hook=hook,
        intro=intro,
        body=body,
        cta=cta,
        outro=outro,
        estimated_duration=f"{duration_minutes}:00",
        b_roll_notes=_suggest_broll(idea, body),
        sound_music_notes=_suggest_music(style),
    )


def _write_hook(idea: VideoIdea, style: str) -> str:
    """Write the first 30 seconds — must grab attention immediately."""
    hooks = {
        "educational": (
            f"By the end of this video, you'll know exactly how to use "
            f"{idea.niche.lower()} to get results — even if you're starting from zero. "
            f"Here's what most people get wrong..."
        ),
        "entertainment": (
            f"I tried {idea.niche.lower()} for 30 days straight. "
            f"What happened next completely changed my perspective..."
        ),
        "review": (
            f"Everyone's talking about {idea.niche.lower()} in 2026. "
            f"But is it actually worth your time? I've tested everything so you don't have to."
        ),
        "vlog": (
            f"So I've been diving deep into {idea.niche.lower()} lately, "
            f"and I want to share everything I've learned — the good, the bad, and the surprising."
        ),
    }
    return hooks.get(style, hooks["educational"])


def _write_intro(idea: VideoIdea) -> str:
    """Write the intro section (after hook)."""
    return (
        f"What's going to in this video. Today we're covering {idea.title.lower()}. "
        f"Whether you're a beginner or already familiar with {idea.niche.lower()}, "
        f"I've got something specific for you in this one. "
        f"Let's get into it."
    )


def _write_body(idea: VideoIdea, duration: int, style: str) -> list[dict]:
    """Write the main content sections with timestamps."""
    sections = []
    num_sections = max(3, min(duration // 3, 8))  # 1 section per ~3 minutes

    for i in range(num_sections):
        timestamp_min = i * 3
        timestamp = f"{timestamp_min}:00"

        if i == 0:
            content = f"First, let's talk about the foundation of {idea.niche.lower()}. " \
                      f"Understanding this is crucial before we dive deeper."
            visual = f"Host talking to camera + text overlay: 'The Basics'"
        elif i == num_sections - 1:
            content = f"Finally, the most important takeaway about {idea.niche.lower()}. " \
                      f"This is where everything comes together."
            visual = f"Host to camera + summary graphics"
        else:
            content = f"Point {i+1}: A key insight about {idea.niche.lower()} " \
                      f"that most people overlook. Here's why it matters..."
            visual = f"B-roll footage + screen recording + text callouts"

        sections.append({
            "timestamp": timestamp,
            "title": f"Section {i+1}",
            "content": content,
            "visual": visual,
            "transition": "cut" if i < num_sections - 1 else "fade",
        })

    return sections


def _write_cta(idea: VideoIdea) -> str:
    """Write call-to-action."""
    return (
        f"If this helped you, smash that like button — it really helps the channel. "
        f"Subscribe and hit the bell for more {idea.niche.lower()} content every week. "
        f"Drop a comment below: what's your biggest challenge with {idea.niche.lower()}?"
    )


def _write_outro() -> str:
    """Write the outro."""
    return (
        "Thanks for watching. I'll see you in the next one. "
        "Check the description for links to everything mentioned in this video."
    )


def _suggest_broll(idea: VideoIdea, body: list[dict]) -> list[str]:
    """Suggest B-roll footage based on content."""
    return [
        f"Opening shot: person at desk with {idea.niche.lower()} setup",
        "Screen recording of tools/platform in use",
        "Close-up of hands typing/working",
        "Lifestyle B-roll of target audience",
        "Result/outcome shots (graphs, screenshots, before/after)",
    ]


def _suggest_music(style: str) -> list[str]:
    """Suggest music/sound based on video style."""
    music = {
        "educational": [
            "Background: lo-fi instrumental, low volume",
            "Transitions: subtle whoosh sounds",
            "Emphasis: light piano sting for key points",
        ],
        "entertainment": [
            "Background: upbeat, energetic instrumental",
            "Transitions: impact sounds, risers",
            "Comedy: subtle bass hits for punchlines",
        ],
        "review": [
            "Background: neutral, professional tone",
            "Transitions: clean cuts, minimal sound",
            "Highlights: subtle tech/UI sounds",
        ],
        "vlog": [
            "Background: chill, lifestyle music",
            "Transitions: natural ambient sounds",
            "Moments: acoustic guitar for reflective parts",
        ],
    }
    return music.get(style, music["educational"])


if __name__ == "__main__":
    from src.models import VideoIdea
    idea = VideoIdea(
        title="AI Automation Tools for Beginners",
        niche="AI automation",
        search_volume="high",
        competition="medium",
        trending_score=75,
        description="Tutorial on getting started with AI automation",
        target_audience="Small business owners",
        estimated_views="10K-50K",
    )
    script = write_script(idea, duration_minutes=8)
    print(f"Script: {script.title}")
    print(f"Duration: {script.estimated_duration}")
    print(f"\nHook: {script.hook[:100]}...")
    print(f"\nBody sections: {len(script.body)}")
    for section in script.body:
        print(f"  {section['timestamp']} — {section['title']}")

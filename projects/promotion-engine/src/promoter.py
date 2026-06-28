"""Promotion Engine — generates and schedules social media posts for AIdentify projects.

Takes project data and creates platform-specific posts:
- Twitter/X: Thread format (5 tweets)
- LinkedIn: Professional story
- Instagram: Carousel brief (needs image from Phani)
- Facebook: Broad reach

All posts are scheduled, not immediate. Respects IST timezone.
No hashtags. Story-driven, not pitch.
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))

# Ocaya API config
OCoYA_BASE = "https://www.app.ocoya.com/api/_public/v1"
OCoYA_KEY = "f15f75a8-3925-4b07-8bb2-aab898df9642"
OCoYA_WORKSPACE = "clapmus480dwb5vzyghnv5dku"

PROFILE_IDS = {
    "twitter": "cmdftz3un00187n0rrzbjc8o4",
    "linkedin": "cll7ytoyz002wl70fnxk0tjwr",
    "instagram": "cmdftzne6005l1hrgeacfi8sx",
    "facebook": "cmdftypmk005e1hrg1b7ow01b",
}

MARKETPLACE_URL = "https://phanindraintelligenzit-afk.github.io/AIdentify/marketplace.html"


def generate_posts(project: dict) -> dict:
    """Generate all platform posts for a project.

    Args:
        project: dict with keys: name, description, github_url, category, agents

    Returns:
        dict with platform -> list of posts
    """
    name = project["name"]
    desc = project.get("description", "")
    github_url = project.get("github_url", "")
    category = project.get("category", "AI")
    agents = project.get("agents", [])

    return {
        "twitter": _twitter_thread(name, desc, github_url, category, agents),
        "linkedin": _linkedin_post(name, desc, github_url, category, agents),
        "instagram": _instagram_post(name, desc, github_url, category),
        "facebook": _facebook_post(name, desc, github_url, category),
    }


def _twitter_thread(name: str, desc: str, github_url: str, category: str, agents: list) -> list[str]:
    """Generate a 5-tweet thread."""
    agent_list = ", ".join([a.split("—")[0].strip() for a in agents[:3]]) if agents else "AI agents"

    tweets = [
        # Tweet 1: Hook
        f"Just built and deployed: {name}. 🤖\n\n{desc[:100]}\n\nBuilt autonomously by our AI agent swarm.\n\nThread 👇",

        # Tweet 2: How it works
        f"How it works:\n\n{agent_list}\n\nEach agent handles one phase of the pipeline. No human intervention needed.",

        # Tweet 3: The tech
        f"Stack: Python, multi-agent pipeline, zero-touch deployment.\n\nScans → Scores → Builds → Tests → Publishes\n\nFrom idea to GitHub in minutes.",

        # Tweet 4: The build story
        f"This wasn't coded by hand.\n\nAn AI agent swarm saw the opportunity, built the full project, ran tests, pushed to GitHub, and updated the marketplace.\n\nAutonomous. Tested. Live.",

        # Tweet 5: CTA
        f"Live now:\n{github_url}\n\nExplore all builds: {MARKETPLACE_URL}\n\nBuilt by AIdentify — India's autonomous AI agency 🇮🇳",
    ]

    # Ensure each tweet is under 280 chars
    return [t[:280] for t in tweets]


def _linkedin_post(name: str, desc: str, github_url: str, category: str, agents: list) -> str:
    """Generate a LinkedIn post (professional, story-driven)."""
    agent_text = ""
    if agents:
        agent_lines = "\n".join([f"  • {a}" for a in agents[:4]])
        agent_text = f"\n\nAgents powering this:\n{agent_lines}"

    return (
        f"We just shipped {name} — built entirely by our AI agent swarm.\n\n"
        f"{desc}\n"
        f"{agent_text}\n\n"
        f"The pipeline: opportunity scan → scoring → build → test → marketplace publish. Fully autonomous.\n\n"
        f"This is what the future of building looks like. No large teams. No funding rounds. Just automation that ships.\n\n"
        f"Live: {github_url}\n"
        f"{MARKETPLACE_URL}\n\n"
        f"What should we build next?"
    )


def _instagram_post(name: str, desc: str, github_url: str, category: str) -> str:
    """Generate Instagram caption (carousel brief)."""
    return (
        f"New build: {name} 🤖🇮🇳\n\n"
        f"{desc[:150]}\n\n"
        f"Swipe to see how our AI agents built this from scratch — no human coding.\n\n"
        f"Link in bio for the full marketplace.\n\n"
        f"#builtnotbought #aiagents #indiahits"  # IG needs some tags for discovery
    )


def _facebook_post(name: str, desc: str, github_url: str, category: str) -> str:
    """Generate Facebook post (broad reach)."""
    return (
        f"Just shipped: {name} 🚀\n\n"
        f"{desc}\n\n"
        f"Built entirely by AI agents. Tested. Published. While we slept.\n\n"
        f"Our autonomous agent swarm is building projects 24/7 — no team, no office, just automation.\n\n"
        f"Check it out: {github_url}\n"
        f"All builds: {MARKETPLACE_URL}"
    )


def schedule_post(platform: str, content: str, post_time_ist: str,
                   media_url: str = None, project_name: str = None) -> dict:
    """Schedule a post via Ocaya API.

    Args:
        platform: twitter, linkedin, instagram, facebook
        content: Post text
        post_time_ist: Time in "HH:MM" format (IST)
        media_url: Optional image URL (required for Instagram)
        project_name: Optional project name (generates image if no media_url)

    Returns:
        API response dict
    """
    import urllib.request

    # Generate image if not provided
    if not media_url and project_name:
        try:
            from src.image_gen import generate_social_image
            image_path = generate_social_image(project_name, "", platform)
            # For Ocaya, we need a URL. Local path won't work.
            # TODO: Upload to a free image host or use data URI workaround
            # For now, note that image was generated
            print(f"  📷 Generated image: {image_path}")
        except Exception as e:
            print(f"  ⚠️ Image generation failed: {e}")

    profile_id = PROFILE_IDS[platform]
    utc_time = _ist_to_utc(post_time_ist)

    payload = {
        "caption": content,
        "socialProfileIds": [profile_id],
        "scheduledAt": utc_time,
        "postNow": False,
    }

    if media_url:
        payload["mediaUrls"] = [media_url]

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{OCoYA_BASE}/post?workspaceId={OCoYA_WORKSPACE}",
        data=data,
        headers={
            "X-API-Key": OCoYA_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


def schedule_posts_for_project(project: dict, start_date: str = None) -> dict:
    """Schedule all posts for a project across platforms.

    Posts at: LinkedIn 8am, Twitter 9am, Instagram 10am, Facebook 11am IST
    """
    if not start_date:
        start_date = datetime.now(IST).strftime("%Y-%m-%d")

    posts = generate_posts(project)
    results = {}

    schedule = [
        ("linkedin", posts["linkedin"], "08:00"),
        ("twitter", "\n\n".join(posts["twitter"]), "09:00"),
        ("instagram", posts["instagram"], "10:00"),
        ("facebook", posts["facebook"], "11:00"),
    ]

    for platform, content, time_ist in schedule:
        result = schedule_post(platform, content, time_ist)
        results[platform] = result
        print(f"  📅 {platform} scheduled for {time_ist} IST: {result.get('postGroupId', result.get('error', '?'))[:20]}")

    return results


def _ist_to_utc(ist_time: str) -> str:
    """Convert IST time (HH:MM) to UTC ISO format for today or tomorrow if time passed."""
    now_ist = datetime.now(IST)
    hour, minute = map(int, ist_time.split(":"))
    dt_ist = now_ist.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # If the scheduled time has already passed today in IST, schedule for tomorrow
    if dt_ist <= now_ist:
        dt_ist = dt_ist + timedelta(days=1)
    
    dt_utc = dt_ist - timedelta(hours=5, minutes=30)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    # Demo with existing projects
    projects = [
        {
            "name": "YouTube Channel Manager",
            "description": "AI content engine for YouTube creators. Generates video ideas, full scripts, SEO metadata, thumbnail briefs, and weekly content calendar.",
            "github_url": "https://github.com/phanindraintelligenzit-afk/youtube-channel-manager",
            "category": "marketing",
            "agents": ["Trend Researcher", "Script Writer", "SEO Agent", "Thumbnail Brief"],
        },
        {
            "name": "Business Inbox Agent",
            "description": "Classifies incoming business requests, extracts structured data, and routes to CRM, support, invoicing, or scheduling workflows.",
            "github_url": "https://github.com/phanindraintelligenzit-afk/business-inbox-agent",
            "category": "marketing",
            "agents": ["Classifier", "Extractor", "Router", "Responder"],
        },
    ]

    for project in projects:
        print(f"\n📢 Generating posts for: {project['name']}")
        posts = generate_posts(project)
        print(f"  Twitter thread: {len(posts['twitter'])} tweets")
        print(f"  LinkedIn: {len(posts['linkedin'])} chars")
        for i, tweet in enumerate(posts["twitter"], 1):
            print(f"    Tweet {i}: {tweet[:60]}...")

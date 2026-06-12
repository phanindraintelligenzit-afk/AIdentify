"""
Multi-Platform Social Media Agent - Post to LinkedIn, X, Instagram, Facebook via Ocoya.
Also handles cross-platform engagement using lead social URLs.
"""
import sys
import os
import json
import random
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocoya_client import (
    create_post,
    schedule_linkedin_post,
    post_to_linkedin,
    post_to_twitter,
    post_to_instagram,
    post_to_facebook,
    post_to_all,
    list_posts,
    LINKEDIN_PROFILE_ID,
    TWITTER_PROFILE_ID,
    INSTAGRAM_PROFILE_ID,
    FACEBOOK_PROFILE_ID,
    WORKSPACE_ID,
)

# ============================================================
# Platform-specific content adaptation
# ============================================================

def adapt_for_platform(caption: str, platform: str) -> str:
    """Adapt a caption for a specific platform's constraints and style."""
    if platform == "twitter":
        # X has 280 char limit for free accounts
        if len(caption) > 270:
            # Truncate smartly at a sentence boundary
            truncated = caption[:270]
            last_period = truncated.rfind('.')
            last_newline = truncated.rfind('\n')
            cut_at = max(last_period, last_newline)
            if cut_at > 100:
                caption = truncated[:cut_at+1]
            else:
                caption = truncated + "..."
        # Add hashtags inline
        return caption

    elif platform == "instagram":
        # Instagram allows longer text but favors emoji + line breaks
        # Move hashtags to end
        lines = caption.split('\n')
        hashtags = [l for l in lines if l.startswith('#')]
        non_tags = [l for l in lines if not l.startswith('#')]
        caption = '\n'.join(non_tags)
        if hashtags:
            caption += '\n.\n.\n.\n' + ' '.join(hashtags)
        return caption

    elif platform == "facebook":
        # Facebook prefers shorter, punchy text
        if len(caption) > 500:
            caption = caption[:500] + "..."
        return caption

    return caption  # LinkedIn: keep as-is


# ============================================================
# Multi-platform post templates
# ============================================================

MULTI_PLATFORM_POSTS = [
    {
        "linkedin": "I'm building an AI automation agency from scratch.\n\nNot with a team of 50. Not with VC funding.\n\nJust me and my AI agents.\n\nHere's what AgentsFactory looks like at Day 1:\n→ 8 AI subagents running operations\n→ Lead finder scanning for prospects\n→ Content writer drafting posts\n→ LinkedIn agent engaging targets\n→ Outreach agent sending 100 DMs/day\n→ Daily briefings at 8 AM\n→ Command Center dashboard tracking everything\n\nThe vision: An AI agency that runs itself.\n\nIf you run a business drowning in manual work — let's talk.\n\n#BuildingInPublic #AIAgents #Automation #SaaS",
        "twitter": "Building an AI automation agency from scratch.\n\nNo team of 50. No VC funding.\n\nJust me + 8 AI agents running everything:\n→ Lead finder\n→ Content writer\n→ LinkedIn agent\n→ Outreach agent\n→ Daily briefings\n→ Command Center\n\nThe vision: An AI agency that runs itself.\n\nDM me if you want in. 🚀\n\n#BuildingInPublic #AIAgents",
        "instagram": "🚀 Building an AI automation agency from scratch\n\nNo team of 50. No VC funding. Just me + 8 AI agents.\n\nHere's what AgentsFactory looks like at Day 1:\n✨ Lead finder scanning prospects\n✨ Content writer drafting posts\n✨ LinkedIn agent engaging targets\n✨ Outreach agent sending DMs\n✨ Daily briefings at 8 AM\n✨ Command Center dashboard\n\nThe vision: An AI agency that runs itself. 💡\n\nLink in bio to learn more!\n\n.\n.\n.\n#BuildingInPublic #AIAgents #Automation #SaaS #StartupLife #TechStartup #Entrepreneurship #AI",
        "facebook": "Excited to announce that AgentsFactory is live! 🚀\n\nWe help e-commerce stores, SaaS companies, and local businesses automate their operations with AI agents.\n\nOur starter plan begins at $500/month.\n\nComment 'INFO' or DM me to learn more!\n\n#AIAgents #Automation #SmallBusiness",
    },
    {
        "linkedin": "💡 The biggest lie in tech right now:\n\n\"AI will replace your job.\"\n\nWrong.\n\nAI will replace the BORING parts of your job.\n\nHere's what I've seen after building 8 AI agents:\n\n✅ Research agents that scan 100+ prospects in minutes\n✅ Writing agents that draft posts, emails, reports\n✅ Engagement agents that nurture leads 24/7\n✅ Automation agents that connect your tools\n\nThe humans who thrive will be the ones who LEARN to direct these agents.\n\nStop fearing AI. Start orchestrating it.\n\nAgree? 👇\n\n#AIAgents #FutureOfWork #Automation",
        "twitter": "Hot take: AI won't replace your job.\n\nIt'll replace the BORING parts.\n\nI built 8 AI agents. Here's what they do:\n\n→ Research 100+ prospects in minutes\n→ Draft posts, emails, reports\n→ Nurture leads 24/7\n→ Connect your tools\n\nThe humans who thrive will be the ones who learn to direct AI.\n\nAgree? 🧵👇\n\n#AIAgents #FutureOfWork",
        "instagram": "🤖 AI won't replace your job.\n\nIt'll replace the BORING parts.\n\nAfter building 8 AI agents, here's what I've learned:\n\n✨ Research agents scan 100+ prospects in minutes\n✨ Writing agents draft posts, emails, reports\n✨ Engagement agents nurture leads 24/7\n✨ Automation agents connect your tools\n\nThe humans who thrive will be the ones who learn to direct AI.\n\nStop fearing. Start orchestrating. 💡\n\n.\n.\n.\n#AIAgents #FutureOfWork #AI #Automation #TechTips #Entrepreneurship #BuildingInPublic",
        "facebook": "Hot take: AI won't replace your job. It'll replace the boring parts. 🤖\n\nAfter building 8 AI agents, here's what I've learned:\n\n→ Research agents scan 100+ prospects in minutes\n→ Writing agents draft posts, emails, reports\n→ Engagement agents nurture leads 24/7\n→ Automation agents connect your tools\n\nThe humans who thrive will be the ones who learn to direct AI.\n\nAgree? Comment below! 👇\n\n#AIAgents #FutureOfWork #Automation",
    },
    {
        "linkedin": "5 things I learned building an AI agency from scratch:\n\n1. Start with ONE agent. Get it working. Then add another.\n2. Content is the best lead gen tool. Post daily. Be consistent.\n3. Automation compounds. Each agent makes the next one easier.\n4. Free models are good enough. Don't pay for AI until you're scaling.\n5. The bottleneck is always decision-making, not execution.\n\nWhich one resonates? 👇\n\n#AIAgents #Entrepreneurship #BuildingInPublic",
        "twitter": "5 things I learned building an AI agency from scratch:\n\n1. Start with ONE agent. Get it working. Then add another.\n2. Content is the best lead gen tool.\n3. Automation compounds.\n4. Free models are good enough.\n5. The bottleneck is decision-making, not execution.\n\nWhich one resonates? 👇\n\n#AIAgents #BuildingInPublic",
        "instagram": "5 things I learned building an AI agency from scratch 💡\n\n1️⃣ Start with ONE agent. Get it working. Then add another.\n2️⃣ Content is the best lead gen tool. Post daily.\n3️⃣ Automation compounds. Each agent makes the next easier.\n4️⃣ Free models are good enough. Don't pay for AI until scaling.\n5️⃣ The bottleneck is decision-making, not execution.\n\nWhich one resonates? Comment below 👇\n\n.\n.\n.\n#AIAgents #Entrepreneurship #BuildingInPublic #StartupTips #AI #Automation",
        "facebook": "5 things I learned building an AI agency from scratch:\n\n1. Start with ONE agent. Get it working. Then add another.\n2. Content is the best lead gen tool. Post daily.\n3. Automation compounds.\n4. Free models are good enough.\n5. The bottleneck is decision-making, not execution.\n\nWhich one resonates with you? Comment below! 👇\n\n#AIAgents #Entrepreneurship #BuildingInPublic",
    },
]


def post_to_all_platforms(post_set: dict = None, schedule_hours: float = 0.25) -> dict:
    """
    Post to all 4 platforms (LinkedIn, X, Instagram, Facebook) simultaneously.
    Each platform gets platform-optimized content.
    """
    if not post_set:
        post_set = random.choice(MULTI_PLATFORM_POSTS)

    dt = datetime.now(timezone.utc) + timedelta(hours=schedule_hours)
    scheduled_at = dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    results = {}

    # LinkedIn
    try:
        results["linkedin"] = post_to_linkedin(
            adapt_for_platform(post_set["linkedin"], "linkedin"),
            scheduled_at=scheduled_at
        )
    except Exception as e:
        results["linkedin"] = {"error": str(e)}

    # X/Twitter
    try:
        results["twitter"] = post_to_twitter(
            adapt_for_platform(post_set["twitter"], "twitter"),
            scheduled_at=scheduled_at
        )
    except Exception as e:
        results["twitter"] = {"error": str(e)}

    # Instagram (requires media URL — rotate through branded images)
    INSTAGRAM_MEDIA_URLS = [
        "https://phanindraintelligenzit-afk.github.io/AgentsFactory/landing/social-assets/01_brand_welcome.png",
        "https://phanindraintelligenzit-afk.github.io/AgentsFactory/landing/social-assets/02_day_progress.png",
        "https://phanindraintelligenzit-afk.github.io/AgentsFactory/landing/social-assets/03_ai_agent_explainer.png",
        "https://phanindraintelligenzit-afk.github.io/AgentsFactory/landing/social-assets/04_services_overview.png",
        "https://phanindraintelligenzit-afk.github.io/AgentsFactory/landing/social-assets/05_what_are_agents.png",
        "https://phanindraintelligenzit-afk.github.io/AgentsFactory/landing/social-assets/06_behind_scenes.png",
        "https://phanindraintelligenzit-afk.github.io/AgentsFactory/landing/social-assets/07_testimonial.png",
        "https://phanindraintelligenzit-afk.github.io/AgentsFactory/landing/social-assets/08_five_things_learned.png",
        "https://phanindraintelligenzit-afk.github.io/AgentsFactory/landing/social-assets/09_workflow_diagram.png",
        "https://phanindraintelligenzit-afk.github.io/AgentsFactory/landing/social-assets/10_cta_dm.png",
    ]

    # Instagram (requires media URL — use branded image)
    try:
        media_url = random.choice(INSTAGRAM_MEDIA_URLS)
        results["instagram"] = create_post(
            caption=adapt_for_platform(post_set["instagram"], "instagram"),
            social_profile_ids=[INSTAGRAM_PROFILE_ID],
            scheduled_at=scheduled_at,
            media_urls=[media_url],
        )
    except Exception as e:
        results["instagram"] = {"error": str(e)}

    # Facebook
    try:
        results["facebook"] = post_to_facebook(
            adapt_for_platform(post_set["facebook"], "facebook"),
            scheduled_at=scheduled_at
        )
    except Exception as e:
        results["facebook"] = {"error": str(e)}

    return results


def engage_with_lead_social(lead: dict) -> dict:
    """
    Engage with a lead across their social platforms.
    Uses their Facebook and Twitter URLs from the lead data.
    """
    results = {"lead": lead.get("company", "Unknown"), "actions": []}

    # Generate platform-specific engagement
    fb_url = lead.get("facebook_url", "")
    tw_url = lead.get("twitter_url", "")

    if fb_url:
        # Create a Facebook post mentioning the lead's industry
        industry = lead.get("category", "business")
        fb_post = f"Shoutout to amazing {industry} companies making waves! 🚀\n\nWho else is doing great work in this space? Tag them below! 👇\n\n#{industry.replace(' ', '')} #BusinessGrowth"
        try:
            result = post_to_facebook(fb_post)
            results["actions"].append({"platform": "facebook", "action": "post", "result": result})
        except Exception as e:
            results["actions"].append({"platform": "facebook", "error": str(e)})

    if tw_url:
        # Create a Twitter post
        tw_post = f"Shoutout to amazing companies in the {lead.get('category', 'marketing')} space! 🚀\n\nWho else is doing great work? Tag them below! 👇"
        try:
            result = post_to_twitter(tw_post)
            results["actions"].append({"platform": "twitter", "action": "post", "result": result})
        except Exception as e:
            results["actions"].append({"platform": "twitter", "error": str(e)})

    return results


def run_multi_platform_cycle() -> dict:
    """
    Run a full multi-platform social media cycle:
    1. Post to all 4 platforms
    2. Engage with top leads' social profiles
    3. Track metrics
    """
    results = {
        "timestamp": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        "actions": [],
    }

    # Step 1: Post to all platforms
    post_results = post_to_all_platforms()
    results["actions"].append({
        "type": "multi_platform_post",
        "results": post_results,
    })
    print(f"✅ Multi-platform post created")
    for platform, result in post_results.items():
        status = "✅" if "error" not in result else "❌"
        print(f"  {status} {platform}: {result.get('postGroupId', result.get('error', 'N/A'))}")

    return results


def get_multi_platform_stats() -> dict:
    """Get stats across all platforms."""
    try:
        posted = list_posts(status="POSTED", limit=100)
        scheduled = list_posts(status="SCHEDULED", limit=100)

        stats = {
            "total_posted": len(posted),
            "total_scheduled": len(scheduled),
            "by_platform": {},
        }

        for post in posted:
            for sp in post.get("socialProfiles", []):
                provider = sp["socialProfile"]["provider"]
                stats["by_platform"][provider] = stats["by_platform"].get(provider, 0) + 1

        return stats
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Multi-Platform Social Media Agent")
    parser.add_argument("--post-all", action="store_true", help="Post to all 4 platforms")
    parser.add_argument("--stats", action="store_true", help="Show multi-platform stats")
    parser.add_argument("--cycle", action="store_true", help="Run full multi-platform cycle")
    args = parser.parse_args()

    if args.post_all:
        results = post_to_all_platforms()
        print(json.dumps(results, indent=2))
    elif args.stats:
        stats = get_multi_platform_stats()
        print(json.dumps(stats, indent=2))
    elif args.cycle:
        results = run_multi_platform_cycle()
        print(json.dumps(results, indent=2))
    else:
        print("Multi-Platform Social Media Agent ready. Use --help for options.")

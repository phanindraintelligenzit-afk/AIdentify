"""
Outreach Agent - Automated personalized outreach across platforms.
Uses Ocoya for social engagement and email for direct outreach.
"""
import sys
import os
import json
import random
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocoya_client import post_to_linkedin, LINKEDIN_PROFILE_ID

# ============================================================
# Outreach templates
# ============================================================

COLD_DM_TEMPLATES = [
    "Hey {name}! I noticed you're working on {company_focus}. We just helped a similar {industry} company automate {pain_point}, saving them {time_saved}. Worth a quick 15-min chat?",
    "Hi {name} — love what {company} is doing with {company_focus}. Quick question: how are you currently handling {pain_point}? We've built AI agents that cut that work by 80%.",
    "Hey {name}, random question — if you could eliminate one repetitive task from your team's workflow, what it would be? We're building AI agents specifically for {industry} companies.",
    "Hi {name}! Saw your post about {topic}. Great insight. We're working on something similar — AI agents that handle {pain_point} for {industry} businesses. Would love to get your thoughts.",
    "Hey {name} — quick one. We help {industry} companies automate {pain_point}. Our clients typically see {result} within 30 days. If that's relevant, happy to share more.",
]

FOLLOW_UP_TEMPLATES = [
    "Hey {name}, just bumping this up. Still relevant — our {industry} clients are seeing great results with {pain_point} automation. 15 min call this week?",
    "Hi {name}, following up. We just onboarded another {industry} client and they're already saving {time_saved}/week. Happy to share the playbook if you're interested.",
    "Hey {name}, one more try. If {pain_point} is still a bottleneck, we should talk. If not, no worries — have a great week!",
]

VALUE_FIRST_TEMPLATES = [
    "Hey {name}, put together a quick analysis of {company}'s {area}. Found 3 quick wins that could save {time_saved}/week. Want me to share?",
    "Hi {name}, I built a free automation audit tool. Ran it for {company} and found some interesting opportunities in {area}. Happy to share the report?",
    "Hey {name} — here's a free resource on how {industry} companies are using AI to handle {pain_point}. Thought it might be useful: [link]. No pitch, just value.",
]


def generate_cold_dm(name: str, company: str, industry: str = "ecommerce",
                     pain_point: str = "manual work", time_saved: str = "20 hours") -> str:
    """Generate a personalized cold DM."""
    template = random.choice(COLD_DM_TEMPLATES)
    company_focus = random.choice([
        "growth", "scaling", "automation", "customer experience",
        "operations", "efficiency", "digital transformation"
    ])
    result = random.choice([
        "20+ hours saved/week", "50% cost reduction", "3x faster delivery",
        "80% less manual work", "double the output with same team"
    ])

    return template.format(
        name=name,
        company=company,
        company_focus=company_focus,
        industry=industry,
        pain_point=pain_point,
        time_saved=time_saved,
        result=result,
        topic="automation"  # default
    )


def generate_follow_up(name: str, company: str, industry: str = "ecommerce",
                       pain_point: str = "manual work", time_saved: str = "20 hours") -> str:
    """Generate a follow-up message."""
    template = random.choice(FOLLOW_UP_TEMPLATES)
    return template.format(
        name=name,
        company=company,
        industry=industry,
        pain_point=pain_point,
        time_saved=time_saved
    )


def create_outreach_post(target_audience: str = "ecommerce founders") -> dict:
    """
    Create a LinkedIn post designed to attract inbound leads.
    These are value-first posts that get people to comment/DM.
    """
    posts = [
        f"Free audit: I'll analyze your {target_audience} operations and find 3 automation opportunities.\n\nNo pitch. No strings.\n\nJust comment 'AUDIT' below.\n\n#Automation #AIAgents #Ecommerce",
        f"I'm offering 5 free AI automation audits this week.\n\nFor {target_audience} who are:\n→ Drowning in manual work\n→ Spending 20+ hrs/week on repeatable tasks\n→ Ready to scale but operations are the bottleneck\n\nComment 'AUDIT' or DM me.\n\n#AIAgents #Automation #Growth",
        f"Give me 15 minutes and I'll show you how to save 20+ hours/week with AI automation.\n\nNo cost. No commitment. Just results.\n\nComment '15' below 👇\n\n#{target_audience.replace(' ', '')} #AIAgents #Automation",
    ]

    post_text = random.choice(posts)
    return post_to_linkedin(post_text)


def run_outreach_cycle(leads: list[dict] = None) -> dict:
    """
    Run a full outreach cycle:
    1. Create an outreach-optimized post
    2. Generate DMs for leads (if provided)
    3. Track outreach metrics
    """
    results = {
        "timestamp": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        "actions": [],
    }

    # Step 1: Create an outreach post
    post_result = create_outreach_post()
    results["actions"].append({
        "type": "outreach_post",
        "result": post_result,
    })
    print(f"✅ Outreach post created: {post_result.get('postGroupId', 'N/A')}")

    # Step 2: Generate DMs for leads (if provided)
    if leads:
        dms_generated = []
        for lead in leads[:10]:  # Max 10 per cycle
            dm = generate_cold_dm(
                name=lead.get("name", "there"),
                company=lead.get("company", "your company"),
                industry=lead.get("industry", "ecommerce"),
            )
            dms_generated.append({
                "lead": lead.get("name"),
                "company": lead.get("company"),
                "dm": dm,
            })
        results["actions"].append({
            "type": "dms_generated",
            "count": len(dms_generated),
            "dms": dms_generated,
        })
        print(f"✅ Generated {len(dms_generated)} outreach DMs")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Outreach Agent")
    parser.add_argument("--outreach", action="store_true", help="Run outreach cycle")
    parser.add_argument("--dm", type=str, help="Generate a cold DM for a name")
    parser.add_argument("--company", type=str, help="Company name for DM")
    parser.add_argument("--outreach-post", action="store_true", help="Create an outreach post")
    args = parser.parse_args()

    if args.outreach:
        results = run_outreach_cycle()
        print(json.dumps(results, indent=2))
    elif args.dm:
        dm = generate_cold_dm(args.dm, args.company or "your company")
        print(dm)
    elif args.outreach_post:
        result = create_outreach_post()
        print(json.dumps(result, indent=2))
    else:
        print("Outreach Agent ready. Use --help for options.")

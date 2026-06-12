#!/usr/bin/env python3
"""AgentsFactory Weekly Review — Run every Monday at 9:00 AM IST.

Generates a comprehensive weekly business review:
1. Revenue this week vs last week
2. Lead pipeline health (new, converted, lost, stage distribution)
3. Content performance (published, engagement)
4. Automation uptime across all clients
5. Top 3 recommendations for the coming week
6. Agent activity summary
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "agentsfactory_metrics.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def log_activity(action: str, target: str = "", status: str = "completed", details: str = ""):
    conn = get_db()
    conn.execute(
        "INSERT INTO agent_activity (agent_name, action, target, status, details) VALUES (?, ?, ?, ?, ?)",
        ("reporter", action, target, status, details),
    )
    conn.commit()
    conn.close()


def get_revenue_comparison() -> dict:
    conn = get_db()
    # This week
    confirmed_this_week = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM revenue WHERE status='confirmed' "
        "AND created_at >= date('now', 'weekday 0', '-7 days')"
    ).fetchone()[0] or 0
    # Last week
    confirmed_last_week = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM revenue WHERE status='confirmed' "
        "AND created_at >= date('now', 'weekday 0', '-14 days') "
        "AND created_at < date('now', 'weekday 0', '-7 days')"
    ).fetchone()[0] or 0
    # Projected
    projected = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM revenue WHERE status='projected'"
    ).fetchone()[0] or 0
    conn.close()
    change = confirmed_this_week - confirmed_last_week
    pct = ((change / confirmed_last_week) * 100) if confirmed_last_week > 0 else 0
    return {
        "this_week": confirmed_this_week,
        "last_week": confirmed_last_week,
        "change": change,
        "pct_change": pct,
        "projected": projected,
    }


def get_lead_pipeline_health() -> dict:
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    new_this_week = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE created_at >= date('now', 'weekday 0', '-7 days')"
    ).fetchone()[0] or 0
    converted = conn.execute("SELECT COUNT(*) FROM leads WHERE stage='won'").fetchone()[0] or 0
    lost = conn.execute("SELECT COUNT(*) FROM leads WHERE stage='lost'").fetchone()[0] or 0
    hot = conn.execute("SELECT COUNT(*) FROM leads WHERE score >= 70").fetchone()[0] or 0
    by_stage = conn.execute(
        "SELECT stage, COUNT(*) as cnt FROM leads GROUP BY stage ORDER BY cnt DESC"
    ).fetchall()
    conn.close()
    return {
        "total": total,
        "new_this_week": new_this_week,
        "converted": converted,
        "lost": lost,
        "hot": hot,
        "by_stage": dict(by_stage),
    }


def get_content_performance() -> dict:
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM content_calendar").fetchone()[0] or 0
    published = conn.execute(
        "SELECT COUNT(*) FROM content_calendar WHERE status='published'"
    ).fetchone()[0] or 0
    published_this_week = conn.execute(
        "SELECT COUNT(*) FROM content_calendar WHERE status='published' "
        "AND published_at >= date('now', 'weekday 0', '-7 days')"
    ).fetchone()[0] or 0
    drafts = conn.execute(
        "SELECT COUNT(*) FROM content_calendar WHERE status='draft'"
    ).fetchone()[0] or 0
    scheduled = conn.execute(
        "SELECT COUNT(*) FROM content_calendar WHERE status='scheduled'"
    ).fetchone()[0] or 0
    by_platform = conn.execute(
        "SELECT platform, COUNT(*) as cnt FROM content_calendar GROUP BY platform"
    ).fetchall()
    conn.close()
    return {
        "total": total,
        "published": published,
        "published_this_week": published_this_week,
        "drafts": drafts,
        "scheduled": scheduled,
        "by_platform": dict(by_platform),
    }


def get_automation_uptime() -> dict:
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM automation_health").fetchone()[0] or 0
    running = conn.execute(
        "SELECT COUNT(*) FROM automation_health WHERE status='running'"
    ).fetchone()[0] or 0
    errors = conn.execute(
        "SELECT COUNT(*) FROM automation_health WHERE status='error'"
    ).fetchone()[0] or 0
    avg_uptime = conn.execute(
        "SELECT COALESCE(AVG(uptime_pct), 0) FROM automation_health"
    ).fetchone()[0] or 0
    total_success = conn.execute(
        "SELECT COALESCE(SUM(success_count), 0) FROM automation_health"
    ).fetchone()[0] or 0
    total_failures = conn.execute(
        "SELECT COALESCE(SUM(failure_count), 0) FROM automation_health"
    ).fetchone()[0] or 0
    conn.close()
    return {
        "total": total,
        "running": running,
        "errors": errors,
        "avg_uptime": round(avg_uptime, 1),
        "total_success": total_success,
        "total_failures": total_failures,
    }


def get_weekly_agent_activity() -> dict:
    conn = get_db()
    total_actions = conn.execute(
        "SELECT COUNT(*) FROM agent_activity "
        "WHERE created_at >= date('now', 'weekday 0', '-7 days')"
    ).fetchone()[0] or 0
    by_agent = conn.execute(
        "SELECT agent_name, COUNT(*) as cnt FROM agent_activity "
        "WHERE created_at >= date('now', 'weekday 0', '-7 days') "
        "GROUP BY agent_name ORDER BY cnt DESC"
    ).fetchall()
    conn.close()
    return {"total_actions": total_actions, "by_agent": dict(by_agent)}


def generate_recommendations(rev: dict, leads: dict, content: dict, auto: dict) -> list[str]:
    recs = []
    # Revenue recommendations
    if rev["projected"] > rev["this_week"] * 2:
        recs.append("💰 **Close projected deals**: You have 2x more projected revenue than confirmed this week. Focus on converting proposals to signed clients.")
    if rev["this_week"] == 0:
        recs.append("💰 **Revenue urgency**: No confirmed revenue this week. Prioritize outreach to warm leads or follow up on proposals.")
    # Lead recommendations
    if leads["hot"] > 0 and leads["new_this_week"] == 0:
        recs.append("🎯 **Activate hot leads**: You have hot leads but no new ones this week. Time to ramp up outbound — aim for 50+ new outreach messages.")
    if leads["total"] < 10:
        recs.append("🎯 **Pipeline building**: Pipeline is thin (< 10 leads). Run the Lead Finder agent: `python src/agents/lead_finder.py --source all --limit 50`")
    # Content recommendations
    if content["published_this_week"] < 3:
        recs.append("📝 **Content gap**: Fewer than 3 posts published this week. Run Content Writer: `python src/agents/content_writer.py --platform linkedin --count 5 --dry-run`")
    if content["drafts"] > 10:
        recs.append("📝 **Draft backlog**: You have 10+ unpublished drafts. Schedule or publish them this week.")
    # Automation recommendations
    if auto["errors"] > 0:
        recs.append(f"🤖 **Automation errors**: {auto['errors']} automation(s) in error state. Check the Automation Health page in the Command Center.")
    if auto["avg_uptime"] < 95 and auto["total"] > 0:
        recs.append(f"🤖 **Uptime alert**: Average uptime is {auto['avg_uptime']}% (below 95% target). Investigate failing automations.")
    # Default if nothing urgent
    if not recs:
        recs.append("✅ **All systems green**: Keep up the momentum. Focus on consistent outreach and content publishing.")
    return recs


def generate_weekly_review() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    rev = get_revenue_comparison()
    leads = get_lead_pipeline_health()
    content = get_content_performance()
    auto = get_automation_uptime()
    activity = get_weekly_agent_activity()
    recs = generate_recommendations(rev, leads, content, auto)

    lines = [
        f"🏭 **AgentsFactory — Weekly Business Review**",
        f"📅 Week of {now} IST",
        "",
        "---",
        "",
        "💰 **Revenue**",
        f"- This week: ${rev['this_week']:,.0f} | Last week: ${rev['last_week']:,.0f}",
        f"- Change: ${rev['change']:+,.0f} ({rev['pct_change']:+.0f}%)",
        f"- Projected pipeline: ${rev['projected']:,.0f}",
        "",
        "🎯 **Lead Pipeline**",
        f"- Total: {leads['total']} | New this week: {leads['new_this_week']}",
        f"- Hot: {leads['hot']} | Converted: {leads['converted']} | Lost: {leads['lost']}",
    ]
    if leads["by_stage"]:
        stage_str = " | ".join(f"{k}: {v}" for k, v in leads["by_stage"].items())
        lines.append(f"- By stage: {stage_str}")

    lines += [
        "",
        "📝 **Content**",
        f"- Published this week: {content['published_this_week']}",
        f"- Total published: {content['published']} | Drafts: {content['drafts']} | Scheduled: {content['scheduled']}",
    ]

    lines += [
        "",
        "🤖 **Automations**",
        f"- Running: {auto['running']}/{auto['total']} | Errors: {auto['errors']}",
        f"- Avg uptime: {auto['avg_uptime']}%",
        f"- Successes: {auto['total_success']:,} | Failures: {auto['total_failures']:,}",
        "",
        "⚡ **Agent Activity (this week)**",
        f"- Total actions: {activity['total_actions']}",
    ]
    if activity["by_agent"]:
        for agent, cnt in activity["by_agent"].items():
            lines.append(f"  - {agent}: {cnt} actions")

    lines += [
        "",
        "---",
        "",
        "🔮 **Top 3 Recommendations for Next Week**",
    ]
    for i, rec in enumerate(recs[:3], 1):
        lines.append(f"{i}. {rec}")

    lines += [
        "",
        "---",
        "",
        "📊 **Command Center:** http://localhost:8501",
        "📋 **Notion:** https://notion.so/37d4baec816581a7a0e1de4593503d35",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    review = generate_weekly_review()
    print(review)
    log_activity("weekly_review", "all", "completed", "Generated weekly business review")

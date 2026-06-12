#!/usr/bin/env python3
"""AgentsFactory Daily Briefing — Run at 8:00 AM IST daily.

Generates a morning briefing with:
1. Automation health check
2. New leads found
3. Content drafted
4. Email scan summary
5. Command center snapshot

Outputs a markdown briefing and sends to Phani via Telegram.
"""

from __future__ import annotations

import sqlite3
import json
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


def get_automation_health() -> dict:
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM automation_health").fetchone()[0]
    running = conn.execute("SELECT COUNT(*) FROM automation_health WHERE status='running'").fetchone()[0]
    errors = conn.execute("SELECT COUNT(*) FROM automation_health WHERE status='error'").fetchone()[0]
    avg_uptime = conn.execute("SELECT COALESCE(AVG(uptime_pct), 0) FROM automation_health").fetchone()[0]
    conn.close()
    return {"total": total, "running": running, "errors": errors, "avg_uptime": round(avg_uptime, 1)}


def get_leads_summary() -> dict:
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    hot = conn.execute("SELECT COUNT(*) FROM leads WHERE score >= 70").fetchone()[0]
    new_today = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE date(created_at) = date('now')"
    ).fetchone()[0]
    by_stage = conn.execute(
        "SELECT stage, COUNT(*) as cnt FROM leads GROUP BY stage ORDER BY cnt DESC"
    ).fetchall()
    conn.close()
    return {"total": total, "hot": hot, "new_today": new_today, "by_stage": dict(by_stage)}


def get_content_summary() -> dict:
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM content_calendar").fetchone()[0]
    published = conn.execute("SELECT COUNT(*) FROM content_calendar WHERE status='published'").fetchone()[0]
    drafts = conn.execute("SELECT COUNT(*) FROM content_calendar WHERE status='draft'").fetchone()[0]
    scheduled = conn.execute("SELECT COUNT(*) FROM content_calendar WHERE status='scheduled'").fetchone()[0]
    conn.close()
    return {"total": total, "published": published, "drafts": drafts, "scheduled": scheduled}


def get_revenue_summary() -> dict:
    conn = get_db()
    confirmed = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM revenue WHERE status='confirmed'"
    ).fetchone()[0]
    projected = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM revenue WHERE status='projected'"
    ).fetchone()[0]
    conn.close()
    return {"confirmed": confirmed, "projected": projected, "total": confirmed + projected}


def get_agent_activity_today() -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT agent_name, action, target, status, created_at FROM agent_activity "
        "WHERE date(created_at) = date('now') ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def generate_briefing() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    health = get_automation_health()
    leads = get_leads_summary()
    content = get_content_summary()
    revenue = get_revenue_summary()
    activity = get_agent_activity_today()

    lines = [
        f"🏭 **AgentsFactory Daily Briefing**",
        f"📅 {now} IST",
        "",
        "---",
        "",
        "🤖 **Automation Health**",
        f"- Running: {health['running']}/{health['total']}",
        f"- Errors: {health['errors']}",
        f"- Avg Uptime: {health['avg_uptime']}%",
        "",
        "🎯 **Lead Pipeline**",
        f"- Total: {leads['total']} | Hot: {leads['hot']} | New today: {leads['new_today']}",
    ]
    if leads["by_stage"]:
        stage_str = " | ".join(f"{k}: {v}" for k, v in leads["by_stage"].items())
        f"- By stage: {stage_str}"
        lines.append(stage_str)

    lines += [
        "",
        "📝 **Content**",
        f"- Published: {content['published']} | Drafts: {content['drafts']} | Scheduled: {content['scheduled']}",
        "",
        "💰 **Revenue**",
        f"- Confirmed: ${revenue['confirmed']:,.0f} | Projected: ${revenue['projected']:,.0f}",
        f"- Total pipeline: ${revenue['total']:,.0f}",
        "",
        "⚡ **Today's Agent Activity**",
    ]

    if activity:
        for a in activity[:10]:
            lines.append(f"- [{a['agent_name']}] {a['action']} → {a['target']} ({a['status']})")
    else:
        lines.append("- No agent activity yet today.")

    lines += [
        "",
        "---",
        "",
        "📊 **Command Center:** http://localhost:8501",
        "📋 **Notion:** https://notion.so/37d4baec816581a7a0e1de4593503d35",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    briefing = generate_briefing()
    print(briefing)
    log_activity("daily_briefing", "all", "completed", "Generated daily briefing")

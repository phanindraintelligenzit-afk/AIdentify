"""
AIdentify Pipeline Manager.

This is the bridge between "Phani picks an opportunity" and "agents build it."

Flow:
  1. Business Scanner cron delivers opportunities to Slack
  2. Phani says "I like #3" or "build the compliance one"
  3. Pipeline Manager creates a project, breaks it into tasks, assigns agents
  4. Agents work, post to War Room, dashboard tracks progress

Usage:
    python scripts/pipeline_manager.py --list
    python scripts/pipeline_manager.py --create "AI Compliance Monitor" --from-opportunity 1
    python scripts/pipeline_manager.py --status
    python scripts/pipeline_manager.py --agent-work
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent_activity import ActivityLogger, init_activity_db

# ── Opportunity templates ────────────────────────────────────────────────────
# These map to the 5 opportunities from the Jun 21 scout report.
# When Phani picks one, we expand it into a full project with tasks.

OPPORTUNITY_TEMPLATES = {
    "compliance": {
        "title": "AI Compliance & Governance Monitor",
        "tagline": "Compliance-as-a-Service for AI teams. EU AI Act enforcement.",
        "revenue": "$2K-$15K/mo",
        "build_weeks": "2-3",
        "tasks": [
            {"title": "Design compliance audit schema", "agent": "Planner", "priority": "high",
             "desc": "Define what data points to capture: agent decisions, data lineage, model versions, user consent"},
            {"title": "Build decision logger middleware", "agent": "Coder", "priority": "high",
             "desc": "LangGraph middleware that logs every agent decision with timestamp, inputs, outputs, confidence"},
            {"title": "Build anomaly detection", "agent": "Coder", "priority": "high",
             "desc": "Flag decisions that deviate from policy: PII leakage, unauthorized data access, off-policy actions"},
            {"title": "Regulatory research — EU AI Act", "agent": "Researcher", "priority": "normal",
             "desc": "Map EU AI Act requirements to technical controls. What must be logged? What triggers reporting?"},
            {"title": "Build audit report generator", "agent": "Coder", "priority": "normal",
             "desc": "Auto-generate compliance reports: daily summary, weekly digest, incident reports"},
            {"title": "Design landing page", "agent": "Planner", "priority": "normal",
             "desc": "Landing page for compliance product. Value prop, pricing tiers, demo CTA"},
            {"title": "Write launch content", "agent": "Social", "priority": "low",
             "desc": "LinkedIn post, Twitter thread, email sequence for launch"},
            {"title": "Outreach to AI-first startups", "agent": "Outreach", "priority": "normal",
             "desc": "Identify 50 AI-first startups (Series A-C). Send personalized compliance audit offers"},
        ],
    },
    "orchestration": {
        "title": "Multi-Agent Orchestration for Dev Teams",
        "tagline": "Agent orchestration layer. What Datadog did for servers, for AI agents.",
        "revenue": "$3K-$8K/mo",
        "build_weeks": "1-2",
        "tasks": [
            {"title": "Design agent pipeline DSL", "agent": "Planner", "priority": "high",
             "desc": "Simple YAML/JSON config to define agent pipelines: code review, security scan, performance check"},
            {"title": "Build pipeline runner", "agent": "Coder", "priority": "high",
             "desc": "FastAPI service that takes a PR URL, runs it through configured agent pipeline, returns results"},
            {"title": "Build security review agent", "agent": "Coder", "priority": "high",
             "desc": "Agent that reviews code for security issues: SQL injection, XSS, auth bypass, secrets in code"},
            {"title": "Competitor analysis — AI code review", "agent": "Researcher", "priority": "normal",
             "desc": "Analyze Snyk, SonarQube, CodeRabbit, Semgrep. What do they miss? Where's the gap?"},
            {"title": "Build landing page + demo", "agent": "Coder", "priority": "normal",
             "desc": "Live demo: paste a PR URL, see agent analysis. Landing page with pricing"},
            {"title": "Write launch content", "agent": "Social", "priority": "low",
             "desc": "Dev-focused content: Twitter thread, LinkedIn post, Hacker News launch"},
            {"title": "Outreach to dev teams", "agent": "Outreach", "priority": "normal",
             "desc": "Target Series A-C dev teams. Offer free pipeline audit"},
        ],
    },
    "lifesci": {
        "title": "Life Sciences Document Processing",
        "tagline": "AI-powered document processing for pharma/biotech regulatory submissions.",
        "revenue": "$5K-$15K/mo",
        "build_weeks": "4-6",
        "tasks": [
            {"title": "Research FDA submission formats", "agent": "Researcher", "priority": "high",
             "desc": "Map IND, NDA, BLA submission structures. What documents are required? What's the validation criteria?"},
            {"title": "Build document extractor", "agent": "Coder", "priority": "high",
             "desc": "Extract structured data from clinical study reports: tables, endpoints, adverse events, statistics"},
            {"title": "Build template validator", "agent": "Coder", "priority": "high",
             "desc": "Validate extracted data against FDA templates. Flag missing fields, format errors, inconsistencies"},
            {"title": "Build CSR generator", "agent": "Coder", "priority": "normal",
             "desc": "Auto-generate Clinical Study Report sections from extracted data"},
            {"title": "Compliance review — 21 CFR Part 11", "agent": "Researcher", "priority": "normal",
             "desc": "Ensure system meets FDA 21 CFR Part 11 requirements for electronic records"},
            {"title": "Landing page for pharma CROs", "agent": "Planner", "priority": "low",
             "desc": "Targeted landing page: compliance, accuracy, speed. Case study format"},
            {"title": "Outreach to pharma CROs", "agent": "Outreach", "priority": "normal",
             "desc": "Identify 30 small/mid-size pharma CROs. Offer free document processing pilot"},
        ],
    },
    "observability": {
        "title": "AI Agent Observability Platform",
        "tagline": "What Datadog did for servers, for AI agents. Trace decisions, track costs, monitor quality.",
        "revenue": "$500-$2K/mo",
        "build_weeks": "3-4",
        "tasks": [
            {"title": "Design agent tracing schema", "agent": "Planner", "priority": "high",
             "desc": "Define trace format: agent name, input, output, latency, cost, confidence, parent trace ID"},
            {"title": "Build trace collector SDK", "agent": "Coder", "priority": "high",
             "desc": "Python SDK that agents can import. Auto-captures traces, sends to collector API"},
            {"title": "Build collector API", "agent": "Coder", "priority": "high",
             "desc": "FastAPI service that receives traces, stores in Postgres, exposes query API"},
            {"title": "Build dashboard", "agent": "Coder", "priority": "normal",
             "desc": "Streamlit dashboard: agent activity, cost tracking, latency percentiles, error rates"},
            {"title": "Competitor analysis", "agent": "Researcher", "priority": "normal",
             "desc": "Analyze LangSmith, Arize, Braintrust, Langfuse. Pricing, features, gaps"},
            {"title": "Open-source strategy", "agent": "Planner", "priority": "normal",
             "desc": "What to open-source (collector SDK) vs sell (hosted dashboard). Community building plan"},
            {"title": "Launch content", "agent": "Social", "priority": "low",
             "desc": "HN launch post, Twitter thread, LinkedIn. Target AI engineers"},
            {"title": "Outreach to AI-first companies", "agent": "Outreach", "priority": "normal",
             "desc": "Target companies with 5+ agents in production. Free tier signup campaign"},
        ],
    },
    "hr": {
        "title": "HR Automation Pipeline",
        "tagline": "End-to-end HR automation: recruiting → onboarding → performance → offboarding.",
        "revenue": "$1K-$3K/mo",
        "build_weeks": "3-4",
        "tasks": [
            {"title": "Map HR pipeline stages", "agent": "Planner", "priority": "high",
             "desc": "Define the full pipeline: resume screen, interview schedule, onboarding docs, policy Q&A, exit survey"},
            {"title": "Build resume screener", "agent": "Coder", "priority": "high",
             "desc": "Agent that scores resumes against job description. Explains why/not a match"},
            {"title": "Build interview scheduler", "agent": "Coder", "priority": "normal",
             "desc": "Agent that coordinates interview times, sends calendar invites, prepares interviewer brief"},
            {"title": "Build onboarding doc generator", "agent": "Coder", "priority": "normal",
             "desc": "Auto-generate onboarding docs: team intro, project overview, first-week checklist, tool access"},
            {"title": "HR tech competitor analysis", "agent": "Researcher", "priority": "normal",
             "desc": "Analyze Lever, Greenhouse, BambooHR, Workable. What's missing? Where's the AI gap?"},
            {"title": "Landing page for HR teams", "agent": "Planner", "priority": "low",
             "desc": "Target mid-size companies (50-500 employees). ROI calculator, case studies"},
            {"title": "Outreach to HR leaders", "agent": "Outreach", "priority": "normal",
             "desc": "Target HR directors at mid-size companies. Free pilot offer"},
        ],
    },
}


class PipelineManager:
    """Manages projects and task assignments for AIdentify."""

    def __init__(self):
        init_activity_db()
        self.logger = ActivityLogger()

    def create_project(self, key: str, custom_title: str = None) -> dict:
        """Create a full project from an opportunity template."""
        template = OPPORTUNITY_TEMPLATES.get(key)
        if not template:
            available = ", ".join(OPPORTUNITY_TEMPLATES.keys())
            return {"error": f"Unknown opportunity '{key}'. Available: {available}"}

        title = custom_title or template["title"]
        project_id = f"proj-{key}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Create project task entries
        created_tasks = []
        for i, task_template in enumerate(template["tasks"]):
            task_id = f"{project_id}-task-{i+1:02d}"
            self.logger.create_task(
                task_id=task_id,
                title=task_template["title"],
                assigned_to=task_template["agent"],
                description=task_template["desc"],
                priority=task_template["priority"],
                tags=json.dumps([key, "opportunity", f"priority-{task_template['priority']}"]),
                created_by="Phani (Pipeline)",
            )
            self.logger.update_task(task_id, "assigned")
            self.logger.log(
                agent_name="OWL",
                action="task_assign",
                target=task_template["title"],
                status="assigned",
                details=f"Assigned to {task_template['agent']} | Project: {title}",
            )
            created_tasks.append({
                "id": task_id,
                "title": task_template["title"],
                "agent": task_template["agent"],
                "priority": task_template["priority"],
            })

        # Log project creation
        self.logger.log(
            agent_name="OWL",
            action="project_create",
            target=title,
            status="completed",
            details=f"Project {project_id}: {len(created_tasks)} tasks, revenue: {template['revenue']}",
        )

        return {
            "project_id": project_id,
            "title": title,
            "tagline": template["tagline"],
            "revenue": template["revenue"],
            "build_weeks": template["build_weeks"],
            "tasks_created": len(created_tasks),
            "tasks": created_tasks,
        }

    def get_pipeline_status(self) -> list:
        """Get all active projects and their task status."""
        tasks = self.logger.get_tasks()
        if not tasks:
            return []

        # Group by project
        projects = {}
        for t in tasks:
            task_id = t["id"]
            # Extract project prefix (proj-KEY-TIMESTAMP)
            parts = task_id.split("-task-")
            if len(parts) == 2:
                proj_key = parts[0]
            else:
                proj_key = "other"

            if proj_key not in projects:
                projects[proj_key] = {
                    "project_id": proj_key,
                    "tasks": [],
                    "total": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "blocked": 0,
                    "backlog": 0,
                    "assigned": 0,
                }
            projects[proj_key]["tasks"].append(t)
            projects[proj_key]["total"] += 1
            status = t.get("status", "backlog")
            if status in projects[proj_key]:
                projects[proj_key][status] += 1

        return list(projects.values())

    def get_agent_workload(self) -> dict:
        """Get current task load per agent."""
        tasks = self.logger.get_tasks()
        agents = {}
        for t in tasks:
            agent = t.get("assigned_to", "Unassigned")
            if agent not in agents:
                agents[agent] = {"total": 0, "in_progress": 0, "assigned": 0, "completed": 0, "blocked": 0, "tasks": []}
            agents[agent]["total"] += 1
            status = t.get("status", "backlog")
            if status in agents[agent]:
                agents[agent][status] += 1
            agents[agent]["tasks"].append({
                "id": t["id"],
                "title": t["title"],
                "status": status,
                "priority": t.get("priority", "normal"),
            })
        return agents

    def mark_task_done(self, task_id: str) -> None:
        self.logger.update_task(task_id, "completed")
        self.logger.log("OWL", "task_complete", task_id, "completed")

    def mark_task_blocked(self, task_id: str, reason: str) -> None:
        self.logger.update_task(task_id, "blocked")
        self.logger.log("OWL", "task_blocked", task_id, "blocked", reason)

    def assign_task(self, task_id: str, agent: str) -> None:
        self.logger.update_task(task_id, assigned_to=agent)
        self.logger.log("OWL", "task_reassign", task_id, "assigned", f"Now assigned to {agent}")


def format_project_summary(result: dict) -> str:
    """Format a project creation result for Slack/console output."""
    if "error" in result:
        return f"❌ {result['error']}"

    lines = [
        f"🚀 *Project Created: {result['title']}*",
        f"_{result['tagline']}_",
        f"",
        f"📊 Revenue: {result['revenue']} | Build: {result['build_weeks']} weeks",
        f"📋 Tasks created: {result['tasks_created']}",
        f"",
        f"*Task Breakdown:*",
    ]

    # Group by agent
    by_agent = {}
    for t in result["tasks"]:
        agent = t["agent"]
        if agent not in by_agent:
            by_agent[agent] = []
        by_agent[agent].append(t)

    for agent, tasks in by_agent.items():
        lines.append(f"  *{agent}* ({len(tasks)} tasks):")
        for t in tasks:
            priority = {"high": "🔴", "normal": "🟡", "low": "🟢"}.get(t["priority"], "🟡")
            lines.append(f"    {priority} `{t['id']}` — {t['title']}")

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIdentify Pipeline Manager")
    parser.add_argument("--list", action="store_true", help="List available opportunities")
    parser.add_argument("--create", type=str, help="Create project from opportunity key")
    parser.add_argument("--custom-title", type=str, help="Custom project title")
    parser.add_argument("--status", action="store_true", help="Show pipeline status")
    parser.add_argument("--agent-work", action="store_true", help="Show agent workload")
    parser.add_argument("--complete", type=str, help="Mark task complete by ID")
    parser.add_argument("--block", type=str, nargs=2, metavar=("TASK_ID", "REASON"), help="Mark task blocked")

    args = parser.parse_args()
    pm = PipelineManager()

    if args.list:
        print("📋 Available Opportunities:")
        print()
        for key, template in OPPORTUNITY_TEMPLATES.items():
            print(f"  *{key}* — {template['title']}")
            print(f"    {template['tagline']}")
            print(f"    Revenue: {template['revenue']} | Build: {template['build_weeks']} weeks | Tasks: {len(template['tasks'])}")
            print()

    elif args.create:
        result = pm.create_project(args.create, args.custom_title)
        print(format_project_summary(result))

    elif args.status:
        projects = pm.get_pipeline_status()
        if not projects:
            print("No active projects. Use --create to start one.")
        else:
            for p in projects:
                done = p["completed"]
                total = p["total"]
                pct = (done / total * 100) if total > 0 else 0
                print(f"📊 {p['project_id']}: {done}/{total} tasks done ({pct:.0f}%)")
                print(f"  In Progress: {p['in_progress']} | Blocked: {p['blocked']} | Backlog: {p['backlog']}")
                for t in p["tasks"]:
                    status_icon = {"completed": "✅", "in_progress": "🔄", "blocked": "🚫", "assigned": "📌", "backlog": "📥"}.get(t["status"], "⚪")
                    print(f"  {status_icon} [{t['assigned_to']}] {t['title']} ({t['id']})")
                print()

    elif args.agent_work:
        workload = pm.get_agent_workload()
        if not workload:
            print("No tasks assigned yet.")
        else:
            for agent, data in workload.items():
                print(f"*{agent}* — {data['total']} tasks total")
                print(f"  In Progress: {data['in_progress']} | Assigned: {data['assigned']} | Completed: {data['completed']} | Blocked: {data['blocked']}")
                for t in data["tasks"]:
                    icon = {"completed": "✅", "in_progress": "🔄", "blocked": "🚫", "assigned": "📌", "backlog": "📥"}.get(t["status"], "⚪")
                    print(f"  {icon} {t['title']} [{t['priority']}]")
                print()

    elif args.complete:
        pm.mark_task_done(args.complete)
        print(f"✅ Task {args.complete} marked complete.")

    elif args.block:
        pm.mark_task_blocked(args.block[0], args.block[1])
        print(f"🚫 Task {args.block[0]} blocked: {args.block[1]}")

    else:
        print("AIdentify Pipeline Manager")
        print()
        print("Usage:")
        print("  python pipeline_manager.py --list                    # Show available opportunities")
        print("  python pipeline_manager.py --create compliance       # Create compliance project")
        print("  python pipeline_manager.py --create orchestration    # Create orchestration project")
        print("  python pipeline_manager.py --status                  # Show all active projects")
        print("  python pipeline_manager.py --agent-work              # Show per-agent workload")
        print("  python pipeline_manager.py --complete <task_id>      # Mark task done")
        print("  python pipeline_manager.py --block <task_id> <reason> # Mark task blocked")

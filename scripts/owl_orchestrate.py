"""
OWL Orchestrator — Task delegation and inter-agent workflow engine.

This is how OWL coordinates the agent swarm:
1. OWL receives a task (from Phani or from a cron)
2. OWL breaks it down and delegates to the right agent(s)
3. Each agent works and posts updates to the War Room
4. OWL tracks progress and reports back to Phani

Usage:
    python3 owl_orchestrate.py --task "Build rate limiter" --assign coder
    python3 owl_orchestrate.py --sprint-review
    python3 owl_orchestrate.py --daily-standup
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from war_room import WarRoom, AgentPersona, AGENT_EMOJI


# Agent capabilities — which agent handles what type of task
AGENT_CAPABILITIES = {
    "research": AgentPersona.RESEARCHER,
    "code": AgentPersona.CODER,
    "review": AgentPersona.REVIEWER,
    "plan": AgentPersona.PLANNER,
    "social": AgentPersona.SOCIAL,
    "outreach": AgentPersona.OUTREACH,
    "data": AgentPersona.DPI_LS,
    "default": AgentPersona.OWL,
}

# Active agent profiles on this machine
ACTIVE_PROFILES = {
    "owl-orchestrator": AgentPersona.OWL,
    "agent-researcher": AgentPersona.RESEARCHER,
    "agent-coder": AgentPersona.CODER,
    "agent-planner": AgentPersona.PLANNER,
    "agent-reviewer": AgentPersona.REVIEWER,
    "agent-social": AgentPersona.SOCIAL,
    "agent-outreach": AgentPersona.OUTREACH,
}


def delegate_task(task: str, assignee: AgentPersona, context: str = "",
                  priority: str = "normal") -> dict:
    """
    OWL delegates a task to an agent and posts to War Room.
    Returns the Slack API response.
    """
    wr = WarRoom()
    
    # OWL announces the delegation
    priority_emoji = {"high": "🔴", "normal": "🟡", "low": "🟢"}.get(priority, "🟡")
    assignee_name = assignee.value[0]
    
    owl_msg = f"{priority_emoji} *New Task Assigned*\n\n"
    owl_msg += f"*To:* {assignee_name}\n"
    owl_msg += f"*Priority:* {priority.upper()}\n"
    owl_msg += f"*Task:* {task}\n"
    if context:
        owl_msg += f"*Context:* {context}\n"
    
    r = wr.post(AgentPersona.OWL, owl_msg, task_ref=task, status="[ASSIGNED]")
    print(f"OWL delegation posted: {r.get('ok')}")
    
    # Post handoff
    r2 = wr.post_handoff(AgentPersona.OWL, assignee, task, context)
    print(f"Handoff posted: {r2.get('ok')}")
    
    return r


def agent_acknowledge(agent: AgentPersona, task: str, eta: str = "") -> dict:
    """An agent acknowledges a task assignment."""
    wr = WarRoom()
    msg = f"Acknowledged. Starting work on: {task}"
    if eta:
        msg += f"\nETA: {eta}"
    return wr.post(agent, msg, task_ref=task, status="[ACKNOWLEDGED]")


def agent_update(agent: AgentPersona, task: str, update: str,
                 status: str = "[IN_PROGRESS]") -> dict:
    """An agent posts a progress update."""
    wr = WarRoom()
    return wr.post(agent, update, task_ref=task, status=status)


def agent_complete(agent: AgentPersona, task: str, summary: str = "") -> dict:
    """An agent marks a task complete."""
    wr = WarRoom()
    msg = f"Task complete."
    if summary:
        msg += f"\n{summary}"
    return wr.post(agent, msg, task_ref=task, status="[DONE]")


def agent_blocked(agent: AgentPersona, task: str, reason: str) -> dict:
    """An agent reports being blocked."""
    wr = WarRoom()
    return wr.post(agent, f"Blocked: {reason}", task_ref=task, status="[BLOCKED]")


def daily_standup() -> dict:
    """Post a daily standup summary to the War Room."""
    wr = WarRoom()
    
    standup_text = "☀️ *Daily Standup*\n\n"
    standup_text += "Please post your updates:\n"
    for persona in [AgentPersona.RESEARCHER, AgentPersona.CODER, 
                    AgentPersona.PLANNER, AgentPersona.REVIEWER]:
        name = persona.value[0]
        standup_text += f"• {name} — yesterday / today / blockers\n"
    
    return wr.post(AgentPersona.OWL, standup_text, status="[STANDUP]")


def sprint_review(sprint_num: int, completed: list, in_progress: list,
                  blocked: list) -> dict:
    """Post a sprint review to the War Room."""
    wr = WarRoom()
    
    text = f"📋 *Sprint {sprint_num} Review*\n\n"
    
    if completed:
        text += f"*Completed ({len(completed)}):*\n"
        for t in completed:
            text += f"  ✅ {t}\n"
        text += "\n"
    
    if in_progress:
        text += f"*In Progress ({len(in_progress)}):*\n"
        for t in in_progress:
            text += f"  🔄 {t}\n"
        text += "\n"
    
    if blocked:
        text += f"*Blocked ({len(blocked)}):*\n"
        for t in blocked:
            text += f"  🚫 {t}\n"
    
    return wr.post(AgentPersona.PLANNER, text, task_ref=f"Sprint {sprint_num}", status="[REVIEW]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OWL Orchestrator")
    parser.add_argument("--task", type=str, help="Task description")
    parser.add_argument("--assign", type=str, help="Agent to assign (coder/researcher/reviewer/planner)")
    parser.add_argument("--context", type=str, default="", help="Additional context")
    parser.add_argument("--priority", type=str, default="normal", choices=["high", "normal", "low"])
    parser.add_argument("--daily-standup", action="store_true", help="Post daily standup")
    parser.add_argument("--sprint-review", action="store_true", help="Post sprint review")
    
    args = parser.parse_args()
    wr = WarRoom()
    
    if args.daily_standup:
        r = daily_standup()
        print(f"Standup posted: {r.get('ok')}")
    
    elif args.sprint_review:
        # Example sprint review
        r = sprint_review(
            sprint_num=6,
            completed=["Rate limiting middleware", "Auth flow refactor", "Landing page v2"],
            in_progress=["Email bounce monitor", "Social dedup fix"],
            blocked=["Instagram image gen — no free API"]
        )
        print(f"Sprint review posted: {r.get('ok')}")
    
    elif args.task and args.assign:
        agent_key = args.assign.lower()
        persona = AGENT_CAPABILITIES.get(agent_key, AgentPersona.OWL)
        r = delegate_task(args.task, persona, args.context, args.priority)
        print(f"Task delegated: {r.get('ok')}")
    
    elif args.task:
        # Just post the task to the war room for discussion
        r = wr.post(AgentPersona.OWL, f"📌 *New Task:* {args.task}\n\nWho should take this?",
                     task_ref=args.task, status="[OPEN]")
        print(f"Task posted: {r.get('ok')}")
    
    else:
        # Default: show war room status
        print("AgentsFactory War Room — OWL Orchestrator")
        print(f"Channel: {wr.CHANNEL_NAME}")
        print(f"\nActive agents:")
        for name, persona in ACTIVE_PROFILES.items():
            p_name, role, desc = persona.value
            print(f"  {p_name} — {role} ({name})")
        print(f"\nAll 7 agents active. No pending agents.")
        print(f"\nUsage:")
        print(f"  python3 owl_orchestrate.py --task 'Fix auth bug' --assign coder --priority high")
        print(f"  python3 owl_orchestrate.py --daily-standup")
        print(f"  python3 owl_orchestrate.py --sprint-review")

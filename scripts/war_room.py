"""
AgentsFactory War Room — Inter-agent communication hub.

Each agent posts to #agentsfactory-war-room with their own persona.
OWL orchestrates task handoffs between agents.

Usage:
    from war_room import WarRoom, AgentPersona
    
    wr = WarRoom()
    wr.post(AgentPersona.OWL, "Starting Sprint 6 review...")
    wr.post(AgentPersona.CODER, "[IN_PROGRESS] Rate limiting middleware")
    wr.post(AgentPersona.REVIEWER, "[APPROVED] PR #247 — clean, no issues")
"""

import json
import os
import sys
import urllib.request
from enum import Enum
from datetime import datetime

# Add scripts dir to path for agent_activity
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from agent_activity import ActivityLogger
    _activity = ActivityLogger()
except Exception:
    _activity = None


class AgentPersona(Enum):
    """Each agent has a display name, emoji icon, and role description."""
    OWL = ("🦉 OWL", "Orchestrator", "Coordinates all agents, assigns tasks, tracks progress")
    RESEARCHER = ("🔬 Researcher", "Research", "Market research, competitive analysis, data gathering")
    CODER = ("💻 Coder", "Development", "Feature implementation, bug fixes, code review")
    PLANNER = ("📋 Planner", "Planning", "Sprint planning, task breakdown, estimation")
    REVIEWER = ("🔍 Reviewer", "QA/Review", "Code review, quality gates, approval")
    SOCIAL = ("📱 Social", "Social Media", "Content creation, posting, engagement")
    OUTREACH = ("📧 Outreach", "Lead Outreach", "Email campaigns, lead nurturing")
    DPI_LS = ("📊 DPI-LS", "Scoring Engine", "Data validation, metric computation")


# Slack emoji per agent for message icon_url fallback
AGENT_EMOJI = {
    AgentPersona.OWL: "owl",
    AgentPersona.RESEARCHER: "microscope",
    AgentPersona.CODER: "computer",
    AgentPersona.PLANNER: "clipboard",
    AgentPersona.REVIEWER: "mag",
    AgentPersona.SOCIAL: "iphone",
    AgentPersona.OUTREACH: "email",
    AgentPersona.DPI_LS: "bar_chart",
}


class WarRoom:
    """Posts messages to the AgentsFactory War Room Slack channel."""
    
    CHANNEL_ID = "C0BC2HB2T33"
    CHANNEL_NAME = "#agentsfactory-war-room"
    
    def __init__(self, token: str = None):
        env_path = os.path.join(os.path.expanduser('~'), '.hermes', '.env')
        if token is None:
            with open(env_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='replace')
            for line in content.split('\n'):
                line = line.strip().replace('\x00', '').replace('\r', '')
                prefix = 'SLACK_BOT_TOKEN'
                cprefix = 'SLACK_BOT_TOKEN_C'
                if line.startswith(prefix + '=') and not line.startswith(cprefix):
                    token = line.split('=', 1)[1].strip()
                    break
        if not token:
            raise ValueError("SLACK_BOT_TOKEN not found in ~/.hermes/.env")
        self.token = token
    
    def _api(self, method: str, data: dict) -> dict:
        url = f"https://slack.com/api/{method}"
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers={
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        })
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    
    def post(self, persona: AgentPersona, message: str, 
             task_ref: str = None, status: str = None) -> dict:
        """
        Post a message to the war room as a specific agent.
        
        Args:
            persona: Which agent is posting
            message: The message content
            task_ref: Optional task reference (e.g., "PR #247", "Sprint 6")
            status: Optional status tag (e.g., [IN_PROGRESS], [APPROVED], [BLOCKED])
        """
        name, role, _ = persona.value
        emoji = AGENT_EMOJI.get(persona, "robot_face")
        
        # Build the message with agent header
        header = f"{name}"
        if status:
            header += f" {status}"
        if task_ref:
            header += f" — `{task_ref}`"
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{header}*\n{message}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f":{emoji}: {role} | {datetime.now().strftime('%d %b %H:%M IST')}"
                    }
                ]
            },
            {"type": "divider"}
        ]
        
        result = self._api("chat.postMessage", {
            "channel": self.CHANNEL_ID,
            "text": f"{header}\n{message}",  # fallback for notifications
            "blocks": blocks,
            "username": name,
            "icon_emoji": f":{emoji}:"
        })

        # Log to activity DB
        if _activity:
            try:
                _activity.log_war_room(
                    agent_name=name,
                    message=message[:500],
                    task_ref=task_ref or "",
                    status_tag=status or "",
                    slack_ts=result.get("ts", ""),
                )
                _activity.log(
                    agent_name=name,
                    action="war_room_post",
                    target=task_ref or "",
                    status="completed",
                    details=message[:200],
                )
            except Exception:
                pass

        return result
    
    def post_handoff(self, from_agent: AgentPersona, to_agent: AgentPersona,
                     task: str, context: str = "") -> dict:
        """Post a task handoff from one agent to another."""
        from_name = from_agent.value[0]
        to_name = to_agent.value[0]
        
        message = f"📤 *Handoff: {from_name} → {to_name}*\n\n"
        message += f"*Task:* {task}\n"
        if context:
            message += f"*Context:* {context}\n"
        message += f"\n{to_name}, please acknowledge and begin."
        
        return self._api("chat.postMessage", {
            "channel": self.CHANNEL_ID,
            "text": message,
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": message}
                },
                {"type": "divider"}
            ]
        })
    
    def post_status_update(self, active_tasks: list, completed: list = None,
                           blocked: list = None) -> dict:
        """Post a full status update (like a daily standup)."""
        text = "📊 *War Room Status Update*\n\n"
        
        if active_tasks:
            text += "*In Progress:*\n"
            for t in active_tasks:
                text += f"  • {t}\n"
            text += "\n"
        
        if completed:
            text += "*Completed:*\n"
            for t in completed:
                text += f"  ✅ {t}\n"
            text += "\n"
        
        if blocked:
            text += "*Blocked:*\n"
            for t in blocked:
                text += f"  🚫 {t}\n"
        
        return self._api("chat.postMessage", {
            "channel": self.CHANNEL_ID,
            "text": text,
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": text}
                },
                {"type": "divider"}
            ]
        })
    
    def get_history(self, limit: int = 20) -> list:
        """Get recent messages from the war room."""
        result = self._api("conversations.history", {
            "channel": self.CHANNEL_ID,
            "limit": limit
        })
        return result.get("messages", [])


# Convenience functions for quick posting
def quick_post(agent: str, message: str, **kwargs):
    """Quick post by agent name string."""
    persona_map = {p.name.lower(): p for p in AgentPersona}
    persona = persona_map.get(agent.lower())
    if not persona:
        raise ValueError(f"Unknown agent: {agent}. Available: {list(persona_map.keys())}")
    wr = WarRoom()
    return wr.post(persona, message, **kwargs)


if __name__ == "__main__":
    # Test: post from each active agent
    wr = WarRoom()
    
    print("Testing War Room posts...")
    
    r = wr.post(AgentPersona.OWL, 
                "War Room is online. All agents will communicate here.",
                status="[ONLINE]")
    print(f"OWL: {r.get('ok')} ts={r.get('ts','')}")
    
    r = wr.post(AgentPersona.RESEARCHER,
                "Sprint 6 competitive analysis queued. Scanning 12 competitors.",
                task_ref="Sprint 6",
                status="[QUEUED]")
    print(f"Researcher: {r.get('ok')} ts={r.get('ts','')}")
    
    r = wr.post(AgentPersona.CODER,
                "Starting rate limiting middleware implementation.",
                task_ref="PR #248",
                status="[IN_PROGRESS]")
    print(f"Coder: {r.get('ok')} ts={r.get('ts','')}")
    
    r = wr.post(AgentPersona.REVIEWER,
                "PR #247 reviewed. Clean code, all tests passing.",
                task_ref="PR #247",
                status="[APPROVED]")
    print(f"Reviewer: {r.get('ok')} ts={r.get('ts','')}")
    
    r = wr.post(AgentPersona.PLANNER,
                "Sprint 6 backlog groomed. 20 tasks prioritized.",
                task_ref="Sprint 6",
                status="[DONE]")
    print(f"Planner: {r.get('ok')} ts={r.get('ts','')}")
    
    print("\nDone! Check #agentsfactory-war-room in Slack.")

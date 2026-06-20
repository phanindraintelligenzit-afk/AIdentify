"""
AgentsFactory Slack Alert Module — reusable error/alert notifications.
Uses urllib (no extra dependencies). Never crashes the calling script.
"""
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone


def send_alert(channel, text):
    """
    Post a message to a Slack channel via chat.postMessage API.
    Uses SLACK_BOT_TOKEN from environment.
    Returns True if sent, False if failed. Never raises.
    """
    try:
        token = os.environ.get("SLACK_BOT_TOKEN", "")
        if not token:
            print("  ⚠️  SLACK_BOT_TOKEN not set — alert not sent")
            return False

        url = "https://slack.com/api/chat.postMessage"
        body = json.dumps({"channel": channel, "text": text}).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                return True
            else:
                print(f"  ⚠️  Slack API error: {data.get('error', 'unknown')}")
                return False
    except urllib.error.HTTPError as e:
        print(f"  ⚠️  Slack HTTP error: {e.code} {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"  ⚠️  Slack URL error: {e.reason}")
        return False
    except Exception as e:
        print(f"  ⚠️  send_alert failed: {e}")
        return False


def format_error_alert(script_name, error_msg, details):
    """
    Format a readable Slack alert message for script errors.
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        f"🚨 *AgentsFactory Alert*\n"
        f"Script: {script_name}\n"
        f"Error: {error_msg}\n"
        f"Time: {ts}\n"
        f"Details: {details}"
    )

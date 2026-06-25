"""
Daily DPI-LS Status Report — pulls Notion data, formats summary, posts to Slack.
"""
import json, os, sys, time, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))

# Load .env
_env_file = Path.home() / ".hermes" / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ[_k.strip()] = _v.strip()  # force set, not default

# Also load project .env
_env_file2 = Path("C:/Users/Admin/Projects/AgentsFactory/.env")
if _env_file2.exists():
    for _line in _env_file2.read_text().splitlines():
        _line = _line.strip()
        if _line and "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ[_k.strip()] = _v.strip()

NOTION_KEY = os.environ.get("NOTION_API_KEY", "")
SLACK_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = "C0BBP317H7G"  # #phani-ai (bot's confirmed channel)

# Slack alerts
sys.path.insert(0, str(Path("C:/Users/Admin/Projects/AgentsFactory/scripts")))
from slack_alert import send_alert, format_error_alert

def notion(method, path, data=None):
    url = f"https://api.notion.com/v1{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {NOTION_KEY}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Notion-Version", "2022-06-28")
    last_err = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_err = e
            print(f"    ⚠️  Notion API attempt {attempt}/3 failed: {e}")
            if attempt < 3:
                time.sleep(5)
    raise last_err

def slack_post(text):
    url = "https://slack.com/api/chat.postMessage"
    body = json.dumps({"channel": SLACK_CHANNEL, "text": text}).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {SLACK_TOKEN}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def get_title(page):
    props = page.get("properties", {})
    for name in ["Task", "Name", "Title"]:
        if name in props:
            arr = props[name].get("title", [])
            if arr:
                return arr[0].get("plain_text", "?")
    return "?"

def get_status(page):
    props = page.get("properties", {})
    if "Status" in props:
        s = props["Status"]
        if s.get("type") == "status":
            return s.get("status", {}).get("name", "")
        if s.get("type") == "select":
            sel = s.get("select")
            return sel.get("name", "") if sel else ""
    return ""

def main():
    now = datetime.now(IST)
    today = now.strftime("%Y-%m-%d")
    print(f"=== DPI-LS Daily Report — {today} ===\n")

    try:
        # Fetch all DPI-LS pages
        res = notion("POST", "/search", {"query": "DPI-LS", "filter": {"value": "page", "property": "object"}})
        pages = res.get("results", [])

        # Group by component
        components = {}
        for p in pages:
            title = get_title(p)
            status = get_status(p)
            url = f"https://notion.so/{p['id'].replace('-','')}"
            # Skip non-component pages (like LSKDM, LS Digital Pvt Ltd)
            if "DPI-LS" not in title and "dFTE" not in title:
                continue
            # Extract component letter
            comp = "?"
            for letter in ["P —", "Q —", "E —", "G —", "R —", "V —", "C —", "Productivity", "Quality", "Efficiency", "Governance", "Risk", "Validation", "Cost"]:
                if letter in title:
                    if "Productivity" in letter or "P —" in letter: comp = "P"
                    elif "Quality" in letter or "Q —" in letter: comp = "Q"
                    elif "Efficiency" in letter or "E —" in letter: comp = "E"
                    elif "Governance" in letter or "G —" in letter: comp = "G"
                    elif "Risk" in letter or "R —" in letter: comp = "R"
                    elif "Validation" in letter or "V —" in letter: comp = "V"
                    elif "Cost" in letter or "C —" in letter: comp = "C"
                    break
            if comp not in components:
                components[comp] = []
            components[comp].append({"title": title, "status": status, "url": url})

        # Build report
        comp_names = {"P": "Productivity", "Q": "Quality", "E": "Efficiency", "G": "Governance", "R": "Risk", "V": "Validation", "C": "Cost"}
        lines = [f"📊 *DPI-LS Daily Report — {today}*\n"]
        for letter in ["P", "Q", "E", "G", "R", "V", "C"]:
            items = components.get(letter, [])
            name = comp_names.get(letter, letter)
            if not items:
                lines.append(f"*{letter} — {name}*: No pages found")
            else:
                status_counts = {}
                for item in items:
                    s = item["status"] or "?"
                    status_counts[s] = status_counts.get(s, 0) + 1
                status_str = ", ".join(f"{s}: {c}" for s, c in status_counts.items())
                lines.append(f"*{letter} — {name}* ({len(items)} pages): {status_str}")
                for item in items:
                    icon = "✅" if item["status"] == "Done" else ("🔄" if item["status"] == "In Progress" else "🔲")
                    lines.append(f"  {icon} {item['title'][:60]} | {item['url']}")

        report = "\n".join(lines)
        print(report)

        # Post to Slack
        if SLACK_TOKEN:
            r = slack_post(report)
            if r.get("ok"):
                print("\n✅ Posted to Slack #all-intelligenzit-chandra")
            else:
                print(f"\n❌ Slack error: {r.get('error')}")
        else:
            print("\n⚠️ No Slack token — report not posted")

    except Exception as e:
        send_alert("C0BBP317H7G", format_error_alert("daily_report.py", str(e), f"Date: {today}"))
        print(f"\n❌ Fatal error: {e}")

if __name__ == "__main__":
    main()

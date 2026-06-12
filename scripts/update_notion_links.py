import subprocess, json

def get_api_key():
    with open(r"C:\Users\Admin\.hermes\.env") as f:
        for line in f:
            line = line.strip()
            if "NOTION_API_KEY" in line and "=" in line:
                return line.split("=", 1)[1].strip()
    raise ValueError("NOTION_API_KEY not found")

PAGE_ID = "37d4baec-8165-81a7a0e1de4593503d35"
api_key = get_api_key()

content = """# AgentsFactory - Quick Links

## Live Tools
- **Command Center Dashboard** — http://localhost:8501 (local, run: `uv run streamlit run src/agentkit/observability/command_center.py`)
- **Landing Page (LIVE)** — https://phanindraintelligenzit-afk.github.io/AgentsFactory/landing/
- **GitHub Repo** — https://github.com/phanindraintelligenzit-afk/AgentsFactory

## Notion Databases
- **Leads** — https://notion.so/37d4baec816581feab68d2c3c347589d
- **Clients** — https://notion.so/37d4baec81658165acbbde53265bcf32
- **Projects** — https://notion.so/37d4baec8165813eb25adb2db16d9f1a
- **Content Calendar** — https://notion.so/37d4baec816581ff870cc12525b08054
- **Automation Health** — https://notion.so/37d4baec816581498cb5dfd76c103e24
- **Revenue** — https://notion.so/37d4baec81658118ae5ee14ff7a604ed
- **Agent Activity** — https://notion.so/37d4baec81658138b971dee054effc65

## Subagents (run from project root)
- **Lead Finder** — `python src/agents/lead_finder.py --source linkedin --limit 20 --dry-run`
- **Content Writer** — `python src/agents/content_writer.py --platform linkedin --pillar tips_tutorial --count 3 --dry-run`
- **LinkedIn Agent** — `python src/agents/linkedin_agent.py --action status`
- **Outreach Agent** — `python src/agents/outreach_agent.py --channel linkedin --dry-run`
- **Daily Briefing** — `python src/agents/daily_briefing.py`
- **Weekly Review** — `python src/agents/weekly_review.py`
- **Form Sync** — `python src/agents/form_sync.py`

## Key Documents
- **Services & Pricing** — docs/services.md
- **Launch Plan** — .hermes/plans/2026-06-12-agentsfactory-launch.md
- **Google Form Setup** — docs/GOOGLE_FORM_SETUP.md
- **Notion Workspace** — docs/notion-workspace.md

## Forms & Integrations
- **Landing Page Form** — Formspree: https://formspree.io/f/xlgkpzeo
- **Google Form Guide** — docs/GOOGLE_FORM_SETUP.md

## Business Info
- **Tagline:** AI Automations That Run Your Business While You Sleep
- **Pricing:** Starter $500-1K/mo | Growth $1-3K/mo | Scale $3-5K/mo
- **Early-bird:** 25% off for first 10 clients (lifetime)
- **Target:** India + US | E-commerce, SaaS, Local Business
- **Formspree:** Connected and live on landing page
"""

auth_header = "Authorization: Bearer " + api_key

payload = {
    "parent": {"page_id": "37d4baec-8165-8126-ae73-e56e6d5d235d"},
    "properties": {
        "title": [{"text": {"content": "Quick Links"}}]
    },
    "markdown": content,
}

# First delete the old page, then create new
# Actually let's just create a new updated page
cmd = [
    "curl", "-s", "-X", "POST",
    "https://api.notion.com/v1/pages",
    "-H", auth_header,
    "-H", "Notion-Version: 2022-06-28",
    "-H", "Content-Type: application/json",
    "-d", json.dumps(payload),
]
result = subprocess.run(cmd, capture_output=True, text=True)
data = json.loads(result.stdout)
page_id = data.get("id")
if page_id:
    clean_id = page_id.replace("-", "")
    print("OK - https://notion.so/" + clean_id)
else:
    print("FAIL - " + str(data))

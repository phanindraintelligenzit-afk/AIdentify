"""Customize the HTML dashboard template for AgentsFactory."""
import json, re

# Read the template
with open(r"C:\Users\Admin\Downloads\KomputerMechanic-Hermes-Dashboard-Template.html", "r", encoding="utf-8") as f:
    html = f.read()

# Read the data snapshot
with open("docs/dashboard_data.json", "r", encoding="utf-8") as f:
    snapshot = json.load(f)

# 1. Replace title
html = html.replace(
    "Hermes / Orchestrator Mission Control — Hardcoded Static Export",
    "AgentsFactory — Business Command Center"
)

# 2. Replace brand name in nav
html = html.replace(">Hermes<", ">AgentsFactory<")
html = html.replace("/ Orchestrator", "/ Command Center")
html = html.replace("v2.5 static", "v1.0")

# 3. Replace overview eyebrow text
html = html.replace("Hermes Orchestrator", "AgentsFactory")
html = html.replace("v2.0 · Awaiting telemetry", "v1.0 · Static Export")

# 4. Replace agents section heading
html = html.replace("The collective.", "AI Agent Workforce")

# 5. Replace tasks section heading
html = html.replace("Task board.", "Execution Board")

# 6. Replace schedule section heading
html = html.replace("Schedule.", "Automation Schedule")

# 7. Replace content section heading
html = html.replace("Library.", "Content Library")

# 8. Replace the STATIC_SNAPSHOT
# Find the old snapshot and replace with ours
old_snapshot_match = re.search(r'const STATIC_SNAPSHOT=(\{.*?\});', html, re.DOTALL)
if old_snapshot_match:
    new_snapshot = json.dumps(snapshot, indent=2, default=str)
    html = html[:old_snapshot_match.start()] + "const STATIC_SNAPSHOT=" + new_snapshot + ";" + html[old_snapshot_match.end():]
    print(f"Replaced STATIC_SNAPSHOT ({len(old_snapshot_match.group(1))} -> {len(new_snapshot)} chars)")
else:
    print("WARNING: Could not find STATIC_SNAPSHOT")

# 9. Replace STATIC_BOARD_TASKS with our tasks
our_tasks = [
    {"id": "t1", "title": "Fix X/Twitter posting errors", "status": "done", "priority": "high", "notes": "3 Twitter posts were erroring — fixed multi-platform agent", "created_at": "2026-06-13T12:00:00Z"},
    {"id": "t2", "title": "Instagram media pipeline", "status": "done", "priority": "high", "notes": "Branded image generation for Instagram posts", "created_at": "2026-06-13T13:00:00Z"},
    {"id": "t3", "title": "Notion lead sync — skip, use SQLite", "status": "done", "priority": "high", "notes": "Decided to use SQLite + Google Sheets as source of truth", "created_at": "2026-06-13T14:00:00Z"},
    {"id": "t4", "title": "Customize HTML dashboard for AgentsFactory", "status": "in_progress", "priority": "high", "notes": "Adapting KomputerMechanic template with real data", "created_at": "2026-06-13T15:00:00Z"},
    {"id": "t5", "title": "Lead outreach automation", "status": "pending", "priority": "medium", "notes": "Build multi-channel outreach sequence", "created_at": "2026-06-12T10:00:00Z"},
    {"id": "t6", "title": "A/B test content tracking", "status": "pending", "priority": "low", "notes": "Track which posts get more engagement", "created_at": "2026-06-11T09:00:00Z"},
    {"id": "t7", "title": "Multi-platform social posting", "status": "done", "priority": "high", "notes": "LinkedIn + X + Facebook + Instagram all working", "created_at": "2026-06-13T16:00:00Z"},
    {"id": "t8", "title": "Command Center dashboard", "status": "done", "priority": "high", "notes": "Streamlit dashboard with 8 pages + Kanban", "created_at": "2026-06-12T08:00:00Z"},
    {"id": "t9", "title": "Self-cloning backup system", "status": "done", "priority": "medium", "notes": "GitHub repo with bootstrap.sh, Dockerfile, CI/CD", "created_at": "2026-06-12T14:00:00Z"},
    {"id": "t10", "title": "Lead scoring + segmentation", "status": "pending", "priority": "medium", "notes": "Score leads by location, size, engagement quality", "created_at": "2026-06-11T11:00:00Z"},
]

old_board_match = re.search(r'const STATIC_BOARD_TASKS=(\[.*?\]);', html, re.DOTALL)
if old_board_match:
    new_board = json.dumps(our_tasks, indent=2)
    html = html[:old_board_match.start()] + "const STATIC_BOARD_TASKS=" + new_board + ";" + html[old_board_match.end():]
    print(f"Replaced STATIC_BOARD_TASKS ({len(old_board_match.group(1))} -> {len(new_board)} chars)")
else:
    print("WARNING: Could not find STATIC_BOARD_TASKS")

# 10. Replace ACCENTS color map for our agents
old_accents = "const ACCENTS={orchestrator:'#A78BFA',scout:'#7DD3FC',scribe:'#F472B6',reach:'#E879F9',dev:'#A78BFA'}"
new_accents = "const ACCENTS={orchestrator:'#A78BFA',scout:'#7DD3FC',scribe:'#F472B6',reach:'#E879F9',dev:'#A78BFA',builder:'#5EE2B5',monitor:'#F26D6D',reporter:'#FBBF24',outreach:'#F5B544'}"
html = html.replace(old_accents, new_accents)

# 11. Replace AGENT_META with our agents
old_meta = re.search(r'const AGENT_META=(\{.*?\});', html, re.DOTALL)
if old_meta:
    new_meta = {
        "orchestrator": {"code": "ORCH", "name": "Orchestrator", "platform": "Telegram", "role": "Top-level coordinator routing work across all agents."},
        "scout": {"code": "SCNT", "name": "Lead Finder", "platform": "Web", "role": "Scans LinkedIn, Twitter, Reddit, Google Maps for prospects."},
        "scribe": {"code": "SCRB", "name": "Content Writer", "platform": "AI", "role": "Drafts LinkedIn posts, tweets, newsletters, blogs."},
        "reach": {"code": "RECH", "name": "Outreach Agent", "platform": "Multi", "role": "Sends personalized DMs and emails to leads."},
        "dev": {"code": "DEV", "name": "Builder", "platform": "Code", "role": "Builds automations, dashboards, and integrations."},
    }
    new_meta_str = json.dumps(new_meta, indent=2)
    html = html[:old_meta.start()] + "const AGENT_META=" + new_meta_str + ";" + html[old_meta.end():]
    print("Replaced AGENT_META")

# 12. Replace "Hermes DBs" label
html = html.replace("Hermes DBs", "AgentsFactory DB")
html = html.replace("Hermes Gateway", "Gateway Status")

# 13. Replace "All systems operational" 
html = html.replace("All systems operational", "AgentsFactory Online")

# 14. Remove the external script references (flock.js, events.js) since we're static
html = html.replace('<script defer src="/~flock.js" data-proxy-url="/~api/analytics"></script>', '<!-- analytics removed -->')
html = html.replace(re.search(r'<script defer src="/__l5e/events\.js".*?</script>', html, re.DOTALL).group(0) if re.search(r'<script defer src="/__l5e/events\.js".*?</script>', html, re.DOTALL) else "", '<!-- events removed -->')

# 15. Remove og:image meta tags (they reference external URLs)
html = re.sub(r'<meta property="og:image".*?/>', '', html)
html = re.sub(r'<meta name="twitter:image".*?/>', '', html)

# Write the customized file
output_path = r"C:\Users\Admin\Projects\AgentsFactory\docs\agentsfactory-dashboard.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ Customized dashboard saved to: {output_path}")
print(f"File size: {len(html):,} bytes")

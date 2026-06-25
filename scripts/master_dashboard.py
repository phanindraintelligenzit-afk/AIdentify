"""
AgentsFactory Master Dashboard — Modern Kanban Board for managing agents and tasks.

Uses a custom HTML/JS Kanban board with drag-and-drop, embedded in Streamlit.
Data is synced from SQLite via the ActivityLogger.

Run with:
    cd C:/Users/Admin/Projects/AgentsFactory
    uv run streamlit run scripts/master_dashboard.py --server.port 8501
"""

from __future__ import annotations

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit.components.v1 import html as st_html

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent_activity import ActivityLogger, init_activity_db
from pipeline_manager import PipelineManager, OPPORTUNITY_TEMPLATES

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgentsFactory — Kanban",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Data layer ───────────────────────────────────────────────────────────────
@st.cache_resource
def get_logger() -> ActivityLogger:
    init_activity_db()
    return ActivityLogger()

@st.cache_resource
def get_pipeline_manager() -> PipelineManager:
    return PipelineManager()

@st.cache_data(ttl=15)
def get_summary(_logger: ActivityLogger) -> dict:
    return _logger.get_summary()

@st.cache_data(ttl=15)
def get_agent_stats(_logger: ActivityLogger, hours: int) -> list:
    return _logger.get_agent_stats(hours=hours)

@st.cache_data(ttl=15)
def get_recent_activity(_logger: ActivityLogger, limit: int, hours: int) -> list:
    return _logger.get_recent_activity(limit=limit, hours=hours)

@st.cache_data(ttl=15)
def get_tasks(_logger: ActivityLogger) -> list:
    return _logger.get_tasks()

@st.cache_data(ttl=15)
def get_cron_health(_logger: ActivityLogger) -> list:
    return _logger.get_cron_health()

@st.cache_data(ttl=15)
def get_pipeline_status(_pm: PipelineManager) -> list:
    return _pm.get_pipeline_status()


# ── Kanban HTML Component ────────────────────────────────────────────────────
def render_kanban_board(tasks: list, height: int = 600) -> str:
    """Generate a modern Kanban board as HTML with drag-and-drop."""

    # Group tasks by status
    columns = {
        "backlog": {"title": "📥 Backlog", "color": "#6b7280", "tasks": []},
        "assigned": {"title": "📌 Assigned", "color": "#3b82f6", "tasks": []},
        "in_progress": {"title": "🔄 In Progress", "color": "#f59e0b", "tasks": []},
        "completed": {"title": "✅ Done", "color": "#10b981", "tasks": []},
        "blocked": {"title": "🚫 Blocked", "color": "#ef4444", "tasks": []},
    }

    for t in tasks:
        status = t.get("status", "backlog")
        if status in columns:
            priority = t.get("priority", "normal")
            priority_colors = {"high": "#ef4444", "normal": "#f59e0b", "low": "#10b981"}
            columns[status]["tasks"].append({
                "id": t.get("id", ""),
                "title": t.get("title", "Untitled"),
                "agent": t.get("assigned_to", "Unassigned"),
                "priority": priority,
                "priority_color": priority_colors.get(priority, "#f59e0b"),
            })

    columns_json = json.dumps(columns)

    return f"""
<!DOCTYPE html>
<html>
<head>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; }}

.kanban-header {{ padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; }}
.kanban-header h1 {{ font-size: 18px; font-weight: 600; color: #f1f5f9; }}
.kanban-header .stats {{ font-size: 13px; color: #94a3b8; }}

.kanban-board {{ display: flex; gap: 16px; padding: 20px; overflow-x: auto; height: {height}px; }}

.kanban-col {{
  min-width: 240px; max-width: 280px; flex: 1;
  background: #1e293b; border-radius: 12px;
  display: flex; flex-direction: column;
  border: 1px solid #334155;
}}
.col-header {{
  padding: 14px 16px; border-bottom: 1px solid #334155;
  display: flex; justify-content: space-between; align-items: center;
}}
.col-title {{ font-size: 13px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }}
.col-count {{
  background: #334155; color: #94a3b8;
  font-size: 11px; font-weight: 600;
  padding: 2px 8px; border-radius: 10px;
}}
.col-dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 8px; }}

.col-body {{ flex: 1; padding: 12px; overflow-y: auto; min-height: 100px; }}
.col-body.drag-over {{ background: rgba(59,130,246,0.1); border-radius: 8px; }}

.kanban-card {{
  background: #0f172a; border: 1px solid #334155;
  border-radius: 8px; padding: 12px; margin-bottom: 10px;
  cursor: grab; transition: all 0.15s ease;
}}
.kanban-card:hover {{ border-color: #475569; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
.kanban-card.dragging {{ opacity: 0.5; cursor: grabbing; }}

.card-title {{ font-size: 14px; font-weight: 500; color: #f1f5f9; margin-bottom: 8px; line-height: 1.3; }}
.card-footer {{ display: flex; justify-content: space-between; align-items: center; }}
.card-agent {{
  font-size: 11px; font-weight: 500; color: #60a5fa;
  background: rgba(59,130,246,0.15);
  padding: 2px 8px; border-radius: 4px;
}}
.card-priority {{
  font-size: 10px; font-weight: 600; text-transform: uppercase;
  padding: 2px 6px; border-radius: 4px;
  background: rgba(255,255,255,0.05);
}}

.empty-state {{ text-align: center; padding: 32px 16px; color: #475569; font-size: 13px; }}

/* Scrollbar */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: #475569; }}
</style>
</head>
<body>

<div class="kanban-header">
  <h1>🤖 AgentsFactory — Task Board</h1>
  <div class="stats" id="stats">Loading...</div>
</div>

<div class="kanban-board" id="board"></div>

<script>
const columns = {columns_json};

const board = document.getElementById('board');
let draggedCard = null;

function renderBoard() {{
  board.innerHTML = '';
  let totalTasks = 0;

  for (const [colId, col] of Object.entries(columns)) {{
    totalTasks += col.tasks.length;

    const colEl = document.createElement('div');
    colEl.className = 'kanban-col';
    colEl.dataset.colId = colId;

    colEl.innerHTML = `
      <div class="col-header">
        <div class="col-title">
          <span class="col-dot" style="background: ${{col.color}}"></span>
          ${{col.title}}
        </div>
        <span class="col-count">${{col.tasks.length}}</span>
      </div>
      <div class="col-body" data-col="${{colId}}">
        ${{col.tasks.length === 0 ? '<div class="empty-state">Drop tasks here</div>' : ''}}
      </div>
    `;

    const body = colEl.querySelector('.col-body');

    // Drag events for drop zone
    body.addEventListener('dragover', (e) => {{
      e.preventDefault();
      body.classList.add('drag-over');
    }});
    body.addEventListener('dragleave', () => body.classList.remove('drag-over'));
    body.addEventListener('drop', (e) => {{
      e.preventDefault();
      body.classList.remove('drag-over');
      if (draggedCard) {{
        const cardId = draggedCard.dataset.cardId;
        const fromCol = draggedCard.dataset.col;
        const toCol = colId;
        if (fromCol !== toCol) {{
          // Move card data
          const card = columns[fromCol].tasks.find(t => t.id === cardId);
          if (card) {{
            columns[fromCol].tasks = columns[fromCol].tasks.filter(t => t.id !== cardId);
            columns[toCol].tasks.push(card);
            renderBoard();
            // Notify parent
            window.parent.postMessage({{type: 'kanban-move', cardId, fromCol, toCol}}, '*');
          }}
        }}
      }}
    }});

    // Render cards
    for (const task of col.tasks) {{
      const card = document.createElement('div');
      card.className = 'kanban-card';
      card.draggable = true;
      card.dataset.cardId = task.id;
      card.dataset.col = colId;

      card.innerHTML = `
        <div class="card-title">${{task.title}}</div>
        <div class="card-footer">
          <span class="card-agent">${{task.agent}}</span>
          <span class="card-priority" style="color: ${{task.priority_color}}">${{task.priority}}</span>
        </div>
      `;

      card.addEventListener('dragstart', (e) => {{
        draggedCard = card;
        card.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
      }});
      card.addEventListener('dragend', () => {{
        card.classList.remove('dragging');
        draggedCard = null;
      }});

      body.appendChild(card);
    }}

    board.appendChild(colEl);
  }}

  document.getElementById('stats').textContent = `${{totalTasks}} tasks · ${{Object.keys(columns).length}} columns · Last updated: ${{new Date().toLocaleTimeString()}}`;
}}

renderBoard();
</script>
</body>
</html>
"""


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 AgentsFactory")
    st.markdown("*Kanban Dashboard*")
    st.divider()

    time_range = st.selectbox(
        "Time Range",
        ["Last 1 hour", "Last 4 hours", "Last 24 hours", "Last 7 days"],
        index=2,
    )
    hours_map = {"Last 1 hour": 1, "Last 4 hours": 4, "Last 24 hours": 24, "Last 7 days": 168}
    hours = hours_map[time_range]

    auto_refresh = st.checkbox("Auto-refresh (15s)", value=True)
    if auto_refresh:
        st.markdown('<meta http-equiv="refresh" content="15">', unsafe_allow_html=True)

    st.divider()

    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("### Agents")
    for emoji, name in [("🦉","OWL"),("🔬","Researcher"),("💻","Coder"),("📋","Planner"),("🔍","Reviewer"),("📱","Social"),("📧","Outreach")]:
        st.markdown(f"`{emoji}` {name}")

# ── Main ─────────────────────────────────────────────────────────────────────
logger = get_logger()
summary = get_summary(logger)

st.markdown("# 🤖 AgentsFactory")
st.markdown(f"*{datetime.now().strftime('%A, %d %B %Y %H:%M:%S IST')}*")

# ── KPIs ─────────────────────────────────────────────────────────────────────
kpi_data = [
    ("Actions Today", summary.get("total_actions_today", 0)),
    ("This Week", summary.get("total_actions_week", 0)),
    ("Active", summary.get("active_tasks", 0)),
    ("Done", summary.get("completed_tasks", 0)),
    ("Backlog", summary.get("backlog_tasks", 0)),
    ("Blocked", summary.get("blocked_tasks", 0)),
    ("Crons OK", f"{summary.get('healthy_crons',0)}/{summary.get('total_crons',0)}"),
    ("Messages", summary.get("war_room_messages_today", 0)),
]
cols = st.columns(8)
for col, (label, value) in zip(cols, kpi_data):
    col.metric(label=str(value), label_visibility="visible")
    col.caption(label)

# ── Kanban Board ─────────────────────────────────────────────────────────────
st.markdown("---")
tasks = get_tasks(logger)
kanban_html = render_kanban_board(tasks, height=500)
st_html(kanban_html, height=520, scrolling=False)

# ── Activity + Crons ────────────────────────────────────────────────────────
st.markdown("---")
ac_col, cron_col = st.columns([3, 2])

with ac_col:
    st.markdown("### 📡 Recent Activity")
    activity = get_recent_activity(logger, limit=20, hours=hours)
    if activity:
        for item in activity[:10]:
            status = item.get("status", "")
            dot = {"completed": "🟢", "in_progress": "🟡", "blocked": "🔴"}.get(status, "⚪")
            st.markdown(f"{dot} **{item['agent_name']}** — `{item.get('action','')}` → {item.get('target','') or '—'} _{item.get('created_at','')[:16]}_")
    else:
        st.info("No activity yet.")

with cron_col:
    st.markdown("### ⏰ Cron Health")
    crons = get_cron_health(logger)
    if crons:
        for cron in crons:
            status = cron.get("last_status", "unknown")
            icon = {"ok": "🟢", "error": "🔴"}.get(status, "⚪")
            total = cron.get("total_runs", 0)
            success = cron.get("total_success", 0)
            st.markdown(f"{icon} **{cron.get('name','')}** `{cron.get('schedule','')}` — {success}/{total}")
    else:
        st.info("No cron data yet.")

# ── Performance Chart ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📊 Agent Performance")
stats = get_agent_stats(logger, hours=hours)
if stats:
    df = pd.DataFrame(stats)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["agent_name"], y=df["completed"], name="Completed", marker_color="#10b981"))
    fig.add_trace(go.Bar(x=df["agent_name"], y=df["in_progress"], name="In Progress", marker_color="#f59e0b"))
    fig.add_trace(go.Bar(x=df["agent_name"], y=df["blocked"], name="Blocked", marker_color="#ef4444"))
    fig.update_layout(
        barmode="stack", height=300,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"), margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Quick Add ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### ➕ Quick Add Task")
with st.form("add_task"):
    c1, c2, c3 = st.columns(3)
    with c1:
        title = st.text_input("Title", placeholder="Task title")
    with c2:
        agent = st.selectbox("Agent", ["Coder","Researcher","Planner","Reviewer","Social","Outreach","OWL"])
    with c3:
        priority = st.selectbox("Priority", ["high","normal","low"], index=1)
    desc = st.text_area("Description", height=68)
    if st.form_submit_button("Create Task", use_container_width=True):
        if title:
            tid = f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            logger.create_task(tid, title, agent, desc, priority, "Dashboard")
            st.success(f"Task assigned to {agent}")
            st.cache_data.clear()
            st.rerun()

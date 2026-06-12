"""AgentsFactory Business Command Center.

Run with:
    uv run streamlit run src/agentkit/observability/command_center.py

This is the OPERATIONAL dashboard (not the dev observability one).
It tracks: projects, revenue, leads, content calendar, automation health, agent activity.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = Path("./agentsfactory_metrics.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_business_db() -> None:
    conn = get_db()
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS clients ("
        "id TEXT PRIMARY KEY, name TEXT NOT NULL, industry TEXT, "
        "contact_name TEXT, contact_email TEXT, contact_phone TEXT, "
        "status TEXT DEFAULT 'lead', deal_value REAL DEFAULT 0, "
        "created_at TEXT DEFAULT (datetime('now')), "
        "updated_at TEXT DEFAULT (datetime('now')), notes TEXT DEFAULT '');"
        ""
        "CREATE TABLE IF NOT EXISTS projects ("
        "id TEXT PRIMARY KEY, client_id TEXT, name TEXT NOT NULL, "
        "description TEXT DEFAULT '', status TEXT DEFAULT 'active', "
        "pipeline_id TEXT, created_at TEXT DEFAULT (datetime('now')), "
        "updated_at TEXT DEFAULT (datetime('now')), completed_at TEXT, "
        "FOREIGN KEY (client_id) REFERENCES clients(id));"
        ""
        "CREATE TABLE IF NOT EXISTS revenue ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, client_id TEXT, "
        "project_id TEXT, amount REAL NOT NULL, "
        "type TEXT DEFAULT 'one_time', status TEXT DEFAULT 'projected', "
        "description TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now')), "
        "FOREIGN KEY (client_id) REFERENCES clients(id), "
        "FOREIGN KEY (project_id) REFERENCES projects(id));"
        ""
        "CREATE TABLE IF NOT EXISTS leads ("
        "id TEXT PRIMARY KEY, name TEXT, company TEXT, email TEXT, "
        "phone TEXT, source TEXT DEFAULT 'inbound', stage TEXT DEFAULT 'new', "
        "score INTEGER DEFAULT 0, notes TEXT DEFAULT '', "
        "created_at TEXT DEFAULT (datetime('now')), "
        "updated_at TEXT DEFAULT (datetime('now')));"
        ""
        "CREATE TABLE IF NOT EXISTS content_calendar ("
        "id TEXT PRIMARY KEY, title TEXT NOT NULL, platform TEXT DEFAULT 'linkedin', "
        "status TEXT DEFAULT 'draft', scheduled_at TEXT, published_at TEXT, "
        "engagement_score REAL DEFAULT 0, notes TEXT DEFAULT '', "
        "created_at TEXT DEFAULT (datetime('now')));"
        ""
        "CREATE TABLE IF NOT EXISTS automation_health ("
        "id TEXT PRIMARY KEY, name TEXT NOT NULL, client_id TEXT, "
        "project_id TEXT, status TEXT DEFAULT 'running', last_run_at TEXT, "
        "last_error TEXT DEFAULT '', success_count INTEGER DEFAULT 0, "
        "failure_count INTEGER DEFAULT 0, uptime_pct REAL DEFAULT 100.0, "
        "notes TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now')), "
        "updated_at TEXT DEFAULT (datetime('now')));"
        ""
        "CREATE TABLE IF NOT EXISTS business_metrics ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, metric_name TEXT NOT NULL, "
        "metric_value REAL NOT NULL, metric_unit TEXT DEFAULT '', "
        "period TEXT DEFAULT 'daily', "
        "recorded_at TEXT DEFAULT (datetime('now')));"
        ""
        "CREATE TABLE IF NOT EXISTS agent_activity ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, agent_name TEXT NOT NULL, "
        "action TEXT NOT NULL, target TEXT DEFAULT '', "
        "status TEXT DEFAULT 'completed', details TEXT DEFAULT '', "
        "created_at TEXT DEFAULT (datetime('now')));"
    )
    conn.commit()
    conn.close()


def log_agent_activity(agent_name: str, action: str, target: str = "",
                       status: str = "completed", details: str = "") -> None:
    conn = get_db()
    conn.execute(
        "INSERT INTO agent_activity (agent_name, action, target, status, details) "
        "VALUES (?, ?, ?, ?, ?)",
        (agent_name, action, target, status, details),
    )
    conn.commit()
    conn.close()


def render_header():
    st.title("AgentsFactory Command Center")
    st.markdown("**AI Automation Agency — Business Operations Dashboard**")
    st.markdown(f"*Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    st.divider()


def render_kpi_overview():
    conn = get_db()
    total_clients = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    active_projects = conn.execute(
        "SELECT COUNT(*) FROM projects WHERE status='active'"
    ).fetchone()[0]
    total_revenue = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM revenue WHERE status='confirmed'"
    ).fetchone()[0]
    projected_revenue = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM revenue WHERE status='projected'"
    ).fetchone()[0]
    total_leads = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    hot_leads = conn.execute(
        "SELECT COUNT(*) FROM leads WHERE score >= 70"
    ).fetchone()[0]
    total_automations = conn.execute(
        "SELECT COUNT(*) FROM automation_health"
    ).fetchone()[0]
    healthy_automations = conn.execute(
        "SELECT COUNT(*) FROM automation_health WHERE status='running' AND uptime_pct >= 95"
    ).fetchone()[0]
    today_activity = conn.execute(
        "SELECT COUNT(*) FROM agent_activity WHERE date(created_at) = date('now')"
    ).fetchone()[0]
    conn.close()

    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    c1.metric("Clients", total_clients)
    c2.metric("Active Projects", active_projects)
    c3.metric("Revenue", f"${total_revenue:,.0f}")
    c4.metric("Projected", f"${projected_revenue:,.0f}")
    c5.metric("Hot Leads", f"{hot_leads}/{total_leads}")
    c6.metric("Automations", f"{healthy_automations}/{total_automations}")
    c7.metric("Agent Actions", today_activity)
    st.divider()


def render_quick_add():
    st.sidebar.divider()
    st.sidebar.subheader("⚡ Quick Add")

    with st.sidebar.expander("➕ Add Lead"):
        with st.form("quick_add_lead"):
            l_name = st.text_input("Name", key="qa_name")
            l_company = st.text_input("Company", key="qa_company")
            l_email = st.text_input("Email", key="qa_email")
            l_source = st.selectbox("Source", ["inbound", "outbound", "referral", "website", "social"], key="qa_source")
            l_score = st.slider("Score", 0, 100, 50, key="qa_score")
            if st.form_submit_button("Add Lead"):
                conn = get_db()
                lid = f"lead_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                conn.execute(
                    "INSERT INTO leads (id, name, company, email, source, stage, score) "
                    "VALUES (?, ?, ?, ?, ?, 'new', ?)",
                    (lid, l_name, l_company, l_email, l_source, l_score),
                )
                conn.commit()
                conn.close()
                log_agent_activity("Phani", "add_lead", l_name, "completed", f"Source: {l_source}, Score: {l_score}")
                st.success(f"Lead '{l_name}' added!")
                st.rerun()

    with st.sidebar.expander("➕ Add Content"):
        with st.form("quick_add_content"):
            c_title = st.text_input("Title", key="qa_ctitle")
            c_platform = st.selectbox("Platform", ["linkedin", "twitter", "newsletter", "youtube", "blog"], key="qa_cplatform")
            c_status = st.selectbox("Status", ["draft", "scheduled", "published"], key="qa_cstatus")
            if st.form_submit_button("Add Content"):
                conn = get_db()
                cid = f"content_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                conn.execute(
                    "INSERT INTO content_calendar (id, title, platform, status) "
                    "VALUES (?, ?, ?, ?)",
                    (cid, c_title, c_platform, c_status),
                )
                conn.commit()
                conn.close()
                log_agent_activity("Phani", "add_content", c_title, "completed", f"Platform: {c_platform}")
                st.success(f"Content '{c_title}' added!")
                st.rerun()

    with st.sidebar.expander("➕ Add Revenue"):
        with st.form("quick_add_revenue"):
            r_desc = st.text_input("Description", key="qa_rdesc")
            r_amount = st.number_input("Amount (USD)", min_value=0.0, value=500.0, key="qa_ramount")
            r_status = st.selectbox("Status", ["projected", "confirmed", "pending"], key="qa_rstatus")
            if st.form_submit_button("Add Revenue"):
                conn = get_db()
                conn.execute(
                    "INSERT INTO revenue (amount, status, description) VALUES (?, ?, ?)",
                    (r_amount, r_status, r_desc),
                )
                conn.commit()
                conn.close()
                log_agent_activity("Phani", "add_revenue", r_desc, "completed", f"${r_amount:,.0f} ({r_status})")
                st.success(f"Revenue '${r_amount:,.0f}' added!")
                st.rerun()


def render_client_projects():
    st.header("Client Projects")
    conn = get_db()
    projects = conn.execute(
        "SELECT p.*, c.name as client_name, c.industry "
        "FROM projects p LEFT JOIN clients c ON p.client_id = c.id "
        "ORDER BY p.updated_at DESC"
    ).fetchall()
    conn.close()

    if not projects:
        st.info("📋 No projects yet. Your first client project will appear here. Use Quick Add in the sidebar or wait for agent activity to populate this.")
        return

    df = pd.DataFrame([dict(p) for p in projects])
    c1, c2 = st.columns([1, 2])
    with c1:
        sc = df['status'].value_counts()
        fig = px.pie(
            values=sc.values, names=sc.index, title="Project Status",
            color=sc.index,
            color_discrete_map={"active": "#22c55e", "completed": "#3b82f6",
                       "paused": "#f59e0b", "cancelled": "#ef4444"},
        )
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        cols = [c for c in ['name', 'client_name', 'status', 'created_at'] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, height=250)
    st.divider()


def render_revenue_dashboard():
    st.header("Revenue Dashboard")
    conn = get_db()
    rev_by_status = conn.execute(
        "SELECT status, COALESCE(SUM(amount), 0) as total, COUNT(*) as count "
        "FROM revenue GROUP BY status"
    ).fetchall()
    monthly = conn.execute(
        "SELECT strftime('%Y-%m', created_at) as month, "
        "COALESCE(SUM(amount), 0) as total FROM revenue "
        "WHERE status='confirmed' GROUP BY month ORDER BY month DESC LIMIT 12"
    ).fetchall()
    top_clients = conn.execute(
        "SELECT c.name, COALESCE(SUM(r.amount), 0) as total "
        "FROM revenue r JOIN clients c ON r.client_id = c.id "
        "WHERE r.status='confirmed' GROUP BY c.id ORDER BY total DESC LIMIT 5"
    ).fetchall()
    conn.close()

    if not rev_by_status or all(r['total'] == 0 for r in rev_by_status):
        st.info("💰 No revenue tracked yet. Add your first revenue entry using Quick Add in the sidebar.")
        return

    c1, c2 = st.columns(2)
    with c1:
        if rev_by_status:
            rdf = pd.DataFrame([dict(r) for r in rev_by_status])
            fig = px.bar(
                rdf, x='status', y='total', color='status',
                title="Revenue by Status",
                labels={"total": "Amount (USD)", "status": "Status"},
                color_discrete_map={"confirmed": "#22c55e", "projected": "#3b82f6", "pending": "#f59e0b"},
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        if monthly:
            mdf = pd.DataFrame([dict(r) for r in monthly])
            fig2 = px.line(
                mdf, x='month', y='total', title="Monthly Revenue Trend",
                labels={"total": "Revenue (USD)", "month": "Month"}, markers=True,
            )
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)

    if top_clients:
        st.subheader("Top Clients by Revenue")
        tdf = pd.DataFrame([dict(c) for c in top_clients])
        tdf.columns = ['Client', 'Revenue']
        tdf['Revenue'] = tdf['Revenue'].apply(lambda x: f"${x:,.0f}")
        st.dataframe(tdf, use_container_width=True)
    st.divider()


def render_lead_pipeline():
    st.header("Lead Pipeline")
    conn = get_db()
    leads = conn.execute(
        "SELECT * FROM leads ORDER BY score DESC, created_at DESC"
    ).fetchall()
    stage_counts = conn.execute(
        "SELECT stage, COUNT(*) as count, COALESCE(SUM(score), 0) as total_score "
        "FROM leads GROUP BY stage"
    ).fetchall()
    conn.close()

    if not leads:
        st.info("🎯 No leads yet. The Lead Finder agent will populate this. Or add leads manually via Quick Add.")
        return

    df = pd.DataFrame([dict(l) for l in leads])
    c1, c2 = st.columns([1, 2])
    with c1:
        if stage_counts:
            sdf = pd.DataFrame([dict(s) for s in stage_counts])
            fig = px.funnel(sdf, x='count', y='stage', title="Lead Funnel")
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        cols = [c for c in ['name', 'company', 'stage', 'score', 'source', 'created_at'] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, height=300)
    st.divider()


def render_content_calendar():
    st.header("Content Calendar")
    conn = get_db()
    content = conn.execute(
        "SELECT * FROM content_calendar ORDER BY scheduled_at ASC"
    ).fetchall()
    conn.close()

    if not content:
        st.info("📝 No content scheduled. The Content Writer agent will populate this. Or add content via Quick Add.")
        return

    df = pd.DataFrame([dict(c) for c in content])
    c1, c2 = st.columns([1, 2])
    with c1:
        sc = df['status'].value_counts()
        fig = px.pie(
            values=sc.values, names=sc.index, title="Content Status",
            color=sc.index,
            color_discrete_map={"published": "#22c55e", "scheduled": "#3b82f6", "draft": "#f59e0b"},
        )
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        cols = [c for c in ['title', 'platform', 'status', 'scheduled_at'] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, height=250)
    st.divider()


def render_automation_health():
    st.header("Automation Health")
    conn = get_db()
    automations = conn.execute(
        "SELECT a.*, c.name as client_name, p.name as project_name "
        "FROM automation_health a "
        "LEFT JOIN clients c ON a.client_id = c.id "
        "LEFT JOIN projects p ON a.project_id = p.id "
        "ORDER BY a.uptime_pct ASC"
    ).fetchall()
    conn.close()

    if not automations:
        st.info("🤖 No automations tracked yet. Once you have client automations running, they'll appear here.")
        return

    df = pd.DataFrame([dict(a) for a in automations])
    c1, c2, c3 = st.columns(3)
    avg_uptime = df['uptime_pct'].mean() if len(df) > 0 else 0
    total_success = df['success_count'].sum() if len(df) > 0 else 0
    total_failures = df['failure_count'].sum() if len(df) > 0 else 0
    c1.metric("Avg Uptime", f"{avg_uptime:.1f}%")
    c2.metric("Total Successes", f"{total_success:,}")
    c3.metric("Total Failures", f"{total_failures:,}")

    c1, c2 = st.columns([1, 2])
    with c1:
        sc = df['status'].value_counts()
        fig = px.pie(
            values=sc.values, names=sc.index, title="Automation Status",
            color=sc.index,
            color_discrete_map={"running": "#22c55e", "paused": "#f59e0b", "error": "#ef4444"},
        )
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        cols = [c for c in ['name', 'client_name', 'status', 'uptime_pct',
                            'success_count', 'failure_count'] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, height=250)
    st.divider()


def render_agent_activity():
    st.header("🤖 Agent Activity Log")
    conn = get_db()
    activity = conn.execute(
        "SELECT * FROM agent_activity ORDER BY created_at DESC LIMIT 100"
    ).fetchall()
    conn.close()

    if not activity:
        st.info("No agent activity yet. As Hermes subagents work on your behalf, their actions will be logged here.")
        return

    df = pd.DataFrame([dict(a) for a in activity])
    df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')

    # Summary stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Actions", len(df))
    c2.metric("Active Agents", df['agent_name'].nunique())
    c3.metric("Today's Actions", len(df[df['created_at'].str.startswith(datetime.now().strftime('%Y-%m-%d'))]))

    # Activity by agent
    st.subheader("Actions by Agent")
    agent_counts = df['agent_name'].value_counts()
    fig = px.bar(
        x=agent_counts.index, y=agent_counts.values,
        labels={"x": "Agent", "y": "Actions"},
        title="Actions per Agent",
        color=agent_counts.index,
    )
    fig.update_layout(height=250)
    st.plotly_chart(fig, use_container_width=True)

    # Activity log table
    st.subheader("Recent Activity")
    cols = [c for c in ['created_at', 'agent_name', 'action', 'target', 'status', 'details'] if c in df.columns]
    st.dataframe(df[cols], use_container_width=True, height=400)
    st.divider()


def render_key_metrics():
    st.header("Key Metrics")
    conn = get_db()
    clients_count = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    projects_active = conn.execute(
        "SELECT COUNT(*) FROM projects WHERE status='active'"
    ).fetchone()[0]
    projects_completed = conn.execute(
        "SELECT COUNT(*) FROM projects WHERE status='completed'"
    ).fetchone()[0]
    revenue_confirmed = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM revenue WHERE status='confirmed'"
    ).fetchone()[0]
    revenue_projected = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM revenue WHERE status='projected'"
    ).fetchone()[0]
    leads_count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    auto_running = conn.execute(
        "SELECT COUNT(*) FROM automation_health WHERE status='running'"
    ).fetchone()[0]
    auto_total = conn.execute("SELECT COUNT(*) FROM automation_health").fetchone()[0]
    content_published = conn.execute(
        "SELECT COUNT(*) FROM content_calendar WHERE status='published'"
    ).fetchone()[0]
    content_total = conn.execute("SELECT COUNT(*) FROM content_calendar").fetchone()[0]
    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("### Clients")
        st.markdown(f"**{clients_count}** total")
        st.markdown(f"**{projects_active}** active projects")
        st.markdown(f"**{projects_completed}** completed")

    with c2:
        st.markdown("### Revenue")
        st.markdown(f"**${revenue_confirmed:,.0f}** confirmed")
        st.markdown(f"**${revenue_projected:,.0f}** projected")
        total = revenue_confirmed + revenue_projected
        st.markdown(f"**${total:,.0f}** total pipeline")

    with c3:
        st.markdown("### Leads & Content")
        st.markdown(f"**{leads_count}** leads in pipeline")
        st.markdown(f"**{content_published}/{content_total}** content published")
        rate = (content_published / content_total * 100) if content_total > 0 else 0
        st.markdown(f"**{rate:.0f}%** publish rate")

    with c4:
        st.markdown("### Automations")
        st.markdown(f"**{auto_running}/{auto_total}** running")
        health = (auto_running / auto_total * 100) if auto_total > 0 else 0
        st.markdown(f"**{health:.0f}%** healthy")
    st.divider()


def render_ai_recommendations():
    st.header("AI Recommendations")
    st.markdown("Ask Hermes for business advice based on your command center data:")

    c1, c2 = st.columns([2, 1])
    with c1:
        question = st.text_input(
            "Ask Hermes",
            placeholder="Based on everything you know about my business, what are the 3 highest-leverage things I should focus on this week?",
        )
    with c2:
        st.markdown("")
        st.markdown("")
        ask_clicked = st.button("Ask Hermes", use_container_width=True)

    if ask_clicked and question:
        st.info("**Prompt to paste into Hermes (Telegram/Slack/Web):**")
        st.code(question, language="text")
        st.markdown("1. Open Hermes")
        st.markdown("2. Paste the prompt above")
        st.markdown("3. Answer any clarifying questions")
        st.markdown("4. Come back to recommendations")
    st.divider()


def main():
    st.set_page_config(
        page_title="AgentsFactory Command Center",
        page_icon="🏭",
        layout="wide",
    )

    init_business_db()

    st.sidebar.title("🏭 AgentsFactory")
    st.sidebar.markdown("**Command Center v1.0**")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigate",
        [
            "Overview",
            "Projects",
            "Revenue",
            "Leads",
            "Content",
            "Automations",
            "Agents",
            "AI Advice",
        ],
    )

    st.sidebar.divider()
    st.sidebar.markdown(f"*{datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    render_quick_add()

    if page == "Overview":
        render_header()
        render_kpi_overview()
        render_client_projects()
        render_revenue_dashboard()
        render_lead_pipeline()
        render_content_calendar()
        render_automation_health()
        render_key_metrics()
    elif page == "Projects":
        render_header()
        render_client_projects()
    elif page == "Revenue":
        render_header()
        render_revenue_dashboard()
    elif page == "Leads":
        render_header()
        render_lead_pipeline()
    elif page == "Content":
        render_header()
        render_content_calendar()
    elif page == "Automations":
        render_header()
        render_automation_health()
    elif page == "Agents":
        render_header()
        render_agent_activity()
    elif page == "AI Advice":
        render_header()
        render_ai_recommendations()


if __name__ == "__main__":
    main()

"""Streamlit dev dashboard for AgentsFactory.

Run with:
    uv run streamlit run src/agentkit/observability/dashboard.py

Provides:
- Pipeline trace viewer (all spans, timing, cost)
- Agent output inspector
- Circuit breaker status
- Cost/latency charts
- Eval results viewer
- Budget alerts
"""

from __future__ import annotations

import json
from typing import Any, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from agentkit.observability.metrics import MetricsCollector


def init_metrics_collector() -> MetricsCollector:
    """Get or create the metrics collector."""
    if "metrics_collector" not in st.session_state:
        st.session_state.metrics_collector = MetricsCollector()
    return st.session_state.metrics_collector


def render_header():
    st.title("🔬 AgentsFactory Dashboard")
    st.markdown("Real-time pipeline observability and evaluation")


def render_overview(collector: MetricsCollector):
    """Render overview metrics."""
    st.header("📊 Overview")

    runs = collector.get_recent_runs(limit=50)
    if not runs:
        st.info("No pipeline runs recorded yet. Run a pipeline to see metrics.")
        return

    df = pd.DataFrame(runs)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Runs", len(df))
    col2.metric("Total Tokens", f"{df['total_tokens'].sum():,.0f}")
    col3.metric("Total Cost", f"${df['total_cost_usd'].sum():.4f}")
    avg_latency = df['total_latency_ms'].mean() if len(df) > 0 else 0
    col4.metric("Avg Latency", f"{avg_latency:.0f}ms")

    # Status breakdown
    st.subheader("Run Status")
    status_counts = df['status'].value_counts()
    fig = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        color=status_counts.index,
        color_map={
            "completed": "#22c55e",
            "failed": "#ef4444",
            "escalated": "#f59e0b",
            "running": "#3b82f6",
        },
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)


def render_cost_analysis(collector: MetricsCollector):
    """Render cost analysis charts."""
    st.header("💰 Cost Analysis")

    runs = collector.get_recent_runs(limit=50)
    if not runs:
        st.info("No data yet.")
        return

    df = pd.DataFrame(runs)
    df['created_at'] = pd.to_datetime(df['created_at'])

    # Cost over time
    fig = px.bar(
        df,
        x='pipeline_id',
        y='total_cost_usd',
        color='status',
        title="Cost per Pipeline Run",
        labels={"total_cost_usd": "Cost (USD)", "pipeline_id": "Pipeline"},
        color_map={"completed": "#22c55e", "failed": "#ef4444", "escalated": "#f59e0b"},
    )
    fig.update_layout(height=350, xaxis={"categoryorder": "total descending"})
    st.plotly_chart(fig, use_container_width=True)

    # Token usage
    col1, col2 = st.columns(2)
    with col1:
        fig2 = px.bar(
            df,
            x='pipeline_id',
            y='total_tokens',
            title="Tokens per Run",
            labels={"total_tokens": "Tokens", "pipeline_id": "Pipeline"},
        )
        fig2.update_layout(height=300, xaxis={"categoryorder": "total descending"})
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        fig3 = px.scatter(
            df,
            x='total_tokens',
            y='total_cost_usd',
            color='status',
            size='agent_count',
            title="Tokens vs Cost",
            labels={"total_tokens": "Tokens", "total_cost_usd": "Cost (USD)"},
        )
        fig3.update_layout(height=300)
        st.plotly_chart(fig3, use_container_width=True)


def render_latency_analysis(collector: MetricsCollector):
    """Render latency analysis."""
    st.header("⏱️ Latency Analysis")

    runs = collector.get_recent_runs(limit=50)
    if not runs:
        st.info("No data yet.")
        return

    df = pd.DataFrame(runs)

    fig = px.bar(
        df,
        x='pipeline_id',
        y='total_latency_ms',
        color='agent_count',
        title="Latency per Pipeline Run",
        labels={"total_latency_ms": "Latency (ms)", "pipeline_id": "Pipeline", "agent_count": "Agents"},
        color_continuous_scale="Viridis",
    )
    fig.update_layout(height=350, xaxis={"categoryorder": "total descending"})
    st.plotly_chart(fig, use_container_width=True)


def render_agent_breakdown(collector: MetricsCollector):
    """Render per-agent metrics."""
    st.header("🤖 Agent Breakdown")

    # Get agent history for all agents
    agent_ids = set()
    runs = collector.get_recent_runs(limit=20)
    for run in runs:
        agent_ids.add(run.get("pipeline_id", ""))

    # Show per-agent metrics from recent runs
    all_agent_metrics = []
    for run in runs:
        pipeline_id = run.get("pipeline_id", "")
        agent_history = collector.get_agent_history(pipeline_id, limit=10)
        all_agent_metrics.extend(agent_history)

    if not all_agent_metrics:
        st.info("No agent metrics recorded yet.")
        return

    df = pd.DataFrame(all_agent_metrics)
    if df.empty:
        st.info("No agent metrics recorded yet.")
        return

    # Cost per agent
    agent_costs = df.groupby('agent_id').agg({
        'cost_usd': 'sum',
        'tokens_used': 'sum',
        'latency_ms': 'mean',
    }).reset_index()

    fig = px.bar(
        agent_costs,
        x='agent_id',
        y='cost_usd',
        title="Cost per Agent",
        labels={"cost_usd": "Total Cost (USD)", "agent_id": "Agent"},
    )
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

    # Agent performance table
    st.subheader("Agent Performance")
    st.dataframe(
        agent_costs.style.format({
            'cost_usd': '${:.6f}',
            'tokens_used': '{:,.0f}',
            'latency_ms': '{:.0f}ms',
        }),
        use_container_width=True,
    )


def render_budget_alerts(collector: MetricsCollector):
    """Render budget alerts."""
    st.header("🚨 Budget Alerts")

    alerts = collector.get_budget_alerts(limit=20)
    if not alerts:
        st.success("No budget alerts — all within limits!")
        return

    df = pd.DataFrame(alerts)
    for _, alert in df.iterrows():
        if alert['alert_type'] == 'cost_exceeded':
            st.error(f"💰 {alert['message']}")
        elif alert['alert_type'] == 'token_exceeded':
            st.warning(f"📊 {alert['message']}")
        elif alert['alert_type'] == 'latency_exceeded':
            st.warning(f"⏱️ {alert['message']}")
        else:
            st.info(f"ℹ️ {alert['message']}")


def render_recent_runs(collector: MetricsCollector):
    """Render recent runs table."""
    st.header("📋 Recent Runs")

    runs = collector.get_recent_runs(limit=20)
    if not runs:
        st.info("No runs recorded yet.")
        return

    df = pd.DataFrame(runs)
    st.dataframe(
        df[['pipeline_id', 'name', 'status', 'total_tokens', 'total_cost_usd',
             'total_latency_ms', 'agent_count', 'created_at']].style.format({
            'total_cost_usd': '${:.6f}',
            'total_tokens': '{:,.0f}',
            'total_latency_ms': '{:.0f}ms',
        }),
        use_container_width=True,
    )


def main():
    """Main dashboard entry point."""
    st.set_page_config(
        page_title="AgentsFactory Dashboard",
        page_icon="🔬",
        layout="wide",
    )

    collector = init_metrics_collector()

    # Sidebar navigation
    st.sidebar.title("🔬 AgentsFactory")
    page = st.sidebar.radio(
        "Navigate",
        ["Overview", "Cost Analysis", "Latency", "Agents", "Budget Alerts", "Recent Runs"],
    )

    render_header()

    if page == "Overview":
        render_overview(collector)
    elif page == "Cost Analysis":
        render_cost_analysis(collector)
    elif page == "Latency":
        render_latency_analysis(collector)
    elif page == "Agents":
        render_agent_breakdown(collector)
    elif page == "Budget Alerts":
        render_budget_alerts(collector)
    elif page == "Recent Runs":
        render_recent_runs(collector)


if __name__ == "__main__":
    main()

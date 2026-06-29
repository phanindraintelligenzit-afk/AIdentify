"""Report generation engine - transforms raw data into narrative reports."""
import json
from datetime import datetime
from typing import Any

from app.services.data_connector import generate_sample_metrics, simulate_data_fetch
from app.core.logging import get_logger

logger = get_logger(__name__)


TEMPLATES = {
    "executive_summary": "Executive Summary",
    "financial_report": "Financial Report",
    "marketing_dashboard": "Marketing Dashboard",
    "engineering_metrics": "Engineering Metrics",
    "weekly_status": "Weekly Status Report",
}


def _format_number(n: float) -> str:
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"{n/1_000:.1f}K"
    if isinstance(n, float):
        return f"{n:.2f}"
    return str(n)


def _format_pct(n: float) -> str:
    return f"{n*100:.1f}%"


def _trend_arrow(current: float, previous: float = 0) -> str:
    if current > previous:
        return "\u2191"
    elif current < previous:
        return "\u2193"
    return "\u2192"


def generate_executive_summary(title: str, all_metrics: dict[str, dict], sources_info: list[dict]) -> str:
    """Generate a full executive summary report."""
    now = datetime.utcnow().strftime("%B %d, %Y")

    sections = []
    sections.append(f"# {title}")
    sections.append(f"*Generated on {now}*\n")

    # Overview
    sections.append("## Overview\n")
    source_names = [s["name"] for s in sources_info]
    sections.append(
        f"This report synthesizes data from **{len(sources_info)} sources** "
        f"({', '.join(source_names)}) to provide a comprehensive view of business performance.\n"
    )

    # Financial metrics
    for source_id, metrics in all_metrics.items():
        if "mrr" in metrics or "arr" in metrics:
            sections.append("## Revenue Metrics\n")
            sections.append("| Metric | Value | Trend |")
            sections.append("|--------|-------|-------|")
            if "mrr" in metrics:
                sections.append(f"| Monthly Recurring Revenue | ${_format_number(metrics['mrr'])} | {_trend_arrow(metrics['mrr'])} |")
            if "arr" in metrics:
                sections.append(f"| Annual Run Rate | ${_format_number(metrics['arr'])} | {_trend_arrow(metrics['arr'])} |")
            if "churn_rate" in metrics:
                sections.append(f"| Churn Rate | {_format_pct(metrics['churn_rate'])} | {_trend_arrow(-metrics['churn_rate'])} |")
            if "new_customers" in metrics:
                sections.append(f"| New Customers | {metrics['new_customers']} | {_trend_arrow(metrics['new_customers'])} |")
            if "revenue_growth_pct" in metrics:
                sections.append(f"| Revenue Growth | {metrics['revenue_growth_pct']}% | {_trend_arrow(metrics['revenue_growth_pct'])} |")
            sections.append("")

    # Sales metrics
    for source_id, metrics in all_metrics.items():
        if "total_leads" in metrics or "deals_won" in metrics:
            sections.append("## Sales Pipeline\n")
            sections.append("| Metric | Value |")
            sections.append("|--------|-------|")
            if "total_leads" in metrics:
                sections.append(f"| Total Leads | {_format_number(metrics['total_leads'])} |")
            if "qualified_leads" in metrics:
                sections.append(f"| Qualified Leads | {_format_number(metrics['qualified_leads'])} |")
            if "conversion_rate" in metrics:
                sections.append(f"| Conversion Rate | {_format_pct(metrics['conversion_rate'])} |")
            if "deals_won" in metrics:
                sections.append(f"| Deals Won | {metrics['deals_won']} |")
            if "avg_deal_size" in metrics:
                sections.append(f"| Avg Deal Size | ${_format_number(metrics['avg_deal_size'])} |")
            sections.append("")

    # Marketing / web metrics
    for source_id, metrics in all_metrics.items():
        if "total_sessions" in metrics:
            sections.append("## Web & Marketing\n")
            sections.append("| Metric | Value |")
            sections.append("|--------|-------|")
            sections.append(f"| Total Sessions | {_format_number(metrics['total_sessions'])} |")
            sections.append(f"| Unique Users | {_format_number(metrics['unique_users'])} |")
            sections.append(f"| Bounce Rate | {_format_pct(metrics['bounce_rate'])} |")
            sections.append(f"| Pages/Session | {metrics['pages_per_session']} |")
            if "traffic_sources" in metrics:
                sections.append("\n**Traffic Sources:**\n")
                for src, val in metrics["traffic_sources"].items():
                    sections.append(f"- {src.capitalize()}: {_format_number(val)}")
            sections.append("")

    # Engineering metrics
    for source_id, metrics in all_metrics.items():
        if "total_tickets" in metrics or "sprint_velocity" in metrics:
            sections.append("## Engineering\n")
            sections.append("| Metric | Value |")
            sections.append("|--------|-------|")
            if "total_tickets" in metrics:
                sections.append(f"| Total Tickets | {metrics['total_tickets']} |")
            if "closed_this_period" in metrics:
                sections.append(f"| Closed This Period | {metrics['closed_this_period']} |")
            if "avg_resolution_hours" in metrics:
                sections.append(f"| Avg Resolution | {metrics['avg_resolution_hours']}h |")
            if "sprint_velocity" in metrics:
                sections.append(f"| Sprint Velocity | {metrics['sprint_velocity']} pts |")
            if "bug_count" in metrics:
                sections.append(f"| Open Bugs | {metrics['bug_count']} |")
            sections.append("")

    # AI-generated narrative
    sections.append("## Key Insights\n")
    insights = _generate_insights(all_metrics)
    for insight in insights:
        sections.append(f"- {insight}")
    sections.append("")

    # Recommendations
    sections.append("## Recommendations\n")
    recs = _generate_recommendations(all_metrics)
    for i, rec in enumerate(recs, 1):
        sections.append(f"{i}. {rec}")
    sections.append("")

    return "\n".join(sections)


def _generate_insights(all_metrics: dict) -> list[str]:
    """Generate AI-style insights from metrics."""
    insights = []
    for source_id, m in all_metrics.items():
        if "churn_rate" in m and m["churn_rate"] > 0.05:
            insights.append(f"Churn rate is at {_format_pct(m['churn_rate'])} - above the 5% threshold. Consider implementing retention campaigns.")
        if "revenue_growth_pct" in m and m["revenue_growth_pct"] > 10:
            insights.append(f"Strong revenue growth at {m['revenue_growth_pct']}% - momentum is positive.")
        if "revenue_growth_pct" in m and m["revenue_growth_pct"] < 0:
            insights.append(f"Revenue declined {m['revenue_growth_pct']}% - investigate pipeline and churn.")
        if "conversion_rate" in m and m["conversion_rate"] < 0.1:
            insights.append(f"Lead conversion at {_format_pct(m['conversion_rate'])} is below target. Review qualification criteria.")
        if "bounce_rate" in m and m["bounce_rate"] > 0.5:
            insights.append(f"Web bounce rate at {_format_pct(m['bounce_rate'])} suggests landing page optimization needed.")
        if "avg_resolution_hours" in m and m["avg_resolution_hours"] > 48:
            insights.append(f"Ticket resolution averaging {m['avg_resolution_hours']}h - consider adding engineering capacity.")
        if "bug_count" in m and m["bug_count"] > 25:
            insights.append(f"{m['bug_count']} open bugs - recommend a stabilization sprint.")
    if not insights:
        insights.append("All key metrics are within normal ranges. Continue monitoring trends.")
    return insights


def _generate_recommendations(all_metrics: dict) -> list[str]:
    """Generate actionable recommendations."""
    recs = []
    for source_id, m in all_metrics.items():
        if "churn_rate" in m and m["churn_rate"] > 0.05:
            recs.append("Launch a customer success outreach program for at-risk accounts.")
        if "conversion_rate" in m and m["conversion_rate"] < 0.1:
            recs.append("A/B test new lead nurture sequences to improve conversion.")
        if "bounce_rate" in m and m["bounce_rate"] > 0.5:
            recs.append("Redesign top landing pages with clearer CTAs and faster load times.")
        if "avg_resolution_hours" in m and m["avg_resolution_hours"] > 48:
            recs.append("Prioritize tech debt reduction to speed up ticket resolution.")
        if "sprint_velocity" in m and m["sprint_velocity"] < 30:
            recs.append("Review sprint planning - velocity is below team average.")
    if not recs:
        recs.append("Maintain current trajectory - focus on incremental improvements.")
    return recs


def generate_report_content(
    title: str,
    template_type: str,
    data_sources: list[dict],
    output_format: str = "html"
) -> tuple[str, dict]:
    """Main entry point: generate a report from data sources."""
    logger.info("Generating report", title=title, template=template_type, sources=len(data_sources))

    all_metrics = {}
    sources_info = []
    total_rows = 0

    for ds in data_sources:
        source_id = str(ds["id"])
        metrics = generate_sample_metrics(ds["source_type"])
        all_metrics[source_id] = metrics
        rows = simulate_data_fetch(ds["source_type"], ds.get("config", {}))
        total_rows += len(rows)
        sources_info.append({
            "id": source_id,
            "name": ds["name"],
            "type": ds["source_type"],
            "rows": len(rows),
        })

    content = generate_executive_summary(title, all_metrics, sources_info)

    if output_format == "json":
        content = json.dumps({
            "title": title,
            "generated_at": datetime.utcnow().isoformat(),
            "sources": sources_info,
            "metrics": all_metrics,
            "insights": _generate_insights(all_metrics),
            "recommendations": _generate_recommendations(all_metrics),
        }, indent=2)

    summary_metrics = {
        "total_sources": len(data_sources),
        "total_rows_processed": total_rows,
        "template_used": TEMPLATES.get(template_type, template_type),
        "generated_at": datetime.utcnow().isoformat(),
    }

    logger.info("Report generated", title=title, rows=total_rows)
    return content, summary_metrics

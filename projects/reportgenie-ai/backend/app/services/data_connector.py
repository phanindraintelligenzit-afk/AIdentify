"""Data connector service - fetches data from various sources."""
import random
from datetime import datetime, timedelta
from typing import Any


def generate_sample_metrics(source_type: str) -> dict[str, Any]:
    """Generate realistic sample metrics based on source type."""
    if source_type == "stripe":
        return {
            "mrr": round(random.uniform(15000, 25000), 2),
            "arr": round(random.uniform(180000, 300000), 2),
            "churn_rate": round(random.uniform(0.01, 0.08), 3),
            "new_customers": random.randint(15, 80),
            "total_customers": random.randint(200, 800),
            "arpu": round(random.uniform(80, 250), 2),
            "revenue_growth_pct": round(random.uniform(-5, 25), 1),
        }
    elif source_type == "hubspot":
        return {
            "total_leads": random.randint(500, 3000),
            "qualified_leads": random.randint(80, 400),
            "opportunities_created": random.randint(20, 120),
            "deals_won": random.randint(5, 50),
            "deals_lost": random.randint(3, 30),
            "conversion_rate": round(random.uniform(0.05, 0.25), 3),
            "avg_deal_size": round(random.uniform(5000, 25000), 2),
            "sales_cycle_days": random.randint(15, 60),
        }
    elif source_type == "ganalytics":
        sessions = random.randint(10000, 100000)
        return {
            "total_sessions": sessions,
            "unique_users": int(sessions * random.uniform(0.55, 0.75)),
            "bounce_rate": round(random.uniform(0.25, 0.65), 3),
            "avg_session_duration_sec": random.randint(60, 300),
            "pages_per_session": round(random.uniform(1.5, 4.5), 2),
            "top_pages": [
                {"path": "/", "views": random.randint(5000, 20000)},
                {"path": "/pricing", "views": random.randint(1000, 5000)},
                {"path": "/blog", "views": random.randint(800, 3000)},
            ],
            "traffic_sources": {
                "organic": random.randint(3000, 30000),
                "direct": random.randint(2000, 15000),
                "referral": random.randint(500, 5000),
                "social": random.randint(300, 3000),
                "paid": random.randint(200, 2000),
            },
        }
    elif source_type == "jira":
        return {
            "total_tickets": random.randint(100, 800),
            "open_tickets": random.randint(10, 100),
            "closed_this_period": random.randint(30, 200),
            "avg_resolution_hours": round(random.uniform(4, 72), 1),
            "sprint_velocity": random.randint(20, 60),
            "bug_count": random.randint(5, 40),
            "feature_requests": random.randint(10, 60),
            "priority_breakdown": {
                "critical": random.randint(1, 8),
                "high": random.randint(5, 20),
                "medium": random.randint(10, 40),
                "low": random.randint(5, 25),
            },
        }
    elif source_type == "csv":
        return {
            "rows_processed": random.randint(1000, 50000),
            "columns": random.randint(5, 25),
            "null_pct": round(random.uniform(0, 0.15), 3),
            "summary_stats": {
                "mean": round(random.uniform(100, 1000), 2),
                "median": round(random.uniform(90, 950), 2),
                "std_dev": round(random.uniform(10, 200), 2),
            },
        }
    else:
        return {
            "records": random.randint(100, 5000),
            "status": "connected",
            "last_fetch": datetime.utcnow().isoformat(),
        }


def simulate_data_fetch(source_type: str, config: dict) -> list[dict]:
    """Simulate fetching data rows from a source."""
    now = datetime.utcnow()
    rows = []
    num_days = config.get("days", 30)

    for i in range(num_days):
        date = now - timedelta(days=i)
        if source_type == "stripe":
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "revenue": round(random.uniform(300, 1200), 2),
                "churned": random.randint(0, 5),
                "new_subs": random.randint(1, 12),
            })
        elif source_type == "ganalytics":
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "sessions": random.randint(200, 3000),
                "users": random.randint(150, 2000),
                "conversions": random.randint(5, 80),
            })
        elif source_type == "jira":
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "created": random.randint(2, 15),
                "resolved": random.randint(1, 12),
                "backlog_change": random.randint(-5, 8),
            })
        else:
            rows.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(random.uniform(10, 100), 2),
                "count": random.randint(1, 50),
            })

    return sorted(rows, key=lambda x: x["date"])

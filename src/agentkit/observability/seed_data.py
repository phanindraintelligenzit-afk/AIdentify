"""Seed data for AgentsFactory Command Center.

Run once to populate the dashboard with sample data:
    uv run python src/agentkit/observability/seed_data.py
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path("./agentsfactory_metrics.db")


def seed():
    # Initialize business tables directly
    conn_init = sqlite3.connect(str(DB_PATH))
    conn_init.executescript(
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
    )
    conn_init.commit()
    conn_init.close()

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # Clients
    clients = [
        ("client_001", "Acme Corp", "E-commerce", "John Doe", "john@acme.com", "+1234567890",
         "active", 5000, "Key client, 3 automations running"),
        ("client_002", "TechStart.io", "SaaS", "Jane Smith", "jane@techstart.io", "+0987654321",
         "active", 3500, "New client, onboarding in progress"),
        ("client_003", "Local Dental Clinic", "Healthcare", "Dr. Raj", "raj@dental.com", "+1122334455",
         "lead", 2000, "Interested in appointment automation"),
        ("client_004", "FoodChain Restaurants", "F&B", "Maria Garcia", "maria@foodchain.com", "+5566778899",
         "lead", 4500, "Needs inventory + ordering automation"),
        ("client_005", "EduLearn Academy", "Education", "Prof. Kumar", "kumar@edulearn.com", "+9988776655",
         "active", 3000, "Student enrollment automation live"),
    ]
    for cl in clients:
        c.execute(
            "INSERT OR IGNORE INTO clients (id, name, industry, contact_name, contact_email, "
            "contact_phone, status, deal_value, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", cl
        )

    # Projects
    projects = [
        ("proj_001", "client_001", "Customer Support Automation",
         "Auto-responses, ticket routing, FAQ bot", "active", "pipeline_001"),
        ("proj_002", "client_001", "Order Tracking System",
         "Real-time order status via WhatsApp", "active", "pipeline_002"),
        ("proj_003", "client_002", "Lead Qualification Bot",
         "Auto-qualify and score incoming leads", "active", "pipeline_003"),
        ("proj_004", "client_005", "Student Enrollment Flow",
         "Automated enrollment and onboarding", "completed", "pipeline_004"),
        ("proj_005", "client_003", "Appointment Booking System",
         "Online booking with SMS reminders", "paused", None),
    ]
    for p in projects:
        c.execute(
            "INSERT OR IGNORE INTO projects (id, client_id, name, description, status, pipeline_id) "
            "VALUES (?, ?, ?, ?, ?, ?)", p
        )

    # Revenue
    revenue = [
        (None, "client_001", "proj_001", 2500, "one_time", "confirmed", "Setup fee"),
        (None, "client_001", "proj_001", 500, "recurring", "confirmed", "Monthly - Support bot"),
        (None, "client_001", "proj_002", 3000, "one_time", "confirmed", "Order tracking build"),
        (None, "client_002", "proj_003", 1500, "one_time", "confirmed", "Lead bot setup"),
        (None, "client_002", "proj_003", 300, "recurring", "confirmed", "Monthly - Lead bot"),
        (None, "client_005", "proj_004", 2000, "one_time", "confirmed", "Enrollment automation"),
        (None, "client_005", "proj_004", 200, "recurring", "confirmed", "Monthly - Enrollment"),
        (None, "client_003", None, 2000, "one_time", "projected", "Appointment system"),
        (None, "client_004", None, 4500, "one_time", "projected", "Inventory automation"),
        (None, "client_004", None, 800, "recurring", "projected", "Monthly - Inventory"),
    ]
    for r in revenue:
        c.execute(
            "INSERT OR IGNORE INTO revenue (id, client_id, project_id, amount, type, status, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)", r
        )

    # Leads
    leads = [
        ("lead_001", "Sarah Johnson", "FashionBrand Co", "sarah@fashion.com", "+1234567890",
         "inbound", "qualified", 85, "Interested in social media automation"),
        ("lead_002", "Mike Chen", "Mike's Plumbing", "mike@plumbing.com", "+0987654321",
         "outbound", "new", 45, "Cold outreach, needs follow-up"),
        ("lead_003", "Lisa Park", "Park Accounting", "lisa@parkacct.com", "+1122334455",
         "referral", "contacted", 70, "Referred by Acme Corp"),
        ("lead_004", "Tom Wilson", "Wilson Law Firm", "tom@wilsonlaw.com", "+5566778899",
         "website", "new", 55, "Filled contact form on website"),
        ("lead_005", "Amy Lee", "Amy's Bakery", "amy@bakery.com", "+9988776655",
         "social", "qualified", 80, "Saw LinkedIn post, wants ordering automation"),
        ("lead_006", "David Brown", "Brown Logistics", "david@logistics.com", "+3344556677",
         "inbound", "new", 40, "Needs inventory tracking"),
        ("lead_007", "Emma Davis", "Davis Marketing", "emma@davis.com", "+7788990011",
         "outbound", "contacted", 65, "Interested in content automation"),
    ]
    for l in leads:
        c.execute(
            "INSERT OR IGNORE INTO leads (id, name, company, email, phone, source, stage, score, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", l
        )

    # Content Calendar
    content = [
        ("content_001", "How AI Agents Save 20 Hours/Week for Small Businesses",
         "linkedin", "published", "2025-06-01", "2025-06-01", 85, "Top performer this month"),
        ("content_002", "5 Automations Every Restaurant Needs",
         "linkedin", "published", "2025-06-05", "2025-06-05", 72, "Good engagement"),
        ("content_003", "Case Study: How Acme Corp Cut Support Costs by 60%",
         "newsletter", "scheduled", "2025-06-15", None, 0, "Waiting for client approval"),
        ("content_004", "The Hidden Cost of Manual Data Entry",
         "twitter", "published", "2025-06-08", "2025-06-08", 55, "Thread format"),
        ("content_005", "AI vs Hiring: The Real Math for Small Businesses",
         "linkedin", "draft", "2025-06-20", None, 0, "Needs final review"),
        ("content_006", "How to Automate Your Lead Follow-Up in 1 Day",
         "youtube", "draft", "2025-06-25", None, 0, "Script ready, filming next week"),
        ("content_007", "Client Spotlight: EduLearn Enrollment Automation",
         "newsletter", "scheduled", "2025-06-18", None, 0, "Case study draft"),
    ]
    for ct in content:
        c.execute(
            "INSERT OR IGNORE INTO content_calendar "
            "(id, title, platform, status, scheduled_at, published_at, engagement_score, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", ct
        )

    # Automation Health
    automations = [
        ("auto_001", "Acme Support Bot", "client_001", "proj_001", "running",
         "2025-06-11T08:00:00", "", 1250, 3, 99.8, "Healthy, minor timeout yesterday"),
        ("auto_002", "Acme Order Tracker", "client_001", "proj_002", "running",
         "2025-06-11T07:45:00", "", 890, 1, 99.9, "All good"),
        ("auto_003", "TechStart Lead Scorer", "client_002", "proj_003", "running",
         "2025-06-11T06:30:00", "", 567, 8, 97.5, "Some API rate limit issues"),
        ("auto_004", "EduLearn Enrollment", "client_005", "proj_004", "running",
         "2025-06-10T09:00:00", "", 2100, 0, 100.0, "Perfect uptime"),
        ("auto_005", "Dental Appointment Reminders", "client_003", "proj_005", "paused",
         "2025-06-01T10:00:00", "", 45, 2, 95.0, "Paused pending client decision"),
    ]
    for a in automations:
        c.execute(
            "INSERT OR IGNORE INTO automation_health "
            "(id, name, client_id, project_id, status, last_run_at, last_error, "
            "success_count, failure_count, uptime_pct, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", a
        )

    # Business Metrics (historical)
    metrics = [
        ("hours_saved_weekly", 42, "hours", "weekly"),
        ("tasks_automated_daily", 156, "tasks", "daily"),
        ("client_satisfaction", 4.7, "score", "monthly"),
        ("avg_response_time", 2.3, "minutes", "daily"),
        ("cost_per_automation", 45, "USD", "monthly"),
        ("lead_conversion_rate", 23, "percent", "monthly"),
        ("revenue_per_client", 2800, "USD", "monthly"),
        ("automation_uptime", 98.5, "percent", "daily"),
    ]
    for m in metrics:
        c.execute(
            "INSERT OR IGNORE INTO business_metrics (metric_name, metric_value, metric_unit, period) "
            "VALUES (?, ?, ?, ?)", m
        )

    conn.commit()
    conn.close()
    print("Seed data loaded successfully!")
    print(f"  Clients: {len(clients)}")
    print(f"  Projects: {len(projects)}")
    print(f"  Revenue entries: {len(revenue)}")
    print(f"  Leads: {len(leads)}")
    print(f"  Content items: {len(content)}")
    print(f"  Automations: {len(automations)}")
    print(f"  Business metrics: {len(metrics)}")


if __name__ == "__main__":
    seed()

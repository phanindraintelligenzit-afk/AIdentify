#!/usr/bin/env python3
"""
Google Forms → agentsfactory_metrics.db sync.
Reads the Google Sheet that Google Forms writes to and syncs leads into the dashboard.
Run this periodically (e.g., every 30 min via cron).

Setup:
1. Create a Google Form with fields: Full Name, Email, Business Type, Biggest Pain Point
2. Link it to a Google Sheet (Responses)
3. Share the Sheet with the service account (or make it public-read)
4. Set GOOGLE_SHEET_ID in ~/.hermes/.env
5. Run: python src/agents/form_sync.py
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
import urllib.request
import json
import csv
import io

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "agentsfactory_metrics.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_sheet_id():
    """Read Google Sheet ID from .env file."""
    env_path = Path(r"C:\Users\Admin\.hermes\.env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "GOOGLE_FORM_SHEET_ID" in line and "=" in line:
                    return line.split("=", 1)[1].strip()
    return None


def read_google_sheet(sheet_id: str) -> list[dict]:
    """Read CSV export of Google Sheet."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = response.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(data))
    return list(reader)


def sync_to_database(rows: list[dict]) -> int:
    """Sync form responses to leads table."""
    conn = get_db()
    inserted = 0
    for row in rows:
        name = row.get("Full Name", "").strip()
        email = row.get("Email Address", row.get("Email", "")).strip()
        business_type = row.get("Business Type", "").strip()
        pain_point = row.get("Biggest Pain Point", "").strip()

        if not name:
            continue

        # Skip duplicates
        exists = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE email = ? OR name = ?",
            (email, name),
        ).fetchone()[0]
        if exists:
            continue

        lid = f"lead_{datetime.now().strftime('%Y%m%d%H%M%S')}_{inserted}"
        score = 50  # Default for form submissions
        conn.execute(
            "INSERT INTO leads (id, name, email, source, stage, score, notes) "
            "VALUES (?, ?, ?, 'website', 'new', ?, ?)",
            (lid, name, email, score, f"Business: {business_type} | Pain: {pain_point}"),
        )
        inserted += 1

        # Also log to agent_activity
        conn.execute(
            "INSERT INTO agent_activity (agent_name, action, target, status, details) "
            "VALUES ('form_sync', 'new_lead_from_form', ?, 'completed', ?)",
            (name, f"Email: {email}, Type: {business_type}"),
        )

    conn.commit()
    conn.close()
    return inserted


FORMSPREE_ENDPOINT = "https://formspree.io/f/xlgkpzeo"

def sync_to_formspree(name, email, business_type, pain_point):
    """Send lead data to Formspree as a backup/submission log."""
    import urllib.request
    import json

    payload = json.dumps({
        "name": name,
        "email": email,
        "business_type": business_type,
        "pain_point": pain_point,
        "source": "landing_page",
    }).encode("utf-8")

    req = urllib.request.Request(
        FORMSPREE_ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status == 200
    except Exception:
        return False
    """Sync form responses to Notion Leads database."""
    import subprocess

    # Read Notion API key
    env_path = Path(r"C:\Users\Admin\.hermes\.env")
    api_key = None
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "NOTION_API_KEY" in line and "=" in line:
                    api_key = line.split("=", 1)[1].strip()
                    break

    if not api_key:
        print("No NOTION_API_KEY found, skipping Notion sync")
        return 0

    NOTION_LEADS_DB = "37d4baec-8165-81fe-ab68-d2c3c347589d"
    inserted = 0

    for row in rows:
        name = row.get("Full Name", "").strip()
        email = row.get("Email Address", row.get("Email", "")).strip()
        business_type = row.get("Business Type", "").strip()
        pain_point = row.get("Biggest Pain Point", "").strip()

        if not name:
            continue

        payload = {
            "parent": {"database_id": NOTION_LEADS_DB},
            "properties": {
                "Name": [{"text": {"content": name}}],
                "Email": {"email": email} if email else None,
                "Source": {"select": {"name": "website"}},
                "Stage": {"select": {"name": "new"}},
                "Score": {"number": 50},
                "Notes": {"rich_text": [{"text": {"content": f"Business: {business_type} | Pain: {pain_point}"}}]},
            },
        }
        # Remove None values
        payload["properties"] = {k: v for k, v in payload["properties"].items() if v is not None}

        cmd = [
            "curl", "-s", "-X", "POST",
            "https://api.notion.com/v1/pages",
            "-H", "Authorization: Bearer " + api_key,
            "-H", "Notion-Version: 2022-06-28",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        if data.get("id"):
            inserted += 1

    return inserted


if __name__ == "__main__":
    sheet_id = get_sheet_id()
    if not sheet_id:
        print("ERROR: GOOGLE_FORM_SHEET_ID not found in ~/.hermes/.env")
        print("Add it like: GOOGLE_FORM_SHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms")
        exit(1)

    print(f"Reading Google Sheet: {sheet_id}")
    rows = read_google_sheet(sheet_id)
    print(f"Found {len(rows)} response(s)")

    if rows:
        db_count = sync_to_database(rows)
        print(f"Synced {db_count} new lead(s) to dashboard DB")

        notion_count = sync_to_notion(rows)
        print(f"Synced {notion_count} new lead(s) to Notion")
    else:
        print("No responses yet.")

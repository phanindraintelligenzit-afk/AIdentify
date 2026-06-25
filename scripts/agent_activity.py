"""
AgentsFactory Agent Activity Logger.

Logs all agent actions (War Room posts, task updates, cron runs) to SQLite.
This is the data source for the Master Dashboard.

Usage:
    from agent_activity import ActivityLogger, log_agent_action, get_recent_activity

    logger = ActivityLogger()
    logger.log("Coder", "task_start", "Rate limiting middleware", "in_progress")
    logger.log("Reviewer", "review_complete", "PR #247", "completed", "Clean code")
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "agentsfactory_metrics.db"


def get_db() -> sqlite3.Connection:
    conn = str(DB_PATH)
    db = sqlite3.connect(conn)
    db.row_factory = sqlite3.Row
    return db


def init_activity_db() -> None:
    """Create all tables needed for agent activity tracking."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS agent_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT DEFAULT '',
            status TEXT DEFAULT 'completed',
            details TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            assigned_to TEXT DEFAULT '',
            status TEXT DEFAULT 'backlog',
            priority TEXT DEFAULT 'normal',
            tags TEXT DEFAULT '[]',
            created_by TEXT DEFAULT 'owl',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT DEFAULT '',
            due_date TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS cron_health (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            schedule TEXT DEFAULT '',
            last_run_at TEXT DEFAULT '',
            last_status TEXT DEFAULT 'unknown',
            last_duration_sec REAL DEFAULT 0,
            last_error TEXT DEFAULT '',
            next_run_at TEXT DEFAULT '',
            total_runs INTEGER DEFAULT 0,
            total_success INTEGER DEFAULT 0,
            total_fail INTEGER DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS war_room_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            message TEXT DEFAULT '',
            task_ref TEXT DEFAULT '',
            status_tag TEXT DEFAULT '',
            slack_ts TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_activity_agent ON agent_activity(agent_name);
        CREATE INDEX IF NOT EXISTS idx_activity_created ON agent_activity(created_at);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to);
        CREATE INDEX IF NOT EXISTS idx_war_room_created ON war_room_messages(created_at);
    """)
    db.commit()
    db.close()


class ActivityLogger:
    """Central logger for all agent activity."""

    def __init__(self):
        init_activity_db()

    def log(self, agent_name: str, action: str, target: str = "",
            status: str = "completed", details: str = "") -> int:
        """Log an agent action. Returns the row id."""
        db = get_db()
        cur = db.execute(
            "INSERT INTO agent_activity (agent_name, action, target, status, details) "
            "VALUES (?, ?, ?, ?, ?)",
            (agent_name, action, target, status, details),
        )
        db.commit()
        row_id = cur.lastrowid
        db.close()
        return row_id

    def log_war_room(self, agent_name: str, message: str,
                     task_ref: str = "", status_tag: str = "",
                     slack_ts: str = "") -> int:
        """Log a War Room message."""
        db = get_db()
        cur = db.execute(
            "INSERT INTO war_room_messages (agent_name, message, task_ref, status_tag, slack_ts) "
            "VALUES (?, ?, ?, ?, ?)",
            (agent_name, message, task_ref, status_tag, slack_ts),
        )
        db.commit()
        row_id = cur.lastrowid
        db.close()
        return row_id

    def create_task(self, task_id: str, title: str, assigned_to: str = "",
                    description: str = "", priority: str = "normal",
                    tags: list = None, created_by: str = "OWL",
                    due_date: str = "") -> None:
        """Create a new task."""
        db = get_db()
        db.execute(
            "INSERT OR REPLACE INTO tasks (id, title, description, assigned_to, "
            "status, priority, tags, created_by, due_date) "
            "VALUES (?, ?, ?, ?, 'backlog', ?, ?, ?, ?)",
            (task_id, title, description, assigned_to, priority,
             json.dumps(tags or []), created_by, due_date),
        )
        db.commit()
        db.close()

    def update_task(self, task_id: str, status: str = None,
                    assigned_to: str = None, details: str = None) -> None:
        """Update a task's status or assignment."""
        db = get_db()
        sets = ["updated_at = datetime('now')"]
        vals = []
        if status:
            sets.append("status = ?")
            vals.append(status)
            if status == "completed":
                sets.append("completed_at = datetime('now')")
        if assigned_to:
            sets.append("assigned_to = ?")
            vals.append(assigned_to)
        vals.append(task_id)
        db.execute(f"UPDATE tasks SET {', '.join(sets)} WHERE id = ?", vals)
        db.commit()
        db.close()

    def update_cron_health(self, cron_id: str, name: str, schedule: str = "",
                           last_run_at: str = "", last_status: str = "",
                           last_duration_sec: float = 0,
                           last_error: str = "", next_run_at: str = "") -> None:
        """Update cron job health status."""
        db = get_db()
        existing = db.execute("SELECT * FROM cron_health WHERE id = ?", (cron_id,)).fetchone()
        if existing:
            total_runs = existing["total_runs"] + 1
            total_success = existing["total_success"] + (1 if last_status == "ok" else 0)
            total_fail = existing["total_fail"] + (1 if last_status == "error" else 0)
            db.execute(
                "UPDATE cron_health SET name=?, schedule=?, last_run_at=?, last_status=?, "
                "last_duration_sec=?, last_error=?, next_run_at=?, total_runs=?, "
                "total_success=?, total_fail=?, updated_at=datetime('now') WHERE id=?",
                (name, schedule, last_run_at, last_status, last_duration_sec,
                 last_error, next_run_at, total_runs, total_success, total_fail, cron_id),
            )
        else:
            db.execute(
                "INSERT INTO cron_health (id, name, schedule, last_run_at, last_status, "
                "last_duration_sec, last_error, next_run_at, total_runs, total_success, total_fail) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
                (cron_id, name, schedule, last_run_at, last_status,
                 last_duration_sec, last_error, next_run_at,
                 1 if last_status == "ok" else 0,
                 1 if last_status == "error" else 0),
            )
        db.commit()
        db.close()

    def get_recent_activity(self, limit: int = 50, agent: str = None,
                            hours: int = 24) -> list:
        """Get recent agent activity."""
        db = get_db()
        since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        if agent:
            rows = db.execute(
                "SELECT * FROM agent_activity WHERE agent_name = ? AND created_at >= ? "
                "ORDER BY created_at DESC LIMIT ?",
                (agent, since, limit),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM agent_activity WHERE created_at >= ? "
                "ORDER BY created_at DESC LIMIT ?",
                (since, limit),
            ).fetchall()
        db.close()
        return [dict(r) for r in rows]

    def get_war_room_history(self, limit: int = 30, hours: int = 24) -> list:
        """Get recent War Room messages."""
        db = get_db()
        since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        rows = db.execute(
            "SELECT * FROM war_room_messages WHERE created_at >= ? "
            "ORDER BY created_at DESC LIMIT ?",
            (since, limit),
        ).fetchall()
        db.close()
        return [dict(r) for r in rows]

    def get_tasks(self, status: str = None, assigned_to: str = None) -> list:
        """Get tasks, optionally filtered."""
        db = get_db()
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if assigned_to:
            query += " AND assigned_to = ?"
            params.append(assigned_to)
        query += " ORDER BY updated_at DESC"
        rows = db.execute(query, params).fetchall()
        db.close()
        return [dict(r) for r in rows]

    def get_cron_health(self) -> list:
        """Get all cron job health records."""
        db = get_db()
        rows = db.execute("SELECT * FROM cron_health ORDER BY name").fetchall()
        db.close()
        return [dict(r) for r in rows]

    def get_agent_stats(self, hours: int = 24) -> list:
        """Get per-agent action counts."""
        db = get_db()
        since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        rows = db.execute(
            "SELECT agent_name, COUNT(*) as actions, "
            "SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed, "
            "SUM(CASE WHEN status='in_progress' THEN 1 ELSE 0 END) as in_progress, "
            "SUM(CASE WHEN status='blocked' THEN 1 ELSE 0 END) as blocked "
            "FROM agent_activity WHERE created_at >= ? "
            "GROUP BY agent_name ORDER BY actions DESC",
            (since,),
        ).fetchall()
        db.close()
        return [dict(r) for r in rows]

    def get_summary(self) -> dict:
        """Get a summary of all activity for the dashboard header."""
        db = get_db()
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")

        stats = {}
        stats["total_actions_today"] = db.execute(
            "SELECT COUNT(*) FROM agent_activity WHERE date(created_at) = ?",
            (today,),
        ).fetchone()[0]
        stats["total_actions_week"] = db.execute(
            "SELECT COUNT(*) FROM agent_activity WHERE date(created_at) >= ?",
            (week_ago,),
        ).fetchone()[0]
        stats["active_tasks"] = db.execute(
            "SELECT COUNT(*) FROM tasks WHERE status IN ('in_progress','assigned')",
        ).fetchone()[0]
        stats["completed_tasks"] = db.execute(
            "SELECT COUNT(*) FROM tasks WHERE status = 'completed'",
        ).fetchone()[0]
        stats["backlog_tasks"] = db.execute(
            "SELECT COUNT(*) FROM tasks WHERE status = 'backlog'",
        ).fetchone()[0]
        stats["blocked_tasks"] = db.execute(
            "SELECT COUNT(*) FROM tasks WHERE status = 'blocked'",
        ).fetchone()[0]
        stats["total_crons"] = db.execute("SELECT COUNT(*) FROM cron_health").fetchone()[0]
        stats["healthy_crons"] = db.execute(
            "SELECT COUNT(*) FROM cron_health WHERE last_status = 'ok'",
        ).fetchone()[0]
        stats["failed_crons"] = db.execute(
            "SELECT COUNT(*) FROM cron_health WHERE last_status = 'error'",
        ).fetchone()[0]
        stats["war_room_messages_today"] = db.execute(
            "SELECT COUNT(*) FROM war_room_messages WHERE date(created_at) = ?",
            (today,),
        ).fetchone()[0]

        db.close()
        return stats


# Module-level convenience functions
_logger = None

def _get_logger() -> ActivityLogger:
    global _logger
    if _logger is None:
        _logger = ActivityLogger()
    return _logger

def log_agent_action(agent_name: str, action: str, target: str = "",
                     status: str = "completed", details: str = "") -> int:
    return _get_logger().log(agent_name, action, target, status, details)

def get_recent_activity(limit: int = 50, agent: str = None, hours: int = 24) -> list:
    return _get_logger().get_recent_activity(limit, agent, hours)

def get_summary() -> dict:
    return _get_logger().get_summary()


if __name__ == "__main__":
    # Initialize and test
    init_activity_db()
    logger = ActivityLogger()

    # Seed some test data
    logger.log("OWL", "orchestrate", "Sprint 6", "completed", "All agents assigned")
    logger.log("Coder", "task_start", "Rate limiting middleware", "in_progress")
    logger.log("Researcher", "research", "Competitor analysis", "completed", "12 competitors scanned")
    logger.log("Reviewer", "review", "PR #247", "completed", "Approved")
    logger.log("Planner", "plan", "Sprint 6 backlog", "completed", "20 tasks prioritized")
    logger.log("Social", "post", "LinkedIn post #45", "completed", "12 engagements")
    logger.log("Outreach", "send", "Lead batch #3", "completed", "40 emails sent")

    logger.create_task("task-001", "Rate limiting middleware", "Coder",
                       "Implement per-agent rate limiting", "high",
                       ["backend", "security"])
    logger.create_task("task-002", "Competitor pricing scan", "Researcher",
                       "Weekly competitor pricing analysis", "normal",
                       ["research"])
    logger.create_task("task-003", "Sprint 6 planning", "Planner",
                       "Groom backlog, estimate stories", "high",
                       ["planning"])

    logger.update_task("task-001", "in_progress")
    logger.update_task("task-002", "completed")
    logger.update_task("task-003", "in_progress")

    logger.log_war_room("OWL", "Sprint 6 kickoff. All agents assigned.", "Sprint 6", "[STARTED]")
    logger.log_war_room("Coder", "Starting rate limiting middleware.", "PR #248", "[IN_PROGRESS]")
    logger.log_war_room("Researcher", "Competitor scan complete. 12 competitors analyzed.", "Sprint 6", "[DONE]")

    print("✅ Activity logger initialized and seeded.")
    print(f"Summary: {logger.get_summary()}")
    print(f"Agent stats: {logger.get_agent_stats()}")

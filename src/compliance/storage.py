"""
SQLite Storage Backend — Append-only storage for audit events.

Events are written to a local SQLite database. Once written, events cannot
be modified or deleted (append-only / immutable). Optional forwarding to
a remote API endpoint is supported.
"""

import json
import logging
import sqlite3
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(__file__).parent.parent / "audit_events.db"

# SQL for creating the audit events table
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    timestamp TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    action_type TEXT NOT NULL,
    input_summary TEXT NOT NULL,
    output_summary TEXT NOT NULL,
    model_version TEXT NOT NULL,
    risk_score REAL NOT NULL,
    event_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_audit_events_agent ON audit_events(agent_name);
CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp ON audit_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_events_action ON audit_events(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_events_event_id ON audit_events(event_id);
"""

# Prevent any UPDATE or DELETE on the table
PREVENT_MODIFICATION_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS prevent_audit_update
BEFORE UPDATE ON audit_events
BEGIN
    SELECT RAISE(ABORT, 'Audit events are immutable — modification not allowed');
END;
"""

PREVENT_DELETE_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS prevent_audit_delete
BEFORE DELETE ON audit_events
BEGIN
    SELECT RAISE(ABORT, 'Audit events are immutable — deletion not allowed');
END;
"""


class SQLiteStorage:
    """
    Append-only SQLite storage for audit events.

    Events can only be written and read — never modified or deleted.
    This ensures immutability for compliance auditing.
    """

    def __init__(self, db_path: Optional[str] = None,
                 remote_api_url: Optional[str] = None,
                 remote_api_key: Optional[str] = None):
        """
        Initialize storage.

        Args:
            db_path: Path to SQLite database file. Defaults to audit_events.db.
            remote_api_url: Optional URL to forward events to a remote API.
            remote_api_key: Optional API key for remote forwarding.
        """
        self.db_path = db_path or str(DEFAULT_DB_PATH)
        self.remote_api_url = remote_api_url
        self.remote_api_key = remote_api_key
        self._init_db()

    def _init_db(self) -> None:
        """Create the database table and immutability triggers."""
        conn = sqlite3.connect(self.db_path)
        conn.executescript(CREATE_TABLE_SQL)
        conn.executescript(CREATE_INDEX_SQL)
        conn.executescript(PREVENT_MODIFICATION_TRIGGER)
        conn.executescript(PREVENT_DELETE_TRIGGER)
        conn.commit()
        conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def store_event(self, event_dict: Dict[str, Any]) -> str:
        """
        Store an audit event. Append-only — events cannot be overwritten.

        Args:
            event_dict: The audit event as a dictionary.

        Returns:
            The event_id of the stored event.

        Raises:
            sqlite3.IntegrityError: If event_id already exists.
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT INTO audit_events 
                   (event_id, timestamp, agent_name, action_type, input_summary,
                    output_summary, model_version, risk_score, event_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event_dict["event_id"],
                    event_dict["timestamp"],
                    event_dict["agent_name"],
                    event_dict["action_type"],
                    json.dumps(event_dict.get("input_summary", {})),
                    json.dumps(event_dict.get("output_summary", {})),
                    event_dict["model_version"],
                    event_dict["risk_score"],
                    json.dumps(event_dict),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

        # Forward to remote API if configured
        if self.remote_api_url:
            self._forward_to_remote(event_dict)

        return event_dict["event_id"]

    def _forward_to_remote(self, event_dict: Dict[str, Any]) -> None:
        """Forward event to remote API endpoint."""
        try:
            body = json.dumps(event_dict).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if self.remote_api_key:
                headers["Authorization"] = f"Bearer {self.remote_api_key}"
            req = urllib.request.Request(
                self.remote_api_url,
                data=body,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status != 200:
                    logger.warning(
                        f"Remote API returned status {resp.status} for event {event_dict.get('event_id')}"
                    )
        except Exception as e:
            logger.error(f"Failed to forward event to remote API: {e}")

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single event by event_id."""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT event_json FROM audit_events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            if row:
                return json.loads(row["event_json"])
            return None
        finally:
            conn.close()

    def get_events(self, agent_name: Optional[str] = None,
                   limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve audit events, optionally filtered by agent.

        Args:
            agent_name: Filter by agent name.
            limit: Maximum number of events to return.
            offset: Number of events to skip.

        Returns:
            List of event dictionaries.
        """
        conn = self._get_connection()
        try:
            if agent_name:
                rows = conn.execute(
                    "SELECT event_json FROM audit_events WHERE agent_name = ? "
                    "ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                    (agent_name, limit, offset),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT event_json FROM audit_events "
                    "ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                ).fetchall()
            return [json.loads(row["event_json"]) for row in rows]
        finally:
            conn.close()

    def count_events(self, agent_name: Optional[str] = None) -> int:
        """Count total events, optionally filtered by agent."""
        conn = self._get_connection()
        try:
            if agent_name:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM audit_events WHERE agent_name = ?",
                    (agent_name,),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM audit_events"
                ).fetchone()
            return row["cnt"]
        finally:
            conn.close()

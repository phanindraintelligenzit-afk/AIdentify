"""
Decision Logger Middleware — Automatic audit logging for AI agent decisions.

Provides the @audit_log() decorator, PII detection, SQLite storage,
and schema-conforming audit events for compliance (EU AI Act, GDPR, SOC 2).
"""

from compliance.models import (
    ActionType,
    AuditEvent,
    ConsentFlags,
    DataLineage,
    InputSummary,
    OutputSummary,
)
from compliance.audit_logger import AuditLogger
from compliance.decorator import audit_log
from compliance.pii_detector import scan_text
from compliance.storage import SQLiteStorage

__all__ = [
    "AuditEvent",
    "AuditLogger",
    "ActionType",
    "ConsentFlags",
    "DataLineage",
    "InputSummary",
    "OutputSummary",
    "SQLiteStorage",
    "audit_log",
    "scan_text",
]

__version__ = "1.0.0"

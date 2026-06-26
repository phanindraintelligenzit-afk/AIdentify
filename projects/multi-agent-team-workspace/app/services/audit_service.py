"""Audit service for recording actions."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models import AuditEntry, AssigneeType
from app.database import SessionLocal


def create_audit_entry(
    db: Session,
    actor: str,
    actor_type: AssigneeType,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    task_id: Optional[int] = None,
    details: Optional[dict] = None,
) -> AuditEntry:
    """Record an audit entry."""
    entry = AuditEntry(
        actor=actor,
        actor_type=actor_type,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        task_id=task_id,
        details=details,
        timestamp=datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_audit_trail(
    db: Session,
    task_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[List[AuditEntry], int]:
    """Query audit entries with optional filters. Returns (entries, total)."""
    query = db.query(AuditEntry)

    if task_id is not None:
        query = query.filter(AuditEntry.task_id == task_id)
    if entity_type is not None:
        query = query.filter(AuditEntry.entity_type == entity_type)
    if action is not None:
        query = query.filter(AuditEntry.action == action)

    total = query.count()
    entries = (
        query.order_by(AuditEntry.timestamp.desc()).offset(skip).limit(limit).all()
    )
    return entries, total

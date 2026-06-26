"""Handoff protocol service."""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models import (
    Task, Handoff, HandoffStatus, AssigneeType, TaskStatus
)
from app.schemas import HandoffCreate, HandoffAccept, HandoffReject
from app.services.audit_service import create_audit_entry


def initiate_handoff(db: Session, handoff_data: HandoffCreate, actor: str) -> Optional[Handoff]:
    """Initiate a handoff from current assignee to target assignee."""
    task = db.query(Task).filter(Task.id == handoff_data.task_id).first()
    if not task:
        return None

    if not task.assignee_name:
        raise ValueError("Cannot handoff an unassigned task")

    # Create handoff record
    handoff = Handoff(
        task_id=task.id,
        from_assignee=task.assignee_name,
        to_assignee=handoff_data.to_assignee,
        reason=handoff_data.reason,
        status=HandoffStatus.PENDING,
    )
    db.add(handoff)

    # Update task status
    task.status = TaskStatus.HANDOFF_PENDING
    db.commit()
    db.refresh(handoff)
    db.refresh(task)

    create_audit_entry(
        db=db,
        actor=actor,
        actor_type=task.assignee_type or AssigneeType.HUMAN,
        action="handoff.initiated",
        entity_type="handoff",
        entity_id=handoff.id,
        task_id=task.id,
        details={
            "from": task.assignee_name,
            "to": handoff_data.to_assignee,
            "reason": handoff_data.reason,
        },
    )

    return handoff


def accept_handoff(db: Session, handoff_id: int, accept_data: HandoffAccept, actor_type: AssigneeType = AssigneeType.HUMAN) -> Optional[Handoff]:
    """Accept a pending handoff. Transfers assignment to target."""
    handoff = db.query(Handoff).filter(Handoff.id == handoff_id).first()
    if not handoff:
        return None

    if handoff.status != HandoffStatus.PENDING:
        raise ValueError(f"Cannot accept handoff with status '{handoff.status.value}'")

    handoff.status = HandoffStatus.ACCEPTED
    handoff.resolved_at = datetime.utcnow()

    # Transfer task assignment
    task = handoff.task
    task.assignee_name = handoff.to_assignee
    # Keep original assignee_type if it was known, otherwise default based on target
    task.status = TaskStatus.IN_PROGRESS

    db.commit()
    db.refresh(handoff)
    db.refresh(task)

    create_audit_entry(
        db=db,
        actor=accept_data.accepted_by,
        actor_type=actor_type,
        action="handoff.accepted",
        entity_type="handoff",
        entity_id=handoff.id,
        task_id=task.id,
        details={
            "from": handoff.from_assignee,
            "to": handoff.to_assignee,
        },
    )

    return handoff


def reject_handoff(db: Session, handoff_id: int, reject_data: HandoffReject, actor_type: AssigneeType = AssigneeType.HUMAN) -> Optional[Handoff]:
    """Reject a pending handoff. Task returns to original assignee."""
    handoff = db.query(Handoff).filter(Handoff.id == handoff_id).first()
    if not handoff:
        return None

    if handoff.status != HandoffStatus.PENDING:
        raise ValueError(f"Cannot reject handoff with status '{handoff.status.value}'")

    handoff.status = HandoffStatus.REJECTED
    handoff.rejection_reason = reject_data.reason
    handoff.resolved_at = datetime.utcnow()

    # Reset task status
    task = handoff.task
    task.status = TaskStatus.IN_PROGRESS

    db.commit()
    db.refresh(handoff)
    db.refresh(task)

    create_audit_entry(
        db=db,
        actor=reject_data.rejected_by,
        actor_type=actor_type,
        action="handoff.rejected",
        entity_type="handoff",
        entity_id=handoff.id,
        task_id=task.id,
        details={
            "from": handoff.from_assignee,
            "to": handoff.to_assignee,
            "rejection_reason": reject_data.reason,
        },
    )

    return handoff


def get_handoff(db: Session, handoff_id: int) -> Optional[Handoff]:
    """Get a single handoff by ID."""
    return db.query(Handoff).filter(Handoff.id == handoff_id).first()


def get_pending_handoffs(db: Session, task_id: Optional[int] = None):
    """Get pending handoffs, optionally filtered by task."""
    query = db.query(Handoff).filter(Handoff.status == HandoffStatus.PENDING)
    if task_id is not None:
        query = query.filter(Handoff.task_id == task_id)
    return query.all()

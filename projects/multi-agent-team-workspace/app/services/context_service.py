"""Context service for shared task context."""

from typing import Optional
from sqlalchemy.orm import Session

from app.models import Task, AssigneeType
from app.services.audit_service import create_audit_entry


def update_context(db: Session, task_id: int, content: str, updated_by: str) -> Optional[Task]:
    """Update the shared context of a task and record audit."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return None

    old_context = task.context
    task.context = content
    db.commit()
    db.refresh(task)

    create_audit_entry(
        db=db,
        actor=updated_by,
        actor_type=AssigneeType.HUMAN,  # Could be determined from auth
        action="context.updated",
        entity_type="task",
        entity_id=task.id,
        task_id=task.id,
        details={"previous_length": len(old_context), "new_length": len(content)},
    )

    return task


def get_context(db: Session, task_id: int) -> Optional[Task]:
    """Get the shared context of a task."""
    return db.query(Task).filter(Task.id == task_id).first()

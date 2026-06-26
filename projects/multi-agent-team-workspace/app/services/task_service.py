"""Task service for CRUD operations."""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import asc

from app.models import Task, TaskStatus, AssigneeType
from app.schemas import TaskCreate, TaskUpdate, TaskAssign
from app.services.audit_service import create_audit_entry


def create_task(db: Session, task_data: TaskCreate) -> Task:
    """Create a new task and record audit."""
    task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        created_by=task_data.created_by,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    create_audit_entry(
        db=db,
        actor=task_data.created_by or "system",
        actor_type=AssigneeType.HUMAN,
        action="task.created",
        entity_type="task",
        entity_id=task.id,
        task_id=task.id,
        details={"title": task.title},
    )
    return task


def get_tasks(
    db: Session,
    status: Optional[TaskStatus] = None,
    assignee: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[List[Task], int]:
    """List tasks with optional filters."""
    query = db.query(Task)

    if status is not None:
        query = query.filter(Task.status == status)
    if assignee is not None:
        query = query.filter(Task.assignee_name == assignee)

    total = query.count()
    tasks = query.order_by(asc(Task.created_at)).offset(skip).limit(limit).all()
    return tasks, total


def get_task(db: Session, task_id: int) -> Optional[Task]:
    """Get a single task by ID."""
    return db.query(Task).filter(Task.id == task_id).first()


def update_task(db: Session, task_id: int, task_data: TaskUpdate, actor: str = "system") -> Optional[Task]:
    """Update a task and record audit."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return None

    update_data = task_data.model_dump(exclude_unset=True)
    changes = {}

    for field, value in update_data.items():
        old_value = getattr(task, field)
        if old_value != value:
            changes[field] = {"old": str(old_value), "new": str(value)}
            setattr(task, field, value)

    if changes:
        db.commit()
        db.refresh(task)

        create_audit_entry(
            db=db,
            actor=actor,
            actor_type=AssigneeType.HUMAN,
            action="task.updated",
            entity_type="task",
            entity_id=task.id,
            task_id=task.id,
            details={"changes": changes},
        )

    return task


def delete_task(db: Session, task_id: int, actor: str = "system") -> bool:
    """Delete a task and record audit."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return False

    create_audit_entry(
        db=db,
        actor=actor,
        actor_type=AssigneeType.HUMAN,
        action="task.deleted",
        entity_type="task",
        entity_id=task.id,
        task_id=task.id,
        details={"title": task.title},
    )

    db.delete(task)
    db.commit()
    return True


def assign_task(db: Session, task_id: int, assign_data: TaskAssign, actor: str = "system") -> Optional[Task]:
    """Assign a task to a human or agent and record audit."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return None

    old_assignee = task.assignee_name
    task.assignee_name = assign_data.assignee_name
    task.assignee_type = assign_data.assignee_type

    if task.status == TaskStatus.BACKLOG:
        task.status = TaskStatus.IN_PROGRESS

    db.commit()
    db.refresh(task)

    create_audit_entry(
        db=db,
        actor=actor,
        actor_type=AssigneeType.HUMAN,
        action="task.assigned",
        entity_type="task",
        entity_id=task.id,
        task_id=task.id,
        details={
            "from": old_assignee,
            "to": assign_data.assignee_name,
            "assignee_type": assign_data.assignee_type.value,
        },
    )

    return task

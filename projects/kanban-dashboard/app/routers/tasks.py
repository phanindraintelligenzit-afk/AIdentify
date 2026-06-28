"""
Task router - CRUD operations for tasks, labels, tags, and activity logs.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import verify_admin_key, verify_api_key
from app.database import get_db
from app.models import (
    ActivityLog,
    Column,
    Label,
    Tag,
    Task,
    TaskPriority,
    TaskStatus,
    task_labels,
    task_tags,
)
from app.schemas import (
    ActivityLogResponse,
    LabelCreate,
    LabelResponse,
    TagCreate,
    TagResponse,
    TaskBulkCreate,
    TaskBulkUpdate,
    TaskCreate,
    TaskMove,
    TaskResponse,
    TaskUpdate,
)
from app.services import trigger_webhooks
from app.websocket import manager

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


async def _get_task_with_relations(db: AsyncSession, task_id: int) -> Optional[Task]:
    """Fetch a task with all its relations loaded."""
    result = await db.execute(
        select(Task)
        .options(
            selectinload(Task.labels),
            selectinload(Task.tags),
        )
        .where(Task.id == task_id)
    )
    return result.scalar_one_or_none()


def _task_with_activity_response(task: Task) -> dict:
    """Convert task to response dict with activity count."""
    return {
        "id": task.id,
        "board_id": task.board_id,
        "column_id": task.column_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "assignee": task.assignee,
        "due_date": task.due_date,
        "position": task.position,
        "is_completed": task.is_completed,
        "labels": task.labels,
        "tags": task.tags,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


async def _log_activity(
    db: AsyncSession,
    task_id: int,
    action: str,
    description: str,
    agent: str = None,
):
    """Create an activity log entry."""
    log = ActivityLog(
        task_id=task_id,
        action=action,
        description=description,
        agent=agent,
    )
    db.add(log)


# ─── Labels ───────────────────────────────────────────────────────

@router.get("/labels", response_model=List[LabelResponse])
async def list_labels(
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """List all labels."""
    result = await db.execute(select(Label).order_by(Label.name))
    return result.scalars().all()


@router.post("/labels", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
async def create_label(
    data: LabelCreate,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_admin_key),
):
    """Create a label."""
    existing = await db.execute(select(Label).where(Label.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Label already exists")

    label = Label(name=data.name, color=data.color)
    db.add(label)
    await db.flush()
    await db.refresh(label)
    return label


# ─── Tags ─────────────────────────────────────────────────────────

@router.get("/tags", response_model=List[TagResponse])
async def list_tags(
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """List all tags."""
    result = await db.execute(select(Tag).order_by(Tag.name))
    return result.scalars().all()


@router.post("/tags", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_admin_key),
):
    """Create a tag."""
    existing = await db.execute(select(Tag).where(Tag.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tag already exists")

    tag = Tag(name=data.name)
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


# ─── Task CRUD ────────────────────────────────────────────────────

@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    board_id: Optional[int] = Query(None),
    column_id: Optional[int] = Query(None),
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    assignee: Optional[str] = Query(None),
    label_id: Optional[int] = Query(None),
    tag_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """List tasks with optional filters."""
    query = (
        select(Task)
        .options(
            selectinload(Task.labels),
            selectinload(Task.tags),
        )
    )

    if board_id:
        query = query.where(Task.board_id == board_id)
    if column_id:
        query = query.where(Task.column_id == column_id)
    if status:
        query = query.where(Task.status == status)
    if priority:
        query = query.where(Task.priority == priority)
    if assignee:
        query = query.where(Task.assignee == assignee)
    if label_id:
        query = query.where(Task.labels.any(Label.id == label_id))
    if tag_id:
        query = query.where(Task.tags.any(Tag.id == tag_id))
    if search:
        query = query.where(Task.title.ilike(f"%{search}%"))

    query = query.order_by(Task.position, Task.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """Get a single task."""
    task = await _get_task_with_relations(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """Create a new task."""
    # Determine board and column
    board_id = data.board_id
    column_id = data.column_id

    if not board_id:
        # Use first active board
        from app.models import Board
        result = await db.execute(
            select(Board).where(Board.is_active == True).order_by(Board.id)
        )
        board = result.scalar_one_or_none()
        if not board:
            raise HTTPException(status_code=400, detail="No active board found")
        board_id = board.id

    if not column_id:
        # Use first column of the board
        result = await db.execute(
            select(Column).where(Column.board_id == board_id).order_by(Column.position)
        )
        column = result.scalar_one_or_none()
        if not column:
            raise HTTPException(status_code=400, detail="No column found in board")
        column_id = column.id

    # Get max position in column
    from sqlalchemy import func
    pos_result = await db.execute(
        select(func.max(Task.position)).where(Task.column_id == column_id)
    )
    max_pos = pos_result.scalar() or 0

    task = Task(
        board_id=board_id,
        column_id=column_id,
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        assignee=data.assignee.value if hasattr(data.assignee, 'value') else data.assignee,
        due_date=data.due_date,
        position=max_pos + 1,
    )
    db.add(task)
    await db.flush()

    # Attach labels
    if data.label_ids:
        for label_id in data.label_ids:
            label_result = await db.execute(select(Label).where(Label.id == label_id))
            label = label_result.scalar_one_or_none()
            if label:
                task.labels.append(label)

    # Attach tags
    if data.tag_ids:
        for tag_id in data.tag_ids:
            tag_result = await db.execute(select(Tag).where(Tag.id == tag_id))
            tag = tag_result.scalar_one_or_none()
            if tag:
                task.tags.append(tag)

    # Log activity
    await _log_activity(db, task.id, "created", f"Task '{task.title}' created", auth.get("agent"))

    await db.refresh(task)
    await trigger_webhooks("task.created", _task_with_activity_response(task))

    # Broadcast
    await manager.broadcast_to_board(board_id, {
        "type": "task_created",
        "task": _task_with_activity_response(task),
    })

    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """Update a task."""
    task = await _get_task_with_relations(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = data.model_dump(exclude_unset=True)

    # Handle labels separately
    if "label_ids" in update_data:
        label_ids = update_data.pop("label_ids")
        task.labels.clear()
        if label_ids:
            for lid in label_ids:
                label_result = await db.execute(select(Label).where(Label.id == lid))
                label = label_result.scalar_one_or_none()
                if label:
                    task.labels.append(label)

    # Handle tags separately
    if "tag_ids" in update_data:
        tag_ids = update_data.pop("tag_ids")
        task.tags.clear()
        if tag_ids:
            for tid in tag_ids:
                tag_result = await db.execute(select(Tag).where(Tag.id == tid))
                tag = tag_result.scalar_one_or_none()
                if tag:
                    task.tags.append(tag)

    # Track status change for activity log
    old_status = task.status
    old_column_id = task.column_id

    # Apply updates
    for key, value in update_data.items:
        if hasattr(value, 'value'):
            value = value.value
        setattr(task, key, value)

    # Auto-set is_completed based on status
    if data.status == TaskStatus.DONE:
        task.is_completed = True
    elif data.status and data.status != TaskStatus.DONE:
        task.is_completed = False

    # Log activity
    changes = []
    if data.status and data.status != old_status:
        changes.append(f"status: {old_status.value} → {data.status.value}")
    if data.column_id and data.column_id != old_column_id:
        changes.append("moved to different column")
    if changes:
        await _log_activity(db, task.id, "updated", "; ".join(changes), auth.get("agent"))

    await db.flush()
    await db.refresh(task)

    task_data = _task_with_activity_response(task)
    await trigger_webhooks("task.updated", task_data)

    # Broadcast
    await manager.broadcast_to_board(task.board_id, {
        "type": "task_updated",
        "task": task_data,
    })

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """Delete a task."""
    task = await _get_task_with_relations(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    board_id = task.board_id
    task_title = task.title

    await db.delete(task)
    await trigger_webhooks("task.deleted", {"task_id": task_id, "title": task_title})

    await manager.broadcast_to_board(board_id, {
        "type": "task_deleted",
        "task_id": task_id,
    })


@router.post("/{task_id}/move", response_model=TaskResponse)
async def move_task(
    task_id: int,
    data: TaskMove,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """Move a task to a different column/position."""
    task = await _get_task_with_relations(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_column_id = task.column_id
    task.column_id = data.column_id
    task.position = data.position

    # Update status based on column
    column_result = await db.execute(select(Column).where(Column.id == data.column_id))
    column = column_result.scalar_one_or_none()
    if column:
        # Try to infer status from column name
        col_name_lower = column.name.lower()
        if "backlog" in col_name_lower or "todo" in col_name_lower:
            task.status = TaskStatus.BACKLOG
        elif "progress" in col_name_lower or "doing" in col_name_lower:
            task.status = TaskStatus.IN_PROGRESS
        elif "review" in col_name_lower:
            task.status = TaskStatus.REVIEW
        elif "done" in col_name_lower or "complete" in col_name_lower:
            task.status = TaskStatus.DONE
            task.is_completed = True

    await _log_activity(
        db, task.id, "moved",
        f"Moved from column {old_column_id} to {data.column_id}",
        auth.get("agent"),
    )

    await db.flush()
    await db.refresh(task)

    task_data = _task_with_activity_response(task)
    await manager.broadcast_to_board(task.board_id, {
        "type": "task_moved",
        "task": task_data,
    })

    return task


# ─── Bulk Operations ──────────────────────────────────────────────

@router.post("/bulk", response_model=List[TaskResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_tasks(
    data: TaskBulkCreate,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """Create multiple tasks at once."""
    created_tasks = []
    for task_data in data.tasks:
        # Same logic as create_task
        board_id = task_data.board_id
        column_id = task_data.column_id

        if not board_id:
            from app.models import Board
            result = await db.execute(
                select(Board).where(Board.is_active == True).order_by(Board.id)
            )
            board = result.scalar_one_or_none()
            if not board:
                continue
            board_id = board.id

        if not column_id:
            result = await db.execute(
                select(Column).where(Column.board_id == board_id).order_by(Column.position)
            )
            column = result.scalar_one_or_none()
            if not column:
                continue
            column_id = column.id

        from sqlalchemy import func
        pos_result = await db.execute(
            select(func.max(Task.position)).where(Task.column_id == column_id)
        )
        max_pos = pos_result.scalar() or 0

        task = Task(
            board_id=board_id,
            column_id=column_id,
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority,
            assignee=task_data.assignee.value if hasattr(task_data.assignee, 'value') else task_data.assignee,
            due_date=task_data.due_date,
            position=max_pos + 1,
        )
        db.add(task)
        await db.flush()

        if task_data.label_ids:
            for lid in task_data.label_ids:
                label_result = await db.execute(select(Label).where(Label.id == lid))
                label = label_result.scalar_one_or_none()
                if label:
                    task.labels.append(label)

        if task_data.tag_ids:
            for tid in task_data.tag_ids:
                tag_result = await db.execute(select(Tag).where(Tag.id == tid))
                tag = tag_result.scalar_one_or_none()
                if tag:
                    task.tags.append(tag)

        await _log_activity(db, task.id, "created", f"Bulk created", auth.get("agent"))
        created_tasks.append(task)

    for task in created_tasks:
        await db.refresh(task)

    await trigger_webhooks("task.bulk_created", {"count": len(created_tasks)})

    return created_tasks


@router.patch("/bulk", response_model=List[TaskResponse])
async def bulk_update_tasks(
    data: TaskBulkUpdate,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """Update multiple tasks at once."""
    result = await db.execute(
        select(Task).where(Task.id.in_(data.task_ids))
    )
    tasks = result.scalars().all()

    for task in tasks:
        update_data = data.model_dump(exclude_unset=True, exclude={"task_ids"})
        for key, value in update_data.items():
            if value is not None:
                if hasattr(value, 'value'):
                    value = value.value
                setattr(task, key, value)

        await _log_activity(db, task.id, "bulk_updated", "Bulk update applied", auth.get("agent"))

    affected_boards = set(t.board_id for t in tasks)
    for task in tasks:
        await db.refresh(task)

    await trigger_webhooks("task.bulk_updated", {"count": len(tasks)})

    # Broadcast to affected boards
    for board_id in affected_boards:
        await manager.broadcast_to_board(board_id, {
            "type": "tasks_bulk_updated",
            "task_ids": data.task_ids,
        })

    return tasks


# ─── Activity Log ─────────────────────────────────────────────────

@router.get("/{task_id}/activities", response_model=List[ActivityLogResponse])
async def get_task_activities(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """Get activity log for a task."""
    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.task_id == task_id)
        .order_by(ActivityLog.created_at.desc())
    )
    return result.scalars().all()

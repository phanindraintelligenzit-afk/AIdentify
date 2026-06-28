"""
Board router - CRUD operations for boards and columns.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import verify_admin_key, verify_api_key
from app.database import get_db
from app.models import Board, Column, Task
from app.schemas import (
    BoardCreate,
    BoardResponse,
    BoardStats,
    BoardUpdate,
    ColumnCreate,
    ColumnResponse,
    ColumnUpdate,
)
from app.services import trigger_webhooks
from app.websocket import manager

router = APIRouter(prefix="/api/boards", tags=["boards"])


@router.get("", response_model=List[BoardResponse])
async def list_boards(
    is_active: Optional[bool] = Query(True),
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """List all boards."""
    query = select(Board).options(selectinload(Board.columns))
    if is_active is not None:
        query = query.where(Board.is_active == is_active)
    query = query.order_by(Board.created_at.desc())
    result = await db.execute(query)
    boards = result.scalars().all()

    # Attach task counts
    response = []
    for board in boards:
        task_count_result = await db.execute(
            select(func.count(Task.id)).where(Task.board_id == board.id)
        )
        board.task_count = task_count_result.scalar()
        response.append(board)

    return response


@router.get("/{board_id}", response_model=BoardResponse)
async def get_board(
    board_id: int,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """Get a single board with its columns."""
    result = await db.execute(
        select(Board)
        .options(selectinload(Board.columns))
        .where(Board.id == board_id)
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    task_count_result = await db.execute(
        select(func.count(Task.id)).where(Task.board_id == board.id)
    )
    board.task_count = task_count_result.scalar()
    return board


@router.post("", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    data: BoardCreate,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_admin_key),
):
    """Create a new board."""
    # Check slug uniqueness
    existing = await db.execute(
        select(Board).where(Board.slug == data.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slug already exists")

    board = Board(
        name=data.name,
        description=data.description,
        slug=data.slug,
    )
    db.add(board)
    await db.flush()

    # Create default columns if provided, else create standard ones
    if data.columns:
        for i, col in enumerate(data.columns):
            column = Column(
                board_id=board.id,
                name=col.name,
                position=col.position if col.position else i,
                color=col.color,
            )
            db.add(column)
    else:
        default_columns = [
            ("Backlog", 0, "#6b7280"),
            ("In Progress", 1, "#3b82f6"),
            ("Review", 2, "#f59e0b"),
            ("Done", 3, "#10b981"),
        ]
        for name, pos, color in default_columns:
            db.add(Column(board_id=board.id, name=name, position=pos, color=color))

    await db.refresh(board)
    await trigger_webhooks("board.created", {"board_id": board.id, "name": board.name})
    return board


@router.patch("/{board_id}", response_model=BoardResponse)
async def update_board(
    board_id: int,
    data: BoardUpdate,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_admin_key),
):
    """Update a board."""
    result = await db.execute(
        select(Board).options(selectinload(Board.columns)).where(Board.id == board_id)
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(board, key, value)

    await db.flush()
    await db.refresh(board)
    await trigger_webhooks("board.updated", {"board_id": board.id, "changes": update_data})

    # Broadcast via WebSocket
    await manager.broadcast_to_board(board_id, {
        "type": "board_updated",
        "board_id": board_id,
    })

    # Refresh to load updated_at
    task_count_result = await db.execute(
        select(func.count(Task.id)).where(Task.board_id == board.id)
    )
    board.task_count = task_count_result.scalar()
    return board


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: int,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_admin_key),
):
    """Delete a board."""
    result = await db.execute(select(Board).where(Board.id == board_id))
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    await db.delete(board)
    await trigger_webhooks("board.deleted", {"board_id": board_id})


@router.get("/{board_id}/stats", response_model=BoardStats)
async def get_board_stats(
    board_id: int,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_api_key),
):
    """Get statistics for a board."""
    from datetime import datetime

    from app.models import TaskStatus, TaskPriority

    # Verify board exists
    result = await db.execute(select(Board).where(Board.id == board_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Board not found")

    # Total tasks
    total_result = await db.execute(
        select(func.count(Task.id)).where(Task.board_id == board_id)
    )
    total = total_result.scalar()

    # By status
    by_status = {}
    for status in TaskStatus:
        count_result = await db.execute(
            select(func.count(Task.id)).where(
                Task.board_id == board_id, Task.status == status
            )
        )
        by_status[status.value] = count_result.scalar()

    # By assignee
    by_assignee_result = await db.execute(
        select(Task.assignee, func.count(Task.id))
        .where(Task.board_id == board_id)
        .group_by(Task.assignee)
    )
    by_assignee = {row[0] or "unassigned": row[1] for row in by_assignee_result.all()}

    # By priority
    by_priority = {}
    for priority in TaskPriority:
        count_result = await db.execute(
            select(func.count(Task.id)).where(
                Task.board_id == board_id, Task.priority == priority
            )
        )
        by_priority[priority.value] = count_result.scalar()

    # Overdue
    overdue_result = await db.execute(
        select(func.count(Task.id)).where(
            Task.board_id == board_id,
            Task.due_date < datetime.utcnow(),
            Task.status != TaskStatus.DONE,
        )
    )

    return BoardStats(
        total_tasks=total,
        by_status=by_status,
        by_assignee=by_assignee,
        by_priority=by_priority,
        overdue_count=overdue_result.scalar(),
    )


# ─── Column endpoints ────────────────────────────────────────────

@router.post("/{board_id}/columns", response_model=ColumnResponse, status_code=status.HTTP_201_CREATED)
async def create_column(
    board_id: int,
    data: ColumnCreate,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_admin_key),
):
    """Add a column to a board."""
    result = await db.execute(select(Board).where(Board.id == board_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Board not found")

    column = Column(
        board_id=board_id,
        name=data.name,
        position=data.position,
        color=data.color,
    )
    db.add(column)
    await db.flush()
    await db.refresh(column)
    return column


@router.patch("/{board_id}/columns/{column_id}", response_model=ColumnResponse)
async def update_column(
    board_id: int,
    column_id: int,
    data: ColumnUpdate,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_admin_key),
):
    """Update a column."""
    result = await db.execute(
        select(Column).where(Column.id == column_id, Column.board_id == board_id)
    )
    column = result.scalar_one_or_none()
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(column, key, value)

    await db.flush()
    return column


@router.delete("/{board_id}/columns/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column(
    board_id: int,
    column_id: int,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(verify_admin_key),
):
    """Delete a column."""
    result = await db.execute(
        select(Column).where(Column.id == column_id, Column.board_id == board_id)
    )
    column = result.scalar_one_or_none()
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")

    await db.delete(column)

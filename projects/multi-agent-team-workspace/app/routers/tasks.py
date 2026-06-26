"""Task CRUD router."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TaskStatus
from app.schemas import (
    TaskCreate, TaskUpdate, TaskAssign, TaskResponse, TaskListResponse
)
from app.services import task_service

router = APIRouter(tags=["tasks"])


@router.post("/tasks/", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    return task_service.create_task(db, task)


@router.get("/tasks/", response_model=TaskListResponse)
def list_tasks(
    status: Optional[TaskStatus] = None,
    assignee: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List all tasks with optional filters."""
    tasks, total = task_service.get_tasks(db, status, assignee, skip, limit)
    return TaskListResponse(tasks=tasks, total=total)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task by ID."""
    task = task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task: TaskUpdate,
    actor: str = Query("system"),
    db: Session = Depends(get_db),
):
    """Update a task."""
    updated = task_service.update_task(db, task_id, task, actor)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    actor: str = Query("system"),
    db: Session = Depends(get_db),
):
    """Delete a task."""
    deleted = task_service.delete_task(db, task_id, actor)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/tasks/{task_id}/assign", response_model=TaskResponse)
def assign_task(
    task_id: int,
    assign: TaskAssign,
    actor: str = Query("system"),
    db: Session = Depends(get_db),
):
    """Assign a task to a human or AI agent."""
    task = task_service.assign_task(db, task_id, assign, actor)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

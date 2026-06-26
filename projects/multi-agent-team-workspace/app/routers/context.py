"""Shared context router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ContextUpdate, ContextResponse
from app.services import context_service

router = APIRouter(tags=["context"])


@router.get("/context/{task_id}", response_model=ContextResponse)
def get_context(task_id: int, db: Session = Depends(get_db)):
    """Get the shared context for a task."""
    task = context_service.get_context(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return ContextResponse(task_id=task.id, context=task.context, updated_at=task.updated_at)


@router.post("/context/{task_id}", response_model=ContextResponse)
def update_context(
    task_id: int,
    context: ContextUpdate,
    db: Session = Depends(get_db),
):
    """Update the shared context for a task."""
    task = context_service.update_context(db, task_id, context.content, context.updated_by)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return ContextResponse(task_id=task.id, context=task.context, updated_at=task.updated_at)

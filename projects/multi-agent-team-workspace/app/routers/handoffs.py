"""Handoff protocol router."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AssigneeType
from app.schemas import (
    HandoffCreate, HandoffAccept, HandoffReject, HandoffResponse
)
from app.services import handoff_service

router = APIRouter(tags=["handoffs"])


@router.post("/handoffs/", response_model=HandoffResponse, status_code=201)
def initiate_handoff(
    handoff: HandoffCreate,
    actor: str = Query(...),
    db: Session = Depends(get_db),
):
    """Initiate a handoff to transfer task between assignees."""
    try:
        result = handoff_service.initiate_handoff(db, handoff, actor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.post("/handoffs/{handoff_id}/accept", response_model=HandoffResponse)
def accept_handoff(
    handoff_id: int,
    accept: HandoffAccept,
    db: Session = Depends(get_db),
):
    """Accept a pending handoff."""
    try:
        result = handoff_service.accept_handoff(db, handoff_id, accept)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result:
        raise HTTPException(status_code=404, detail="Handoff not found")
    return result


@router.post("/handoffs/{handoff_id}/reject", response_model=HandoffResponse)
def reject_handoff(
    handoff_id: int,
    reject: HandoffReject,
    db: Session = Depends(get_db),
):
    """Reject a pending handoff."""
    try:
        result = handoff_service.reject_handoff(db, handoff_id, reject)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result:
        raise HTTPException(status_code=404, detail="Handoff not found")
    return result


@router.get("/handoffs/{handoff_id}", response_model=HandoffResponse)
def get_handoff(handoff_id: int, db: Session = Depends(get_db)):
    """Get a specific handoff by ID."""
    handoff = handoff_service.get_handoff(db, handoff_id)
    if not handoff:
        raise HTTPException(status_code=404, detail="Handoff not found")
    return handoff

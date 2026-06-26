"""Audit trail router."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AuditEntryResponse, AuditTrailResponse
from app.services.audit_service import get_audit_trail

router = APIRouter(tags=["audit"])


@router.get("/audit/", response_model=AuditTrailResponse)
def audit_trail(
    task_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get the audit trail with optional filters."""
    entries, total = get_audit_trail(db, task_id, entity_type, action, skip, limit)
    return AuditTrailResponse(entries=entries, total=total)

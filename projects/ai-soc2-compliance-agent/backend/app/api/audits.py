"""Audit management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models import Audit, AuditStatus
from schemas import AuditCreate, AuditListResponse, AuditResponse, AuditUpdate

router = APIRouter()


@router.get("", response_model=AuditListResponse)
async def list_audits(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: AuditStatus = None,
    db: AsyncSession = Depends(get_db),
):
    """List all audit engagements."""
    query = select(Audit)
    if status:
        query = query.where(Audit.status == status)
    query = query.order_by(Audit.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    count_query = select(Audit)
    if status:
        count_query = count_query.where(Audit.status == status)
    total = len((await db.execute(count_query)).scalars().all())

    return AuditListResponse(
        total=total,
        items=[AuditResponse.model_validate(a) for a in items],
    )


@router.post("", response_model=AuditResponse, status_code=201)
async def create_audit(data: AuditCreate, db: AsyncSession = Depends(get_db)):
    """Create a new audit engagement."""
    audit = Audit(**data.model_dump())
    db.add(audit)
    await db.commit()
    await db.refresh(audit)
    return audit


@router.get("/{audit_id}", response_model=AuditResponse)
async def get_audit(audit_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific audit."""
    result = await db.execute(select(Audit).where(Audit.id == audit_id))
    audit = result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audit


@router.patch("/{audit_id}", response_model=AuditResponse)
async def update_audit(
    audit_id: int, data: AuditUpdate, db: AsyncSession = Depends(get_db)
):
    """Update audit details."""
    result = await db.execute(select(Audit).where(Audit.id == audit_id))
    audit = result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(audit, key, value)

    await db.commit()
    await db.refresh(audit)
    return audit


@router.delete("/{audit_id}", status_code=204)
async def delete_audit(audit_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an audit."""
    result = await db.execute(select(Audit).where(Audit.id == audit_id))
    audit = result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    await db.delete(audit)
    await db.commit()


@router.post("/{audit_id}/update-progress", response_model=AuditResponse)
async def update_audit_progress(
    audit_id: int, percentage: float = Query(..., ge=0, le=100), db: AsyncSession = Depends(get_db)
):
    """Update audit completion percentage."""
    result = await db.execute(select(Audit).where(Audit.id == audit_id))
    audit = result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    audit.completion_percentage = percentage
    if percentage >= 100:
        audit.status = AuditStatus.COMPLETE

    await db.commit()
    await db.refresh(audit)
    return audit

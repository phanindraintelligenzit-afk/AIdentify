"""SOC2 compliance control CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models import ComplianceControl, ControlStatus
from schemas import (
    ComplianceControlCreate,
    ComplianceControlListResponse,
    ComplianceControlResponse,
    ComplianceControlUpdate,
)

router = APIRouter()


@router.get("", response_model=ComplianceControlListResponse)
async def list_controls(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: str = None,
    status: ControlStatus = None,
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """List all SOC2 compliance controls."""
    query = select(ComplianceControl)
    if active_only:
        query = query.where(ComplianceControl.is_active == True)  # noqa: E712
    if category:
        query = query.where(ComplianceControl.category == category)
    if status:
        query = query.where(ComplianceControl.status == status)
    query = query.order_by(ComplianceControl.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    count_query = select(ComplianceControl)
    if active_only:
        count_query = count_query.where(ComplianceControl.is_active == True)  # noqa: E712
    if category:
        count_query = count_query.where(ComplianceControl.category == category)
    if status:
        count_query = count_query.where(ComplianceControl.status == status)
    total = len((await db.execute(count_query)).scalars().all())

    return ComplianceControlListResponse(
        total=total,
        items=[ComplianceControlResponse.model_validate(c) for c in items],
    )


@router.post("", response_model=ComplianceControlResponse, status_code=201)
async def create_control(data: ComplianceControlCreate, db: AsyncSession = Depends(get_db)):
    """Create a new compliance control."""
    control = ComplianceControl(**data.model_dump())
    db.add(control)
    await db.commit()
    await db.refresh(control)
    return control


@router.get("/{control_id}", response_model=ComplianceControlResponse)
async def get_control(control_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific compliance control."""
    result = await db.execute(
        select(ComplianceControl).where(ComplianceControl.id == control_id)
    )
    control = result.scalar_one_or_none()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    return control


@router.patch("/{control_id}", response_model=ComplianceControlResponse)
async def update_control(
    control_id: int, data: ComplianceControlUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a compliance control."""
    result = await db.execute(
        select(ComplianceControl).where(ComplianceControl.id == control_id)
    )
    control = result.scalar_one_or_none()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(control, key, value)

    await db.commit()
    await db.refresh(control)
    return control


@router.delete("/{control_id}", status_code=204)
async def delete_control(control_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a compliance control and all its evidence."""
    result = await db.execute(
        select(ComplianceControl).where(ComplianceControl.id == control_id)
    )
    control = result.scalar_one_or_none()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    await db.delete(control)
    await db.commit()

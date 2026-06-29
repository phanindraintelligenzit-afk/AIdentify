"""Evidence collection and management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models import ComplianceControl, Evidence, EvidenceType
from schemas import (
    EvidenceCreate,
    EvidenceListResponse,
    EvidenceResponse,
    EvidenceUpdate,
)

router = APIRouter()


@router.get("", response_model=EvidenceListResponse)
async def list_evidence(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    control_id: int = None,
    evidence_type: EvidenceType = None,
    valid_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """List collected evidence."""
    query = select(Evidence)
    if control_id:
        query = query.where(Evidence.control_id == control_id)
    if evidence_type:
        query = query.where(Evidence.evidence_type == evidence_type)
    if valid_only:
        query = query.where(Evidence.is_valid == True)  # noqa: E712
    query = query.order_by(Evidence.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    evidence_items = result.scalars().all()

    total_query = select(Evidence)
    if control_id:
        total_query = total_query.where(Evidence.control_id == control_id)
    if evidence_type:
        total_query = total_query.where(Evidence.evidence_type == evidence_type)
    if valid_only:
        total_query = total_query.where(Evidence.is_valid == True)  # noqa: E712
    total = len((await db.execute(total_query)).scalars().all())

    # Enrich with control name
    items = []
    for e in evidence_items:
        control_result = await db.execute(
            select(ComplianceControl.name).where(ComplianceControl.id == e.control_id)
        )
        control_name = control_result.scalar_one_or_none() or ""
        data = {**e.__dict__, "control_name": control_name}
        items.append(EvidenceResponse.model_validate(data))

    return EvidenceListResponse(total=total, items=items)


@router.post("", response_model=EvidenceResponse, status_code=201)
async def create_evidence(data: EvidenceCreate, db: AsyncSession = Depends(get_db)):
    """Upload/attach evidence to a control."""
    # Verify control exists
    control_result = await db.execute(
        select(ComplianceControl).where(ComplianceControl.id == data.control_id)
    )
    control = control_result.scalar_one_or_none()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    evidence = Evidence(**data.model_dump())
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)

    return EvidenceResponse.model_validate(
        {**evidence.__dict__, "control_name": control.name}
    )


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(evidence_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific evidence item."""
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    control_result = await db.execute(
        select(ComplianceControl.name).where(ComplianceControl.id == evidence.control_id)
    )
    control_name = control_result.scalar_one_or_none() or ""
    return EvidenceResponse.model_validate(
        {**evidence.__dict__, "control_name": control_name}
    )


@router.patch("/{evidence_id}", response_model=EvidenceResponse)
async def update_evidence(
    evidence_id: int, data: EvidenceUpdate, db: AsyncSession = Depends(get_db)
):
    """Update evidence metadata."""
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(evidence, key, value)

    await db.commit()
    await db.refresh(evidence)

    control_result = await db.execute(
        select(ComplianceControl.name).where(ComplianceControl.id == evidence.control_id)
    )
    control_name = control_result.scalar_one_or_none() or ""
    return EvidenceResponse.model_validate(
        {**evidence.__dict__, "control_name": control_name}
    )


@router.delete("/{evidence_id}", status_code=204)
async def delete_evidence(evidence_id: int, db: AsyncSession = Depends(get_db)):
    """Delete evidence."""
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    await db.delete(evidence)
    await db.commit()

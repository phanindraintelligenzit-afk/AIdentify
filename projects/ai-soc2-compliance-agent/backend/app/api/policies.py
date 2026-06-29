"""Security policy management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models import Policy
from schemas import PolicyCreate, PolicyListResponse, PolicyResponse, PolicyUpdate

router = APIRouter()


@router.get("", response_model=PolicyListResponse)
async def list_policies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str = None,
    policy_type: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List all security policies."""
    query = select(Policy)
    if status:
        query = query.where(Policy.status == status)
    if policy_type:
        query = query.where(Policy.policy_type == policy_type)
    query = query.order_by(Policy.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    count_query = select(Policy)
    if status:
        count_query = count_query.where(Policy.status == status)
    if policy_type:
        count_query = count_query.where(Policy.policy_type == policy_type)
    total = len((await db.execute(count_query)).scalars().all())

    return PolicyListResponse(
        total=total,
        items=[PolicyResponse.model_validate(p) for p in items],
    )


@router.post("", response_model=PolicyResponse, status_code=201)
async def create_policy(data: PolicyCreate, db: AsyncSession = Depends(get_db)):
    """Create a new security policy."""
    policy = Policy(**data.model_dump())
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific policy."""
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.patch("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: int, data: PolicyUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a policy."""
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(policy, key, value)

    await db.commit()
    await db.refresh(policy)
    return policy


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(policy_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a policy."""
    result = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    await db.delete(policy)
    await db.commit()

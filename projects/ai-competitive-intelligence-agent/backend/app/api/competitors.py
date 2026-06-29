"""Competitor CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models import Competitor
from schemas import CompetitorCreate, CompetitorListResponse, CompetitorResponse, CompetitorUpdate

router = APIRouter()


@router.get("", response_model=CompetitorListResponse)
async def list_competitors(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """List all tracked competitors."""
    query = select(Competitor)
    if active_only:
        query = query.where(Competitor.is_active == True)  # noqa: E712
    query = query.order_by(Competitor.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    count_query = select(Competitor)
    if active_only:
        count_query = count_query.where(Competitor.is_active == True)  # noqa: E712
    total = len((await db.execute(count_query)).scalars().all())

    return CompetitorListResponse(total=total, items=[CompetitorResponse.model_validate(c) for c in items])


@router.post("", response_model=CompetitorResponse, status_code=201)
async def create_competitor(data: CompetitorCreate, db: AsyncSession = Depends(get_db)):
    """Add a new competitor to monitor."""
    competitor = Competitor(**data.model_dump())
    db.add(competitor)
    await db.commit()
    await db.refresh(competitor)
    return competitor


@router.get("/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor(competitor_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific competitor."""
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor


@router.patch("/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(
    competitor_id: int, data: CompetitorUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a competitor's monitoring settings."""
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(competitor, key, value)

    await db.commit()
    await db.refresh(competitor)
    return competitor


@router.delete("/{competitor_id}", status_code=204)
async def delete_competitor(competitor_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a competitor and all its data."""
    result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    competitor = result.scalar_one_or_none()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    await db.delete(competitor)
    await db.commit()

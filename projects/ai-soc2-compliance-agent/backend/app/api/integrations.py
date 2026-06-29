"""Third-party integration management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models import Integration
from schemas import (
    IntegrationCreate,
    IntegrationListResponse,
    IntegrationResponse,
    IntegrationUpdate,
)

router = APIRouter()


@router.get("", response_model=IntegrationListResponse)
async def list_integrations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    provider: str = None,
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
):
    """List all connected integrations."""
    query = select(Integration)
    if active_only:
        query = query.where(Integration.is_active == True)  # noqa: E712
    if provider:
        query = query.where(Integration.provider == provider)
    query = query.order_by(Integration.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    count_query = select(Integration)
    if active_only:
        count_query = count_query.where(Integration.is_active == True)  # noqa: E712
    if provider:
        count_query = count_query.where(Integration.provider == provider)
    total = len((await db.execute(count_query)).scalars().all())

    return IntegrationListResponse(
        total=total,
        items=[IntegrationResponse.model_validate(i) for i in items],
    )


@router.post("", response_model=IntegrationResponse, status_code=201)
async def create_integration(data: IntegrationCreate, db: AsyncSession = Depends(get_db)):
    """Connect a third-party integration."""
    integration = Integration(**data.model_dump())
    db.add(integration)
    await db.commit()
    await db.refresh(integration)
    return integration


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(integration_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific integration."""
    result = await db.execute(
        select(Integration).where(Integration.id == integration_id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return integration


@router.patch("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: int, data: IntegrationUpdate, db: AsyncSession = Depends(get_db)
):
    """Update integration settings."""
    result = await db.execute(
        select(Integration).where(Integration.id == integration_id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(integration, key, value)

    await db.commit()
    await db.refresh(integration)
    return integration


@router.delete("/{integration_id}", status_code=204)
async def delete_integration(integration_id: int, db: AsyncSession = Depends(get_db)):
    """Disconnect an integration."""
    result = await db.execute(
        select(Integration).where(Integration.id == integration_id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    await db.delete(integration)
    await db.commit()


@router.post("/{integration_id}/sync", response_model=IntegrationResponse)
async def sync_integration(integration_id: int, db: AsyncSession = Depends(get_db)):
    """Manually trigger a sync for an integration."""
    from datetime import datetime

    result = await db.execute(
        select(Integration).where(Integration.id == integration_id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    integration.last_sync_at = datetime.utcnow()
    await db.commit()
    await db.refresh(integration)
    return integration

"""Signal detection and management endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models import Competitor, Signal, SignalSeverity, SignalType
from schemas import SignalListResponse, SignalMarkRead, SignalResponse

router = APIRouter()


@router.get("", response_model=SignalListResponse)
async def list_signals(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    severity: SignalType = None,
    unread_only: bool = Query(False),
    competitor_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List detected competitive signals."""
    query = select(Signal)

    if unread_only:
        query = query.where(Signal.is_read == False)  # noqa: E712
    if competitor_id:
        query = query.where(Signal.competitor_id == competitor_id)

    query = query.order_by(Signal.detected_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    signals = result.scalars().all()

    # Count unread
    unread_count = await db.execute(
        select(func.count(Signal.id)).where(Signal.is_read == False)  # noqa: E712
    )
    unread = unread_count.scalar()

    # Total count
    total_count = await db.execute(select(func.count(Signal.id)))
    total = total_count.scalar()

    # Enrich with competitor name
    items = []
    for s in signals:
        comp_result = await db.execute(select(Competitor.name).where(Competitor.id == s.competitor_id))
        comp_name = comp_result.scalar_one_or_none() or ""
        data = {**s.__dict__, "competitor_name": comp_name}
        items.append(SignalResponse.model_validate(data))

    return SignalListResponse(total=total, unread=unread, items=items)


@router.post("/mark-read")
async def mark_signals_read(data: SignalMarkRead, db: AsyncSession = Depends(get_db)):
    """Mark signals as read."""
    for signal_id in data.signal_ids:
        result = await db.execute(select(Signal).where(Signal.id == signal_id))
        signal = result.scalar_one_or_none()
        if signal:
            signal.is_read = True
    await db.commit()
    return {"updated": len(data.signal_ids)}


@router.get("/feed")
async def signal_feed(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Get recent signals as a feed (for dashboard)."""
    since = datetime.utcnow() - timedelta(hours=hours)
    result = await db.execute(
        select(Signal).where(Signal.detected_at >= since).order_by(Signal.detected_at.desc())
    )
    signals = result.scalars().all()

    items = []
    for s in signals:
        comp_result = await db.execute(select(Competitor.name).where(Competitor.id == s.competitor_id))
        comp_name = comp_result.scalar_one_or_none() or ""
        data = {**s.__dict__, "competitor_name": comp_name}
        items.append(SignalResponse.model_validate(data))

    return {"period_hours": hours, "total": len(items), "items": items}

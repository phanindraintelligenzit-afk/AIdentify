"""Briefing/digest generation endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models import Briefing, Competitor, Signal
from schemas import BriefingCreate, BriefingResponse

router = APIRouter()


@router.get("", response_model=list[BriefingResponse])
async def list_briefings(db: AsyncSession = Depends(get_db)):
    """List all briefings."""
    result = await db.execute(select(Briefing).order_by(Briefing.created_at.desc()))
    briefings = result.scalars().all()
    return [BriefingResponse.model_validate(b) for b in briefings]


@router.post("/generate", response_model=BriefingResponse, status_code=201)
async def generate_briefing(data: BriefingCreate, db: AsyncSession = Depends(get_db)):
    """Generate a competitive briefing for a time period."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=data.period_days)

    # Get signals in period
    signals_result = await db.execute(
        select(Signal)
        .where(Signal.detected_at >= start_date, Signal.detected_at <= end_date)
        .order_by(Signal.detected_at.desc())
    )
    signals = signals_result.scalars().all()

    # Get unique competitor IDs
    competitor_ids = list(set(s.competitor_id for s in signals))

    # Build summary
    signal_count_by_type: dict[str, int] = []
    for s in signals:
        signal_count_by_type[s.signal_type.value] = signal_count_by_type.get(s.signal_type.value, 0) + 1

    summary_parts = [
        f"## Competitive Briefing: {start_date.strftime('%b %d')} — {end_date.strftime('%b %d, %Y')}",
        f"",
        f"**{len(signals)} signals** detected across **{len(competitor_ids)} competitors**.",
        f"",
    ]

    if signal_count_by_type:
        summary_parts.append("### Signal Breakdown")
        for sig_type, count in sorted(signal_count_by_type.items(), key=lambda x: -x[1]):
            summary_parts.append(f"- **{sig_type}**: {count}")
        summary_parts.append("")

    # Highlight critical/high signals
    critical_signals = [s for s in signals if s.severity in ("critical", "high")]
    if critical_signals:
        summary_parts.append("### ⚠️ High Priority Signals")
        for s in critical_signals[:5]:
            summary_parts.append(f"- [{s.severity.upper()}] {s.title}")
        summary_parts.append("")

    if not signals:
        summary_parts.append("*No signals detected in this period. Add more competitors or extend the time range.*")

    briefing = Briefing(
        title=data.title or f"Competitive Briefing — {end_date.strftime('%b %d, %Y')}",
        summary="\n".join(summary_parts),
        signal_ids=[s.id for s in signals],
        competitor_ids=competitor_ids,
        period_start=start_date,
        period_end=end_date,
    )
    db.add(briefing)
    await db.commit()
    await db.refresh(briefing)

    return BriefingResponse.model_validate(briefing)


@router.get("/{briefing_id}", response_model=BriefingResponse)
async def get_briefing(briefing_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific briefing."""
    result = await db.execute(select(Briefing).where(Briefing.id == briefing_id))
    briefing = result.scalar_one_or_none()
    if not briefing:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Briefing not found")
    return BriefingResponse.model_validate(briefing)

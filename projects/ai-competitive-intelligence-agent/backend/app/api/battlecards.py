"""Battlecard generation and management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models import Battlecard, Competitor, Signal
from schemas import (
    BattlecardCreate,
    BattlecardGenerateRequest,
    BattlecardResponse,
)

router = APIRouter()


def _generate_battlecard_ai(competitor: Competitor, signals: list[Signal]) -> dict:
    """Generate battlecard content using signal data (AI-simulated)."""
    # Extract signal insights
    pricing_signals = [s for s in signals if s.signal_type == "pricing_change"]
    product_signals = [s for s in signals if s.signal_type == "product_launch"]
    review_signals = [s for s in signals if s.signal_type == "review_update"]
    job_signals = [s for s in signals if s.signal_type == "job_posting"]

    strengths = []
    weaknesses = []
    win_strategies = []
    differentiators = []

    # Analyze signals for patterns
    if pricing_signals:
        strengths.append(f"Active pricing strategy — {len(pricing_signals)} changes detected")
        win_strategies.append("Emphasize pricing flexibility and transparent billing")

    if product_signals:
        strengths.append(f"Product velocity — {len(product_signals)} launches tracked")
        differentiators.append("Our release cadence and feature depth")

    if review_signals:
        review_texts = [s.title for s in review_signals[:3]]
        weaknesses.append(f"Review themes: {', '.join(review_texts)}")

    if job_signals:
        strengths.append(f"Growing team — {len(job_signings)} new roles posted" if (job_signals := job_signals) else "")
        win_strategies.append("They're hiring rapidly — likely scaling, may have onboarding gaps")

    # Default content if no signals yet
    if not strengths:
        strengths = ["Established market presence", "Recognized brand in their segment"]
    if not weaknesses:
        weaknesses = ["Limited public signal data — monitor for 2+ weeks"]
    if not win_strategies:
        win_strategies = [
            "Focus on our unique differentiators",
            "Leverage customer success stories",
            "Highlight integration capabilities",
        ]
    if not differentiators:
        differentiators = [
            "Superior customer support",
            "Faster implementation time",
            "Better integration ecosystem",
        ]

    return {
        "title": f"Battlecard: {competitor.name}",
        "overview": f"Competitive intelligence for {competitor.name} ({competitor.domain}). "
        f"Based on {len(signals)} tracked signals.",
        "strengths": strengths,
        "weaknesses": weaknesses,
        "win_strategies": win_strategies,
        "loss_risks": [
            "They may undercut on pricing",
            "Feature parity in core areas",
            "Stronger brand recognition in some segments",
        ],
        "key_differentiators": differentiators,
        "pricing_intel": f"Pricing signals detected: {len(pricing_signals)}. "
        "Monitor their pricing page for changes.",
        "target_accounts": [],
        "objection_handlers": {
            "They're cheaper": "Total cost of ownership favors us when factoring support and integrations",
            "They have more features": "We focus on depth in core workflows, not breadth",
            "They're the market leader": "Leaders move slowly; we ship faster and listen to customers",
        },
        "talk_track": f"When competing against {competitor.name}, emphasize our agility, "
        "customer-centric approach, and faster time-to-value. "
        "Reference specific customer wins in their segment.",
    }


@router.get("", response_model=list[BattlecardResponse])
async def list_battlecards(
    competitor_id: int = None,
    published_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List all battlecards."""
    query = select(Battlecard)
    if competitor_id:
        query = query.where(Battlecard.competitor_id == competitor_id)
    if published_only:
        query = query.where(Battlecard.is_published == True)  # noqa: E712
    query = query.order_by(Battlecard.updated_at.desc())

    result = await db.execute(query)
    cards = result.scalars().all()

    items = []
    for card in cards:
        comp_result = await db.execute(select(Competitor.name).where(Competitor.id == card.competitor_id))
        comp_name = comp_result.scalar_one_or_none() or ""
        data = {**card.__dict__, "competitor_name": comp_name}
        items.append(BattlecardResponse.model_validate(data))

    return items


@router.post("/generate", response_model=BattlecardResponse, status_code=201)
async def generate_battlecard(
    data: BattlecardGenerateRequest, db: AsyncSession = Depends(get_db)
):
    """Generate a new battlecard for a competitor using AI."""
    # Get competitor
    comp_result = await db.execute(select(Competitor).where(Competitor.id == data.competitor_id))
    competitor = comp_result.scalar_one_or_none()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    # Get recent signals
    signals_result = await db.execute(
        select(Signal)
        .where(Signal.competitor_id == data.competitor_id)
        .order_by(Signal.detected_at.desc())
        .limit(50)
    )
    signals = signals_result.scalars().all()

    # Generate content
    content = _generate_battlecard_ai(competitor, signals)

    battlecard = Battlecard(
        competitor_id=competitor.id,
        generated_by="ai",
        **content,
    )
    db.add(battlecard)
    await db.commit()
    await db.refresh(battlecard)

    data = {**battlecard.__dict__, "competitor_name": competitor.name}
    return BattlecardResponse.model_validate(data)


@router.get("/{card_id}", response_model=BattlecardResponse)
async def get_battlecard(card_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific battlecard."""
    result = await db.execute(select(Battlecard).where(Battlecard.id == card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Battlecard not found")

    comp_result = await db.execute(select(Competitor.name).where(Competitor.id == card.competitor_id))
    comp_name = comp_result.scalar_one_or_none() or ""
    data = {**card.__dict__, "competitor_name": comp_name}
    return BattlecardResponse.model_validate(data)


@router.post("/{card_id}/publish", response_model=BattlecardResponse)
async def publish_battlecard(card_id: int, db: AsyncSession = Depends(get_db)):
    """Publish a battlecard (makes it visible to sales team)."""
    result = await db.execute(select(Battlecard).where(Battlecard.id == card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Battlecard not found")

    card.is_published = True
    card.version += 1
    await db.commit()
    await db.refresh(card)

    comp_result = await db.execute(select(Competitor.name).where(Competitor.id == card.competitor_id))
    comp_name = comp_result.scalar_one_or_none() or ""
    data = {**card.__dict__, "competitor_name": comp_name}
    return BattlecardResponse.model_validate(data)

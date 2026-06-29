"""Signal detection engine — scans for competitive intelligence signals."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Competitor, Signal, SignalSeverity, SignalType


class SignalDetector:
    """Detects competitive signals from various sources.

    In production, this would integrate with:
    - Website diffing (visualping.io API or self-hosted)
    - Job board APIs (LinkedIn, Indeed, Greenhouse)
    - Review scraping (G2, Capterra, TrustRadius)
    - RSS feeds (company blogs, press releases)
    - Twitter/X API for social mentions
    - BuiltWith for tech stack changes
    - Crunchbase for funding data

    For the open-source version, we provide a pluggable architecture
    where users can connect their own data sources.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def scan_competitor(self, competitor: Competitor) -> list[Signal]:
        """Run all enabled scans for a competitor."""
        signals: list[Signal] = []

        if competitor.monitor_website:
            signals.extend(await self._check_website(competitor))

        if competitor.monitor_pricing:
            signals.extend(await self._check_pricing(competitor))

        if competitor.monitor_jobs:
            signals.extend(await self._check_jobs(competitor))

        if competitor.monitor_reviews:
            signals.extend(await self._check_reviews(competitor))

        if competitor.monitor_social:
            signals.extend(await self._check_social(competitor))

        # Save all detected signals
        for signal in signals:
            self.db.add(signal)

        if signals:
            await self.db.commit()

        return signals

    async def scan_all(self) -> dict[int, list[Signal]]:
        """Scan all active competitors."""
        result = await self.db.execute(
            select(Competitor).where(Competitor.is_active == True)  # noqa: E712
        )
        competitors = result.scalars().all()

        all_signals: dict[int, list[Signal]] = {}
        for competitor in competitors:
            signals = await self.scan_competitor(competitor)
            all_signals[competitor.id] = signals

        return all_signals

    async def _check_website(self, competitor: Competitor) -> list[Signal]:
        """Check for website changes (placeholder for diffing integration)."""
        # In production: fetch page, compare hash, diff content
        return []

    async def _check_pricing(self, competitor: Competitor) -> list[Signal]:
        """Check for pricing page changes."""
        # In production: scrape pricing page, compare with stored version
        return []

    async def _check_jobs(self, competitor: Competitor) -> list[Signal]:
        """Check for new job postings."""
        # In production: query job board APIs
        return []

    async def _check_reviews(self, competitor: Competitor) -> list[Signal]:
        """Check for new reviews on G2/Capterra/TrustRadius."""
        # In production: scrape review sites
        return []

    async def _check_social(self, competitor: Competitor) -> list[Signal]:
        """Check for social media mentions."""
        # In production: query Twitter/X API, Reddit API
        return []

    def create_signal(
        self,
        competitor_id: int,
        signal_type: SignalType,
        title: str,
        description: str = "",
        severity: SignalSeverity = SignalSeverity.MEDIUM,
        source_url: str = "",
        confidence: float = 0.8,
        raw_data: dict[str, Any] | None = None,
    ) -> Signal:
        """Helper to create a signal object."""
        return Signal(
            competitor_id=competitor_id,
            signal_type=signal_type,
            title=title,
            description=description,
            severity=severity,
            source_url=source_url,
            confidence_score=confidence,
            raw_data=raw_data or {},
            detected_at=datetime.utcnow(),
        )

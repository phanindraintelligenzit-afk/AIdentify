"""Background worker for periodic signal scanning."""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from core.config import settings
from core.database import async_session
from models import Competitor
from services.signal_detector import SignalDetector

logger = logging.getLogger(__name__)


async def run_scan_cycle():
    """Run a single scan cycle for all active competitors."""
    async with async_session() as db:
        detector = SignalDetector(db)
        logger.info(f"Starting scan cycle at {datetime.utcnow().isoformat()}")
        results = await detector.scan_all()

        total_signals = sum(len(s) for s in results.values())
        logger.info(f"Scan complete: {len(results)} competitors scanned, {total_signals} signals detected")


async def run_worker():
    """Run the background scanning worker indefinitely."""
    logger.info(f"CI Agent worker started — scanning every {settings.SCAN_INTERVAL_MINUTES} minutes")

    while True:
        try:
            await run_scan_cycle()
        except Exception as e:
            logger.error(f"Scan cycle error: {e}")

        await asyncio.sleep(settings.SCAN_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())

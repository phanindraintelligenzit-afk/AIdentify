"""
Webhook delivery service.
"""
import asyncio
import hashlib
import hmac
import json
from datetime import datetime
from typing import List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models import Webhook


async def get_active_webhooks(db: AsyncSession) -> List[Webhook]:
    """Fetch all active webhooks from the database."""
    result = await db.execute(
        select(Webhook).where(Webhook.is_active == True)
    )
    return result.scalars().all()


async def deliver_webhook(webhook: Webhook, event: str, payload: dict):
    """Deliver a webhook to the specified URL."""
    if event not in webhook.events.split(","):
        return

    body = json.dumps({
        "event": event,
        "data": payload,
        "timestamp": datetime.utcnow().isoformat(),
    })

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": event,
    }

    if webhook.secret:
        signature = hmac.new(
            webhook.secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(webhook.url, content=body, headers=headers)
    except Exception:
        pass  # Webhooks are best-effort


async def trigger_webhooks(event: str, payload: dict):
    """Trigger all relevant webhooks for an event."""
    async with async_session_factory() as db:
        webhooks = await get_active_webhooks(db)
        tasks = [deliver_webhook(wh, event, payload) for wh in webhooks]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

"""
Authentication middleware and API key management.
"""
import os
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Default API keys (in production, store in database or secrets manager)
DEFAULT_API_KEYS = {
    "kanban-dev-key-2024": {"role": "admin", "agent": "owl"},
    "kanban-agent-researcher": {"role": "agent", "agent": "researcher"},
    "kanban-agent-writer": {"role": "agent", "agent": "writer"},
    "kanban-agent-outreach": {"role": "agent", "agent": "outreach"},
    "kanban-agent-social": {"role": "agent", "agent": "social"},
}

# Load additional keys from environment
env_keys = os.getenv("KANBAN_API_KEYS", "")
if env_keys:
    for pair in env_keys.split(","):
        if ":" in pair:
            key, role = pair.split(":", 1)
            DEFAULT_API_KEYS[key.strip()] = {"role": role.strip(), "agent": "owl"}


async def verify_api_key(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Verify the API key from X-API-Key header.
    Returns dict with role and agent info.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
        )

    key_info = DEFAULT_API_KEYS.get(api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return key_info


async def verify_admin_key(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Verify API key has admin role.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key.",
        )

    key_info = DEFAULT_API_KEYS.get(api_key)
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    if key_info["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    return key_info


def get_current_agent(api_key: Optional[str] = Security(API_KEY_HEADER)) -> Optional[str]:
    """Extract agent name from API key."""
    if api_key:
        key_info = DEFAULT_API_KEYS.get(api_key)
        if key_info:
            return key_info.get("agent")
    return None

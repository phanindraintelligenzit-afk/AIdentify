"""Response package management endpoints."""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timezone

from app.schemas.dsar import ResponsePackageCreate, ResponsePackageResponse

router = APIRouter()

RESPONSE_STORE = {}


@router.post("/{reference_number}")
async def create_response_package(reference_number: str, package: ResponsePackageCreate):
    """Create a response package for a DSAR."""
    pkg = {
        "id": len(RESPONSE_STORE) + 1,
        "dsar_id": reference_number,
        "included_data": package.included_data,
        "excluded_data": ["third_party_pii", "trade_secrets"],
        "redactions_count": 3,
        "format": package.format,
        "approved_by": None,
        "approved_at": None,
        "sent_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "notes": package.notes,
    }
    RESPONSE_STORE[reference_number] = pkg
    return pkg


@router.post("/{reference_number}/approve")
async def approve_package(reference_number: str, approver_id: int = 1):
    """Approve a response package for sending."""
    if reference_number not in RESPONSE_STORE:
        raise HTTPException(status_code=404, detail="Response package not found")
    RESPONSE_STORE[reference_number]["approved_by"] = approver_id
    RESPONSE_STORE[reference_number]["approved_at"] = datetime.now(timezone.utc).isoformat()
    return {"message": "Package approved", "reference": reference_number}


@router.post("/{reference_number}/send")
async def send_response(reference_number: str):
    """Mark response as sent to requester."""
    if reference_number not in RESPONSE_STORE:
        raise HTTPException(status_code=404, detail="Response package not found")
    RESPONSE_STORE[reference_number]["sent_at"] = datetime.now(timezone.utc).isoformat()
    return {"message": "Response sent to requester", "reference": reference_number}


@router.get("/{reference_number}")
async def get_response_package(reference_number: str):
    """Get response package details."""
    if reference_number not in RESPONSE_STORE:
        raise HTTPException(status_code=404, detail="Response package not found")
    return RESPONSE_STORE[reference_number]

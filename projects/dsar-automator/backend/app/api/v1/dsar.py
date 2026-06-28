"""DSAR request management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from app.schemas.dsar import DSARCreate, DSARResponse, DSARDetail, DSARStatusEnum
from app.api.deps import get_current_user

router = APIRouter()

DSAR_STORE = {}
COUNTER = 0


def _generate_reference() -> str:
    global COUNTER
    COUNTER += 1
    return f"DSAR-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{COUNTER:04d}"


@router.post("/", response_model=DSARResponse, status_code=201)
async def create_dsar(request: DSARCreate):
    """Create a new DSAR request."""
    ref = _generate_reference()
    now = datetime.now(timezone.utc)
    deadline_days = 30 if request.regulation == "gdpr" else 45
    dsar = {
        "id": COUNTER,
        "reference_number": ref,
        "requester_name": request.requester_name,
        "requester_email": request.requester_email,
        "requester_phone": request.requester_phone,
        "request_type": request.request_type.value,
        "status": "received",
        "received_at": now.isoformat(),
        "deadline_at": (now + timedelta(days=deadline_days)).isoformat(),
        "days_remaining": deadline_days,
        "records_found_count": 0,
        "risk_level": "low",
        "data_categories_found": [],
        "description": request.description,
    }
    DSAR_STORE[ref] = dsar
    return dsar


@router.get("/", response_model=List[DSARResponse])
async def list_dsars(
    status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List DSAR requests with optional filters."""
    results = list(DSAR_STORE.values())
    if status:
        results = [r for r in results if r["status"] == status]
    if risk_level:
        results = [r for r in results if r["risk_level"] == risk_level]
    return results[skip:skip + limit]


@router.get("/{reference_number}", response_model=DSARDetail)
async def get_dsar(reference_number: str):
    """Get detailed DSAR request information."""
    if reference_number not in DSAR_STORE:
        raise HTTPException(status_code=404, detail="DSAR not found")
    dsar = DSAR_STORE[reference_number]
    dsar["discovery_results"] = []
    dsar["audit_trail"] = []
    return dsar


@router.patch("/{reference_number}/status")
async def update_status(reference_number: str, status: DSARStatusEnum):
    """Update DSAR processing status."""
    if reference_number not in DSAR_STORE:
        raise HTTPException(status_code=404, detail="DSAR not found")
    DSAR_STORE[reference_number]["status"] = status.value
    return DSAR_STORE[reference_number]


@router.post("/{reference_number}/verify")
async def verify_identity(reference_number: str):
    """Mark identity verification as complete."""
    if reference_number not in DSAR_STORE:
        raise HTTPException(status_code=404, detail="DSAR not found")
    DSAR_STORE[reference_number]["status"] = "discovering"
    return {"message": "Identity verified", "next_step": "data_discovery"}

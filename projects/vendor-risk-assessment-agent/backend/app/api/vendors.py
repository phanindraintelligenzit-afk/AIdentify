"""Vendor CRUD API routes."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import json

from app.schemas import (
    VendorCreate, VendorUpdate, VendorResponse, VendorSummary,
    RiskFindingCreate, RiskFindingResponse
)
from app.services.risk_scorer import calculate_vendor_risk_score

router = APIRouter(prefix="/vendors", tags=["vendors"])

# In-memory store for demo (replace with DB in production)
VENDORS = {}
FINDINGS = {}


@router.get("", response_model=list[VendorSummary])
async def list_vendors(
    risk_level: Optional[str] = None,
    category: Optional[str] = None,
    is_critical: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List all vendors with optional filtering."""
    vendors = list(VENDORS.values())
    
    if risk_level:
        vendors = [v for v in vendors if v.get("risk_level") == risk_level]
    if category:
        vendors = [v for v in vendors if v.get("category") == category]
    if is_critical is not None:
        vendors = [v for v in vendors if v.get("is_critical") == is_critical]
    
    # Build summaries
    result = []
    for v in vendors:
        result.append(VendorSummary(
            id=v["id"],
            name=v["name"],
            category=v.get("category"),
            risk_level=v["risk_level"],
            risk_score=v["risk_score"],
            is_critical=v.get("is_critical", False),
        ))
    
    return result[skip : skip + limit]


@router.post("", response_model=VendorResponse, status_code=201)
async def create_vendor(vendor: VendorCreate):
    """Add a new vendor to the risk management system."""
    import uuid
    from datetime import datetime
    
    vendor_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    vendor_data = {
        "id": vendor_id,
        "name": vendor.name,
        "domain": vendor.domain,
        "category": vendor.category,
        "contact_email": vendor.contact_email,
        "contact_name": vendor.contact_name,
        "risk_level": "medium",
        "risk_score": 50.0,
        "is_critical": vendor.is_critical,
        "notes": vendor.notes,
        "created_at": now,
        "updated_at": now,
    }
    
    VENDORS[vendor_id] = vendor_data
    return VendorResponse(**vendor_data)


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(vendor_id: str):
    """Get vendor details by ID."""
    if vendor_id not in VENDORS:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return VendorResponse(**VENDORS[vendor_id])


@router.patch("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(vendor_id: str, update: VendorUpdate):
    """Update vendor information."""
    if vendor_id not in VENDORS:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    vendor = VENDORS[vendor_id]
    update_data = update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        vendor[field] = value
    
    from datetime import datetime
    vendor["updated_at"] = datetime.utcnow()
    
    return VendorResponse(**vendor)


@router.delete("/{vendor_id}", status_code=204)
async def delete_vendor(vendor_id: str):
    """Remove a vendor."""
    if vendor_id not in VENDORS:
        raise HTTPException(status_code=404, detail="Vendor not found")
    del VENDORS[vendor_id]
    # Also remove associated findings
    FINDINGS.pop(vendor_id, None)


@router.post("/{vendor_id}/findings", response_model=RiskFindingResponse, status_code=201)
async def create_finding(vendor_id: str, finding: RiskFindingCreate):
    """Add a risk finding for a vendor."""
    if vendor_id not in VENDORS:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    import uuid
    from datetime import datetime
    
    finding_id = str(uuid.uuid4())
    finding_data = {
        "id": finding_id,
        "vendor_id": vendor_id,
        "category": finding.category,
        "severity": finding.severity.value if hasattr(finding.severity, 'value') else finding.severity,
        "title": finding.title,
        "description": finding.description,
        "recommendation": finding.recommendation,
        "is_resolved": False,
        "created_at": datetime.utcnow(),
    }
    # vendor_id from path takes precedence
    
    if vendor_id not in FINDINGS:
        FINDINGS[vendor_id] = []
    FINDINGS[vendor_id].append(finding_data)
    
    # Recalculate vendor risk score
    _recalculate_vendor_risk(vendor_id)
    
    return RiskFindingResponse(**finding_data)


@router.get("/{vendor_id}/findings", response_model=list[RiskFindingResponse])
async def list_findings(vendor_id: str, unresolved_only: bool = False):
    """List risk findings for a vendor."""
    if vendor_id not in VENDORS:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    findings = FINDINGS.get(vendor_id, [])
    if unresolved_only:
        findings = [f for f in findings if not f.get("is_resolved")]
    
    return [RiskFindingResponse(**f) for f in findings]


def _recalculate_vendor_risk(vendor_id: str):
    """Recalculate vendor risk score based on findings."""
    vendor = VENDORS[vendor_id]
    findings = FINDINGS.get(vendor_id, [])
    open_findings = [f for f in findings if not f.get("is_resolved")]
    
    score, level = calculate_vendor_risk_score(
        assessment_score=vendor.get("risk_score"),
        open_findings=open_findings,
        is_critical=vendor.get("is_critical", False),
    )
    vendor["risk_score"] = score
    vendor["risk_level"] = level

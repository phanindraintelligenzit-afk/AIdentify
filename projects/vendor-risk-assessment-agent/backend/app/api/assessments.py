"""Assessment API routes."""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import uuid

from app.schemas import (
    AssessmentCreate, AssessmentResponse, AssessmentSubmit
)
from app.services.assessment_service import (
    get_template, get_all_templates, process_assessment_responses
)

router = APIRouter(prefix="/assessments", tags=["assessments"])

# In-memory store
ASSESSMENTS = {}


@router.get("/templates")
async def list_templates():
    """List available assessment templates."""
    return get_all_templates()


@router.get("/templates/{template_name}")
async def get_template_detail(template_name: str):
    """Get full template with questions."""
    template = get_template(template_name)
    return template


@router.post("", response_model=AssessmentResponse, status_code=201)
async def create_assessment(assessment: AssessmentCreate):
    """Create a new assessment for a vendor."""
    from app.api.vendors import VENDORS
    
    if assessment.vendor_id not in VENDORS:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    assessment_id = str(uuid.uuid4())
    now = datetime.utcnow()
    due_date = now + timedelta(days=assessment.due_days)
    
    assessment_data = {
        "id": assessment_id,
        "vendor_id": assessment.vendor_id,
        "template": assessment.template,
        "status": "pending",
        "score": None,
        "risk_level": None,
        "responses": None,
        "sent_at": None,
        "completed_at": None,
        "due_date": due_date,
        "created_at": now,
    }
    
    ASSESSMENTS[assessment_id] = assessment_data
    return AssessmentResponse(**assessment_data)


@router.post("/{assessment_id}/send", response_model=AssessmentResponse)
async def send_assessment(assessment_id: str):
    """Mark assessment as sent to vendor."""
    if assessment_id not in ASSESSMENTS:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    assessment = ASSESSMENTS[assessment_id]
    assessment["status"] = "sent"
    assessment["sent_at"] = datetime.utcnow()
    
    return AssessmentResponse(**assessment)


@router.post("/{assessment_id}/submit", response_model=AssessmentResponse)
async def submit_assessment(assessment_id: str, submission: AssessmentSubmit):
    """Submit completed assessment responses."""
    if assessment_id not in ASSESSMENTS:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    assessment = ASSESSMENTS[assessment_id]
    
    # Process responses
    result = process_assessment_responses(submission.responses)
    
    assessment["status"] = "completed"
    assessment["score"] = result["score"]
    assessment["risk_level"] = result["risk_level"]
    assessment["responses"] = submission.responses
    assessment["completed_at"] = datetime.utcnow()
    
    # Update vendor risk score
    from app.api.vendors import VENDORS, _recalculate_vendor_risk
    vendor_id = assessment["vendor_id"]
    if vendor_id in VENDORS:
        VENDORS[vendor_id]["risk_score"] = result["score"]
        VENDORS[vendor_id]["risk_level"] = result["risk_level"]
        _recalculate_vendor_risk(vendor_id)
    
    return AssessmentResponse(**assessment)


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(assessment_id: str):
    """Get assessment details."""
    if assessment_id not in ASSESSMENTS:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return AssessmentResponse(**ASSESSMENTS[assessment_id])


@router.get("")
async def list_assessments(status: str = None, vendor_id: str = None):
    """List assessments with optional filters."""
    assessments = list(ASSESSMENTS.values())
    
    if status:
        assessments = [a for a in assessments if a["status"] == status]
    if vendor_id:
        assessments = [a for a in assessments if a["vendor_id"] == vendor_id]
    
    return [AssessmentResponse(**a) for a in assessments]

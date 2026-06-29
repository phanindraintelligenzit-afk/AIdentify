"""Dashboard API routes."""
from fastapi import APIRouter
from app.schemas import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get aggregated dashboard statistics."""
    from app.api.vendors import VENDORS, FINDINGS
    from app.api.assessments import ASSESSMENTS
    
    vendors = list(VENDORS.values())
    assessments = list(ASSESSMENTS.values())
    
    total = len(vendors)
    critical = sum(1 for v in vendors if v.get("is_critical"))
    high_risk = sum(1 for v in vendors if v.get("risk_level") in ("high", "critical"))
    
    pending = sum(1 for a in assessments if a["status"] in ("pending", "sent", "in_progress"))
    completed = sum(1 for a in assessments if a["status"] == "completed")
    
    all_findings = []
    for findings_list in FINDINGS.values():
        all_findings.extend(findings_list)
    open_findings = sum(1 for f in all_findings if not f.get("is_resolved"))
    
    avg_score = sum(v.get("risk_score", 50) for v in vendors) / max(total, 1)
    
    # Risk distribution
    distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for v in vendors:
        level = v.get("risk_level", "medium")
        distribution[level] = distribution.get(level, 0) + 1
    
    return DashboardStats(
        total_vendors=total,
        critical_vendors=critical,
        high_risk_vendors=high_risk,
        pending_assessments=pending,
        completed_assessments=completed,
        open_findings=open_findings,
        avg_risk_score=round(avg_score, 1),
        risk_distribution=distribution,
    )


@router.get("/health")
async def health_check():
    """API health check."""
    return {"status": "healthy", "service": "vendor-risk-assessment-agent"}

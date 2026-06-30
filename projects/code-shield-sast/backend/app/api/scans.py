"""API routes for scans."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.scan import (
    ScanCreate, ScanResponse, ScanDetail, FindingResponse,
    DashboardStats, HealthResponse,
)
from app.services.scan_service import ScanService
from app.services.sast_engine import SASTScanner
from app.core.config import get_settings
import time

router = APIRouter()
scan_service = ScanService()
scanner = SASTScanner()

_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=get_settings().APP_VERSION,
        uptime_seconds=round(time.time() - _start_time, 1),
    )


@router.get("/rules")
async def list_rules():
    """List all available detection rules."""
    return {"rules": scanner.get_rules_summary(), "total": scanner.rule_count}


@router.post("/scan", response_model=ScanResponse)
async def create_scan(
    data: ScanCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create and run a new security scan."""
    scan = await scan_service.create_scan(db, data)
    await db.flush()
    # Run scan synchronously for API simplicity
    scan = await scan_service.run_scan(db, scan.id)
    await db.refresh(scan)
    return scan


@router.post("/scan/code", response_model=ScanResponse)
async def scan_code(
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Scan a code snippet directly."""
    code = data.get("code", "")
    filename = data.get("filename", "input.py")
    
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")
    
    # Create a scan record
    from app.models.scan import Scan, ScanStatus
    scan = Scan(
        repository=f"inline://{filename}",
        branch="main",
        status=ScanStatus.PENDING,
    )
    db.add(scan)
    await db.flush()
    
    # Run scan with code
    scan = await scan_service.run_scan(db, scan.id, code=code)
    await db.refresh(scan)
    return scan


@router.get("/scans", response_model=List[ScanResponse])
async def list_scans(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all scans."""
    scans = await scan_service.list_scans(db, limit=limit)
    return scans


@router.get("/scans/{scan_id}", response_model=ScanDetail)
async def get_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get scan details with findings."""
    scan = await scan_service.get_scan(db, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    findings = await scan_service.get_findings(db, scan_id)
    
    # Build response manually
    return {
        "id": scan.id,
        "repository": scan.repository,
        "branch": scan.branch,
        "status": scan.status,
        "total_files": scan.total_files,
        "scanned_files": scan.scanned_files,
        "total_findings": scan.total_findings,
        "critical_count": scan.critical_count,
        "high_count": scan.high_count,
        "medium_count": scan.medium_count,
        "low_count": scan.low_count,
        "info_count": scan.info_count,
        "risk_score": scan.risk_score,
        "scan_duration_seconds": scan.scan_duration_seconds,
        "created_at": scan.created_at,
        "completed_at": scan.completed_at,
        "findings": [
            {
                "id": f.id,
                "scan_id": f.scan_id,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "rule_id": f.rule_id,
                "severity": f.severity,
                "title": f.title,
                "description": f.description,
                "remediation": f.remediation,
                "cwe_id": f.cwe_id,
                "owasp_category": f.owasp_category,
                "code_snippet": f.code_snippet,
                "confidence": f.confidence,
                "created_at": f.created_at,
            }
            for f in findings
        ],
    }


@router.get("/scans/{scan_id}/findings", response_model=List[FindingResponse])
async def get_findings(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get findings for a specific scan."""
    findings = await scan_service.get_findings(db, scan_id)
    return findings


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics."""
    return await scan_service.get_dashboard_stats(db)

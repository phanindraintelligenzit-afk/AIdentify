"""Pydantic schemas for API."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.scan import ScanStatus, Severity


# --- Finding schemas ---

class FindingBase(BaseModel):
    file_path: str
    line_number: Optional[int] = None
    rule_id: str
    severity: Severity
    title: str
    description: Optional[str] = None
    remediation: Optional[str] = None
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    code_snippet: Optional[str] = None
    confidence: float = 0.8


class FindingResponse(FindingBase):
    id: int
    scan_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Scan schemas ---

class ScanCreate(BaseModel):
    repository: str = Field(..., description="Git URL or local path to scan")
    branch: str = "main"


class ScanResponse(BaseModel):
    id: int
    repository: str
    branch: str
    status: ScanStatus
    total_files: int = 0
    scanned_files: int = 0
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    risk_score: float = 0.0
    scan_duration_seconds: float = 0.0
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScanDetail(ScanResponse):
    findings: List[FindingResponse] = []


# --- Dashboard schemas ---

class DashboardStats(BaseModel):
    total_scans: int
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    avg_risk_score: float
    scans_this_week: int
    top_rules: List[dict]
    severity_distribution: dict


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float

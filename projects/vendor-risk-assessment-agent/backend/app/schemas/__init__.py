"""Pydantic schemas for API request/response."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssessmentStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    EXPIRED = "expired"


# --- Vendor Schemas ---

class VendorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: Optional[str] = None
    category: Optional[str] = None
    contact_email: Optional[str] = None
    contact_name: Optional[str] = None
    is_critical: bool = False
    notes: Optional[str] = None


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    category: Optional[str] = None
    contact_email: Optional[str] = None
    contact_name: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    is_critical: Optional[bool] = None
    notes: Optional[str] = None


class VendorResponse(BaseModel):
    id: str
    name: str
    domain: Optional[str]
    category: Optional[str]
    contact_email: Optional[str]
    contact_name: Optional[str]
    risk_level: str
    risk_score: float
    is_critical: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VendorSummary(BaseModel):
    id: str
    name: str
    category: Optional[str]
    risk_level: str
    risk_score: float
    is_critical: bool
    assessment_count: int = 0
    open_findings: int = 0


# --- Assessment Schemas ---

class AssessmentCreate(BaseModel):
    vendor_id: str
    template: str = "standard"
    due_days: int = 14


class AssessmentResponse(BaseModel):
    id: str
    vendor_id: str
    template: str
    status: str
    score: Optional[float]
    risk_level: Optional[str]
    sent_at: Optional[datetime]
    completed_at: Optional[datetime]
    due_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AssessmentSubmit(BaseModel):
    responses: dict


# --- Risk Finding Schemas ---

class RiskFindingCreate(BaseModel):
    vendor_id: Optional[str] = None
    category: str
    severity: RiskLevel
    title: str
    description: Optional[str] = None
    recommendation: Optional[str] = None


class RiskFindingResponse(BaseModel):
    id: str
    vendor_id: str
    category: str
    severity: str
    title: str
    description: Optional[str]
    recommendation: Optional[str]
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Dashboard Schemas ---

class DashboardStats(BaseModel):
    total_vendors: int
    critical_vendors: int
    high_risk_vendors: int
    pending_assessments: int
    completed_assessments: int
    open_findings: int
    avg_risk_score: float
    risk_distribution: dict


class RiskTrend(BaseModel):
    date: str
    avg_score: float
    new_findings: int

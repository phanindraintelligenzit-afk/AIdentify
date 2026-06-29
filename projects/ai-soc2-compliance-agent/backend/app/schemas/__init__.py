"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from models import AuditStatus, ControlStatus, EvidenceType


# ── Health schema (imported from schemas.health) ──


# ── Control schemas ──

class ComplianceControlBase(BaseModel):
    control_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=512)
    description: str = ""
    category: str = Field(..., min_length=1, max_length=100)
    subcategory: str = ""
    tsc_criterion: str = ""
    status: ControlStatus = ControlStatus.NOT_STARTED
    assignee: str = ""
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: str = ""


class ComplianceControlCreate(ComplianceControlBase):
    pass


class ComplianceControlUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tsc_criterion: Optional[str] = None
    status: Optional[ControlStatus] = None
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ComplianceControlResponse(BaseModel):
    id: int
    control_id: str
    name: str
    description: str
    category: str
    subcategory: str
    tsc_criterion: str
    status: ControlStatus
    assignee: str
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComplianceControlListResponse(BaseModel):
    total: int
    items: list[ComplianceControlResponse]


# ── Evidence schemas ──

class EvidenceBase(BaseModel):
    evidence_type: EvidenceType
    title: str = Field(..., min_length=1, max_length=512)
    description: str = ""
    source: str = ""
    source_url: str = ""
    file_path: str = ""
    file_hash: str = ""
    collected_by: str = "auto"
    is_valid: bool = True
    valid_until: Optional[datetime] = None
    raw_metadata: dict = {}


class EvidenceCreate(EvidenceBase):
    control_id: int


class EvidenceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    collected_by: Optional[str] = None
    is_valid: Optional[bool] = None
    valid_until: Optional[datetime] = None
    raw_metadata: Optional[dict] = None


class EvidenceResponse(BaseModel):
    id: int
    control_id: int
    control_name: str = ""
    evidence_type: EvidenceType
    title: str
    description: str
    source: str
    source_url: str
    file_path: str
    file_hash: str
    collected_by: str
    is_valid: bool
    valid_from: datetime
    valid_until: Optional[datetime] = None
    raw_metadata: dict
    created_at: datetime

    class Config:
        from_attributes = True


class EvidenceListResponse(BaseModel):
    total: int
    items: list[EvidenceResponse]


class EvidenceSummary(BaseModel):
    control_id: int
    control_name: str
    total_evidence: int
    valid_evidence: int
    invalid_evidence: int


# ── Audit schemas ──

class AuditBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=512)
    audit_type: str = "SOC2 Type II"
    status: AuditStatus = AuditStatus.NOT_STARTED
    auditor_name: str = ""
    auditor_contact: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    observation_period_start: Optional[datetime] = None
    observation_period_end: Optional[datetime] = None
    notes: str = ""
    completion_percentage: float = 0.0


class AuditCreate(AuditBase):
    pass


class AuditUpdate(BaseModel):
    name: Optional[str] = None
    audit_type: Optional[str] = None
    status: Optional[AuditStatus] = None
    auditor_name: Optional[str] = None
    auditor_contact: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    observation_period_start: Optional[datetime] = None
    observation_period_end: Optional[datetime] = None
    notes: Optional[str] = None
    completion_percentage: Optional[float] = None


class AuditResponse(BaseModel):
    id: int
    name: str
    audit_type: str
    status: AuditStatus
    auditor_name: str
    auditor_contact: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    observation_period_start: Optional[datetime] = None
    observation_period_end: Optional[datetime] = None
    notes: str
    completion_percentage: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AuditListResponse(BaseModel):
    total: int
    items: list[AuditResponse]


# ── Policy schemas ──

class PolicyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=512)
    policy_type: str = Field(..., min_length=1, max_length=100)
    version: str = "1.0"
    content: str = ""
    status: str = "draft"
    owner: str = ""
    review_date: Optional[datetime] = None
    approved_by: str = ""
    approved_at: Optional[datetime] = None


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    policy_type: Optional[str] = None
    version: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None
    review_date: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


class PolicyResponse(BaseModel):
    id: int
    name: str
    policy_type: str
    version: str
    content: str
    status: str
    owner: str
    review_date: Optional[datetime] = None
    approved_by: str
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PolicyListResponse(BaseModel):
    total: int
    items: list[PolicyResponse]


# ── Integration schemas ──

class IntegrationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    provider: str = Field(..., min_length=1, max_length=100)
    integration_type: str = "api"
    config: dict = {}
    status: str = "connected"
    last_sync_at: Optional[datetime] = None
    credentials_encrypted: str = ""


class IntegrationCreate(IntegrationBase):
    pass


class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    integration_type: Optional[str] = None
    config: Optional[dict] = None
    status: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    credentials_encrypted: Optional[str] = None
    is_active: Optional[bool] = None


class IntegrationResponse(BaseModel):
    id: int
    name: str
    provider: str
    integration_type: str
    config: dict
    status: str
    last_sync_at: Optional[datetime] = None
    credentials_encrypted: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IntegrationListResponse(BaseModel):
    total: int
    items: list[IntegrationResponse]


# ── Dashboard schemas ──

class DashboardStats(BaseModel):
    total_controls: int
    controls_complete: int
    controls_failing: int
    total_evidence: int
    total_policies: int
    policies_approved: int
    total_integrations: int
    active_integrations: int
    audits_in_progress: int
    compliance_percentage: float

"""Pydantic schemas for DSAR API."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class RequestTypeEnum(str, Enum):
    ACCESS = "access"
    ERASURE = "erasure"
    RECTIFICATION = "rectification"
    PORTABILITY = "portability"
    OBJECTION = "objection"


class RegulationEnum(str, Enum):
    GDPR = "gdpr"
    CCPA = "ccpa"
    LGPD = "lgpd"
    OTHER = "other"


class DSARStatusEnum(str, Enum):
    RECEIVED = "received"
    VERIFYING = "verifying"
    DISCOVERING = "discovering"
    REVIEWING = "reviewing"
    APPROVING = "approving"
    READY_TO_SEND = "ready_to_send"
    SENT = "sent"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXTENDED = "extended"


class DSARCreate(BaseModel):
    requester_name: str = Field(..., min_length=1, max_length=255)
    requester_email: EmailStr
    requester_phone: Optional[str] = None
    request_type: RequestTypeEnum = RequestTypeEnum.ACCESS
    regulation: RegulationEnum = RegulationEnum.GDPR
    description: Optional[str] = None


class DSARResponse(BaseModel):
    id: int
    reference_number: str
    requester_name: str
    requester_email: str
    requester_phone: Optional[str] = None
    request_type: str
    status: str
    received_at: str
    deadline_at: str
    days_remaining: int
    records_found_count: int
    risk_level: str
    data_categories_found: List[str] = []
    description: Optional[str] = None

    class Config:
        from_attributes = True


class DiscoveryItem(BaseModel):
    source_system: str
    source_name: str
    data_category: str
    records_count: int
    data_schema: Optional[dict] = None
    contains_pii: bool = False
    contains_third_party_data: bool = False
    discovered_at: Optional[str] = None


class DSARDetail(DSARResponse):
    discovery_results: List[DiscoveryItem] = []
    audit_trail: List[dict] = []


class ResponsePackageCreate(BaseModel):
    included_data: List[str] = []
    format: str = "json"
    notes: Optional[str] = None


class ResponsePackageResponse(BaseModel):
    id: int
    dsar_id: str
    included_data: List[str]
    excluded_data: List[str]
    redactions_count: int
    format: str
    approved_by: Optional[int] = None
    approved_at: Optional[str] = None
    sent_at: Optional[str] = None
    created_at: str
    notes: Optional[str] = None


class DashboardStats(BaseModel):
    total_requests: int
    pending_requests: int
    completed_this_month: int
    overdue_requests: int
    avg_processing_days: float
    compliance_rate: float
    systems_connected: int
    total_data_sources: int

"""
ContractLens Pydantic Schemas for API
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ContractType(str, Enum):
    NDA = "NDA"
    MSA = "MSA"
    SOW = "SOW"
    DPA = "DPA"
    EMPLOYMENT = "EMPLOYMENT"
    VENDOR = "VENDOR"
    OTHER = "OTHER"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnalysisStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ClauseType(str, Enum):
    TERMINATION = "TERMINATION"
    INDEMNIFICATION = "INDEMNIFICATION"
    LIABILITY = "LIABILITY"
    CONFIDENTIALITY = "CONFIDENTIALITY"
    IP_OWNERSHIP = "IP_OWNERSHIP"
    PAYMENT_TERMS = "PAYMENT_TERMS"
    DATA_PROTECTION = "DATA_PROTECTION"
    NON_COMPETE = "NON_COMPETE"
    WARRANTY = "WARRANTY"
    FORCE_MAJEURE = "FORCE_MAJEURE"
    DISPUTE_RESOLUTION = "DISPUTE_RESOLUTION"
    ASSIGNMENT = "ASSIGNMENT"
    GOVERNING_LAW = "GOVERNING_LAW"
    OTHER = "OTHER"


# Request schemas
class ContractUpload(BaseModel):
    filename: str
    content_text: str
    contract_type: ContractType = ContractType.OTHER


class ContractCreate(BaseModel):
    filename: str
    original_filename: str
    contract_type: ContractType = ContractType.OTHER
    content_text: str
    file_size: Optional[int] = None
    page_count: Optional[int] = None


class AnalysisRequest(BaseModel):
    contract_id: int
    force_reanalyze: bool = False


# Response schemas
class ContractBase(BaseModel):
    id: int
    filename: str
    original_filename: str
    contract_type: ContractType
    file_size: Optional[int]
    page_count: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContractResponse(ContractBase):
    content_preview: str  # First 500 chars


class ContractDetail(ContractBase):
    content_text: str


class ClauseResponse(BaseModel):
    id: int
    clause_type: ClauseType
    title: Optional[str]
    content: str
    start_char: int
    end_char: int
    page_number: Optional[int]
    confidence_score: float

    class Config:
        from_attributes = True


class RiskResponse(BaseModel):
    id: int
    risk_type: str
    title: str
    description: str
    risk_level: RiskLevel
    confidence_score: float
    location: Optional[str]
    suggestion: Optional[str]
    reference_clause: Optional[str]

    class Config:
        from_attributes = True


class AnalysisBase(BaseModel):
    id: int
    contract_id: int
    status: AnalysisStatus
    overall_risk_score: float
    risk_level: RiskLevel
    summary: Optional[str]
    key_findings: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    processing_time_ms: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AnalysisResponse(AnalysisBase):
    risks: List[RiskResponse] = []


class AnalysisSummary(BaseModel):
    total_contracts: int
    total_analyses: int
    avg_risk_score: float
    risk_distribution: Dict[str, int]
    recent_analyses: List[AnalysisBase]


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    timestamp: datetime
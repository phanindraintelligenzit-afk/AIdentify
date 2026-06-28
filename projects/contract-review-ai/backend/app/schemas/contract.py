from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr
from enum import Enum


class ContractType(str, Enum):
    NDA = "nda"
    MSA = "msa"
    OTHER = "other"


class ContractStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ClauseRiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    APPROVED = "approved"


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class PlaybookBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    contract_type: ContractType = ContractType.OTHER
    rules: Dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False


class PlaybookCreate(PlaybookBase):
    pass


class PlaybookUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    contract_type: Optional[ContractType] = None
    rules: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class PlaybookResponse(PlaybookBase):
    id: UUID
    is_active: bool
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ClauseRuleBase(BaseModel):
    clause_name: str = Field(..., min_length=1, max_length=255)
    clause_patterns: List[str] = Field(default_factory=list)
    required_elements: Optional[List[str]] = None
    forbidden_elements: Optional[List[str]] = None
    risk_level: ClauseRiskLevel = ClauseRiskLevel.MEDIUM
    redline_suggestion: Optional[str] = None
    explanation: Optional[str] = None
    is_active: bool = True
    order: int = 0


class ClauseRuleCreate(ClauseRuleBase):
    pass


class ClauseRuleUpdate(BaseModel):
    clause_name: Optional[str] = Field(None, min_length=1, max_length=255)
    clause_patterns: Optional[List[str]] = None
    required_elements: Optional[List[str]] = None
    forbidden_elements: Optional[List[str]] = None
    risk_level: Optional[ClauseRiskLevel] = None
    redline_suggestion: Optional[str] = None
    explanation: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None


class ClauseRuleResponse(ClauseRuleBase):
    id: UUID
    playbook_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PlaybookWithRules(PlaybookResponse):
    rules: List[ClauseRuleResponse] = []


class ContractBase(BaseModel):
    contract_type: ContractType = ContractType.OTHER
    playbook_id: Optional[UUID] = None


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    contract_type: Optional[ContractType] = None
    playbook_id: Optional[UUID] = None


class ContractResponse(ContractBase):
    id: UUID
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    status: ContractStatus
    owner_id: UUID
    playbook_id: Optional[UUID] = None
    risk_summary: Optional[Dict[str, Any]] = None
    redline_docx_path: Optional[str] = None
    redline_pdf_path: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ContractWithDetails(ContractResponse):
    clause_analysis: Optional[Dict[str, Any]] = None


class ClauseAnalysisResult(BaseModel):
    clause_name: str
    clause_text: str
    risk_level: ClauseRiskLevel
    issues: List[str] = Field(default_factory=list)
    matched_rules: List[str] = Field(default_factory=list)
    redline_suggestion: Optional[str] = None
    explanation: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)


class RiskSummary(BaseModel):
    total_clauses: int
    high_risk: int
    medium_risk: int
    low_risk: int
    approved: int
    overall_risk_score: float = Field(ge=0.0, le=100.0)
    risk_breakdown: Dict[str, int] = Field(default_factory=dict)


class ContractAnalysisResponse(BaseModel):
    contract_id: UUID
    clause_analysis: List[ClauseAnalysisResult]
    risk_summary: RiskSummary
    redline_docx_url: Optional[str] = None
    redline_pdf_url: Optional[str] = None


class ProcessingJobStatus(BaseModel):
    job_id: UUID
    contract_id: UUID
    status: str
    progress: int
    current_step: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class UploadResponse(BaseModel):
    contract_id: UUID
    job_id: UUID
    message: str
    status: ContractStatus


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    redis: str
"""
Pydantic models for audit events conforming to the compliance audit schema.

Schema: docs/compliance_audit_schema.md (v1.0.0)
Target Compliance: EU AI Act, GDPR, SOC 2 Type II
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ActionType(str, Enum):
    """Categorized action types for audit events."""
    GENERATE_TEXT = "generate_text"
    CLASSIFY = "classify"
    RECOMMEND = "recommend"
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"
    DATA_ACCESS = "data_access"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"
    TOOL_CALL = "tool_call"
    DECISION = "decision"
    INFERENCE = "inference"
    ROUTING = "routing"
    SUMMARIZE = "summarize"
    TRANSLATE = "translate"
    CUSTOM = "custom"


class DataClassification(str, Enum):
    """Data classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class SourceType(str, Enum):
    """Types of data sources."""
    DATABASE = "database"
    API = "api"
    FILE = "file"
    VECTOR_STORE = "vector_store"
    CACHE = "cache"
    EXTERNAL = "external"
    USER_INPUT = "user_input"


class AccessType(str, Enum):
    """Types of data access."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"


class ConsentType(str, Enum):
    """Legal basis for processing under GDPR."""
    EXPLICIT = "explicit"
    IMPLIED = "implied"
    LEGITIMATE_INTEREST = "legitimate_interest"
    CONTRACTUAL_NECESSITY = "contractual_necessity"
    LEGAL_OBLIGATION = "legal_obligation"
    NONE = "none"


class Environment(str, Enum):
    """Deployment environment."""
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TESTING = "testing"


class SourceAccessed(BaseModel):
    """A single data source accessed during the decision."""
    source_id: str
    source_type: SourceType
    access_type: AccessType
    data_classification: Optional[DataClassification] = None
    records_affected: Optional[int] = None
    authorization_verified: Optional[bool] = None


class DataWritten(BaseModel):
    """Data written during the decision."""
    destination_id: Optional[str] = None
    destination_type: Optional[str] = None
    data_classification: Optional[DataClassification] = None
    records_affected: Optional[int] = None


class DataLineage(BaseModel):
    """Complete record of data accessed during this decision."""
    sources_accessed: List[SourceAccessed] = Field(default_factory=list)
    data_written: List[DataWritten] = Field(default_factory=list)
    retention_policy: Optional[str] = None


class ConsentFlags(BaseModel):
    """User consent status for this interaction."""
    user_consent_obtained: bool
    consent_type: ConsentType
    consent_timestamp: Optional[str] = None
    consent_scope: Optional[List[str]] = None
    data_processing_purpose: Optional[str] = Field(None, max_length=256)
    right_to_explanation: Optional[bool] = None
    human_oversight_available: Optional[bool] = None


class InputSummary(BaseModel):
    """Sanitized summary of inputs to the decision."""
    prompt_hash: str
    input_length_tokens: int = Field(ge=0)
    input_classification: Optional[DataClassification] = None
    pii_detected: bool
    pii_types: Optional[List[str]] = None
    data_sources: Optional[List[str]] = None


class OutputSummary(BaseModel):
    """Summary of the agent's output/decision."""
    output_hash: str
    output_length_tokens: int = Field(ge=0)
    decision: str = Field(max_length=512)
    rationale: Optional[str] = Field(None, max_length=2048)
    pii_detected: bool
    pii_types: Optional[List[str]] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)


class HumanReview(BaseModel):
    """Human oversight details."""
    reviewer_id: Optional[str] = None
    review_timestamp: Optional[str] = None
    review_decision: Optional[str] = None  # approved, modified, rejected, overridden
    review_notes: Optional[str] = Field(None, max_length=1024)


class AuditEvent(BaseModel):
    """
    A single AI agent decision event for compliance auditing.

    Conforms to the schema defined in docs/compliance_audit_schema.md.
    Once created, events are immutable (use model_copy for derived versions).
    """
    event_id: str  # UUIDv7 preferred
    timestamp: str  # ISO 8601 UTC
    agent_name: str = Field(max_length=128)
    action_type: ActionType
    input_summary: InputSummary
    output_summary: OutputSummary
    model_version: str = Field(max_length=64)
    risk_score: float = Field(ge=0, le=100)

    # Optional fields from schema
    agent_id: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    model_provider: Optional[str] = Field(None, max_length=64)
    user_id: Optional[str] = Field(None, max_length=128)
    session_id: Optional[str] = None
    data_lineage: Optional[DataLineage] = None
    consent_flags: Optional[ConsentFlags] = None
    risk_factors: Optional[List[str]] = None
    compliance_tags: Optional[List[str]] = None
    human_review: Optional[HumanReview] = None
    latency_ms: Optional[int] = Field(None, ge=0)
    cost_usd: Optional[float] = Field(None, ge=0)
    environment: Optional[Environment] = None
    version_tag: Optional[str] = Field(None, max_length=64)
    metadata: Optional[Dict[str, str]] = None

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate that timestamp is proper ISO 8601."""
        try:
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid ISO 8601 timestamp: {v}")

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return self.model_dump(mode="json")

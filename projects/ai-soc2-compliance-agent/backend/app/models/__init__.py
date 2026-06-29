"""Database models for SOC2 compliance."""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class ControlStatus(str, PyEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    EVIDENCE_COLLECTED = "evidence_collected"
    REVIEW_PENDING = "review_pending"
    COMPLETE = "complete"
    FAILING = "failing"


class EvidenceType(str, PyEnum):
    POLICY = "policy"
    SCREENSHOT = "screenshot"
    LOG = "log"
    CONFIG = "config"
    TICKET = "ticket"
    CHAT = "chat"
    DOCUMENT = "document"
    ATTESTATION = "attestation"
    AUTOMATED = "automated"


class AuditStatus(str, PyEnum):
    NOT_STARTED = "not_started"
    PREPARATION = "preparation"
    EVIDENCE_COLLECTION = "evidence_collection"
    AUDITOR_REVIEW = "auditor_review"
    REMEDIATION = "remediation"
    COMPLETE = "complete"


class ComplianceControl(Base):
    """A SOC2 Trust Services Criteria control."""

    __tablename__ = "controls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    control_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subcategory: Mapped[str] = mapped_column(String(100), default="")
    tsc_criterion: Mapped[str] = mapped_column(String(50), default="")  # CC6.1, CC7.2, etc.
    status: Mapped[ControlStatus] = mapped_column(Enum(ControlStatus), default=ControlStatus.NOT_STARTED)
    assignee: Mapped[str] = mapped_column(String(255), default="")
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    evidence_items: Mapped[list["Evidence"]] = relationship("Evidence", back_populates="control", cascade="all, delete-orphan")


class Evidence(Base):
    """Evidence collected for a control."""

    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    control_id: Mapped[int] = mapped_column(ForeignKey("controls.id"), nullable=False, index=True)
    evidence_type: Mapped[EvidenceType] = mapped_column(Enum(EvidenceType), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(512), default="")  # Where it came from
    source_url: Mapped[str] = mapped_column(String(2048), default="")
    file_path: Mapped[str] = mapped_column(String(1024), default="")
    file_hash: Mapped[str] = mapped_column(String(128), default="")
    collected_by: Mapped[str] = mapped_column(String(100), default="auto")  # auto, manual, integration
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    raw_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    control: Mapped["ComplianceControl"] = relationship("ComplianceControl", back_populates="evidence_items")


class Audit(Base):
    """A SOC2 audit engagement."""

    __tablename__ = "audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    audit_type: Mapped[str] = mapped_column(String(50), default="SOC2 Type II")  # Type I or Type II
    status: Mapped[AuditStatus] = mapped_column(Enum(AuditStatus), default=AuditStatus.NOT_STARTED)
    auditor_name: Mapped[str] = mapped_column(String(255), default="")
    auditor_contact: Mapped[str] = mapped_column(String(512), default="")
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    observation_period_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    observation_period_end: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Policy(Base):
    """Security policies and procedures."""

    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    content: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="draft")
    owner: Mapped[str] = mapped_column(String(255), default="")
    review_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[str] = mapped_column(String(255), default="")
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Integration(Base):
    """Connected third-party services for automated evidence collection."""

    __tablename__ = "integrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    integration_type: Mapped[str] = mapped_column(String(50), default="api")
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="connected")
    last_sync_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    credentials_encrypted: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

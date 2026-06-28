import enum
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, DateTime, Enum, ForeignKey, Integer, 
    Boolean, JSON, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class ContractType(str, enum.Enum):
    NDA = "nda"
    MSA = "msa"
    OTHER = "other"


class ContractStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ClauseRiskLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    APPROVED = "approved"


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    contracts = relationship("Contract", back_populates="owner")
    playbooks = relationship("Playbook", back_populates="owner")


class Contract(Base):
    __tablename__ = "contracts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    contract_type = Column(Enum(ContractType), default=ContractType.OTHER)
    status = Column(Enum(ContractStatus), default=ContractStatus.UPLOADED, index=True)
    extracted_text = Column(Text)
    clause_analysis = Column(JSON)
    risk_summary = Column(JSON)
    redline_docx_path = Column(String(500))
    redline_pdf_path = Column(String(500))
    playbook_id = Column(UUID(as_uuid=True), ForeignKey("playbooks.id"))
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    error_message = Column(Text)
    processing_time_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    owner = relationship("User", back_populates="contracts")
    playbook = relationship("Playbook", back_populates="contracts")
    
    __table_args__ = (
        Index("ix_contracts_owner_created", "owner_id", "created_at"),
        Index("ix_contracts_status_created", "status", "created_at"),
    )


class Playbook(Base):
    __tablename__ = "playbooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    contract_type = Column(Enum(ContractType), default=ContractType.OTHER)
    rules = Column(JSON, nullable=False)  # YAML/JSON rules
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = relationship("User", back_populates="playbooks")
    contracts = relationship("Contract", back_populates="playbook")
    
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_playbook_owner_name"),
    )


class ClauseRule(Base):
    __tablename__ = "clause_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    playbook_id = Column(UUID(as_uuid=True), ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False)
    clause_name = Column(String(255), nullable=False)
    clause_patterns = Column(JSON, nullable=False)  # Regex patterns to identify clause
    required_elements = Column(JSON)  # Required elements in clause
    forbidden_elements = Column(JSON)  # Forbidden elements in clause
    risk_level = Column(Enum(ClauseRiskLevel), default=ClauseRiskLevel.MEDIUM)
    redline_suggestion = Column(Text)
    explanation = Column(Text)
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    playbook = relationship("Playbook", back_populates="rules")


# Add rules relationship to Playbook
Playbook.rules = relationship("ClauseRule", back_populates="playbook", order_by="ClauseRule.order", cascade="all, delete-orphan")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(String(255), unique=True, index=True)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(255))
    result = Column(JSON)
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    contract = relationship("Contract")
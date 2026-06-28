"""
ContractLens Database Models
Using SQLAlchemy with SQLite
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class ContractType(str, enum.Enum):
    NDA = "NDA"
    MSA = "MSA"
    SOW = "SOW"
    DPA = "DPA"
    EMPLOYMENT = "EMPLOYMENT"
    VENDOR = "VENDOR"
    OTHER = "OTHER"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnalysisStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ClauseType(str, enum.Enum):
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


class Contract(Base):
    __tablename__ = "contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    contract_type = Column(SQLEnum(ContractType), default=ContractType.OTHER)
    content_text = Column(Text, nullable=False)
    file_size = Column(Integer)
    page_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analyses = relationship("Analysis", back_populates="contract", cascade="all, delete-orphan")
    clauses = relationship("Clause", back_populates="contract", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    status = Column(SQLEnum(AnalysisStatus), default=AnalysisStatus.PENDING)
    overall_risk_score = Column(Float, default=0.0)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)
    summary = Column(Text)
    key_findings = Column(JSON)  # List of key findings
    recommendations = Column(JSON)  # List of recommendations
    processing_time_ms = Column(Integer)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    contract = relationship("Contract", back_populates="analyses")
    risks = relationship("Risk", back_populates="analysis", cascade="all, delete-orphan")


class Clause(Base):
    __tablename__ = "clauses"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    clause_type = Column(SQLEnum(ClauseType), default=ClauseType.OTHER)
    title = Column(String(255))
    content = Column(Text, nullable=False)
    start_char = Column(Integer)
    end_char = Column(Integer)
    page_number = Column(Integer)
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    contract = relationship("Contract", back_populates="clauses")
    risks = relationship("Risk", back_populates="clause", cascade="all, delete-orphan")


class Risk(Base):
    __tablename__ = "risks"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    clause_id = Column(Integer, ForeignKey("clauses.id"), nullable=True)
    risk_type = Column(String(100), nullable=False)  # e.g., "UNLIMITED_LIABILITY", "BROAD_INDEMNITY"
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False)
    confidence_score = Column(Float, default=0.0)
    location = Column(String(255))  # e.g., "Section 5.2, Paragraph 3"
    suggestion = Column(Text)  # Suggested fix
    reference_clause = Column(Text)  # The actual clause text
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("Analysis", back_populates="risks")
    clause = relationship("Clause", back_populates="risks")


class ContractTemplate(Base):
    __tablename__ = "contract_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    contract_type = Column(SQLEnum(ContractType), nullable=False)
    description = Column(Text)
    template_content = Column(Text, nullable=False)  # Template with placeholders
    key_clauses = Column(JSON)  # Required clauses for this type
    risk_patterns = Column(JSON)  # Known risk patterns for this type
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
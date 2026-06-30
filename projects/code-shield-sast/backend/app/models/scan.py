"""Scan models."""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    repository = Column(String(500), nullable=False)
    branch = Column(String(200), default="main")
    status = Column(Enum(ScanStatus), default=ScanStatus.PENDING)
    total_files = Column(Integer, default=0)
    scanned_files = Column(Integer, default=0)
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    info_count = Column(Integer, default=0)
    risk_score = Column(Float, default=0.0)
    scan_duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False)
    file_path = Column(String(1000), nullable=False)
    line_number = Column(Integer, nullable=True)
    rule_id = Column(String(100), nullable=False)
    severity = Column(Enum(Severity), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    remediation = Column(Text, nullable=True)
    cwe_id = Column(String(50), nullable=True)
    owasp_category = Column(String(100), nullable=True)
    code_snippet = Column(Text, nullable=True)
    confidence = Column(Float, default=0.8)
    created_at = Column(DateTime, default=datetime.utcnow)

    scan = relationship("Scan", back_populates="findings")


# Alias for compatibility
ScanResult = Finding

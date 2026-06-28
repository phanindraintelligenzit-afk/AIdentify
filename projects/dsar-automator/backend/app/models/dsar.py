"""SQLAlchemy models for DSAR data."""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
import enum
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class DSARStatusEnum(str, enum.Enum):
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


class RegulationEnum(str, enum.Enum):
    GDPR = "gdpr"
    CCPA = "ccpa"
    LGPD = "lgpd"
    OTHER = "other"


class RequestTypeEnum(str, enum.Enum):
    ACCESS = "access"
    ERASURE = "erasure"
    RECTIFICATION = "rectification"
    PORTABILITY = "portability"
    OBJECTION = "objection"


class DSARRequest(Base):
    __tablename__ = "dsar_requests"

    id = Column(Integer, primary_key=True, index=True)
    reference_number = Column(String(50), unique=True, index=True, nullable=False)
    requester_name = Column(String(255))
    requester_email = Column(String(255), index=True)
    requester_phone = Column(String(50))
    request_type = Column(String(50))
    regulation = Column(String(20), default="gdpr")
    status = Column(String(50), default="received")
    description = Column(Text)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    deadline_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    assigned_to = Column(Integer)
    risk_level = Column(String(20), default="low")
    records_found_count = Column(Integer, default=0)
    data_categories_found = Column(JSON, default=list)
    response_package_id = Column(Integer)
    response_sent_at = Column(DateTime(timezone=True))
    response_method = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DiscoveryResult(Base):
    __tablename__ = "discovery_results"

    id = Column(Integer, primary_key=True, index=True)
    dsar_id = Column(Integer, index=True)
    source_system = Column(String(100))
    source_name = Column(String(255))
    data_category = Column(String(100))
    records_count = Column(Integer, default=0)
    data_schema = Column(JSON)
    contains_pii = Column(Integer, default=0)
    contains_third_party_data = Column(Integer, default=0)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    dsar_id = Column(Integer, index=True)
    action = Column(String(100))
    performed_by = Column(String(100))
    details = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

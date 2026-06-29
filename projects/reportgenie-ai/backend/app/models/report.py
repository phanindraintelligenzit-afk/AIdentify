"""SQLAlchemy models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    source_type = Column(String(50), nullable=False)
    config = Column(JSON, default=dict)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_synced_at = Column(DateTime, nullable=True)
    row_count = Column(Integer, default=0)

    reports = relationship("Report", secondary="report_sources", back_populates="data_sources")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, default="")
    template_type = Column(String(50), default="executive_summary")
    status = Column(String(20), default="draft")
    output_format = Column(String(20), default="html")
    generated_content = Column(Text, nullable=True)
    metrics = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    generated_at = Column(DateTime, nullable=True)

    data_sources = relationship("DataSource", secondary="report_sources", back_populates="reports")


class ReportSource(Base):
    __tablename__ = "report_sources"

    report_id = Column(Integer, ForeignKey("reports.id"), primary_key=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.id"), primary_key=True)


class ReportSchedule(Base):
    __tablename__ = "report_schedules"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    frequency = Column(String(20), default="weekly")
    day_of_week = Column(Integer, default=1)
    hour = Column(Integer, default=9)
    recipients = Column(JSON, default=list)
    is_active = Column(Integer, default=1)
    last_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

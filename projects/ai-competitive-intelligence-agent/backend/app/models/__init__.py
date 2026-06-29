"""Database models for competitive intelligence."""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class SignalType(str, PyEnum):
    """Types of competitive signals."""
    WEBSITE_CHANGE = "website_change"
    PRICING_CHANGE = "pricing_change"
    JOB_POSTING = "job_posting"
    PRODUCT_LAUNCH = "product_launch"
    REVIEW_UPDATE = "review_update"
    SOCIAL_MENTION = "social_mention"
    PRESS_RELEASE = "press_release"
    FUNDING = "funding"
    TECH_STACK = "tech_stack"
    CONTENT_PUBLISHED = "content_published"


class SignalSeverity(str, PyEnum):
    """Severity levels for signals."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Competitor(Base):
    """A competitor being monitored."""

    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    industry: Mapped[str] = mapped_column(String(100), default="")
    employee_count: Mapped[str] = mapped_column(String(50), default="")
    funding_stage: Mapped[str] = mapped_column(String(100), default="")
    logo_url: Mapped[str] = mapped_column(String(1024), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Monitoring config
    monitor_website: Mapped[bool] = mapped_column(Boolean, default=True)
    monitor_pricing: Mapped[bool] = mapped_column(Boolean, default=True)
    monitor_jobs: Mapped[bool] = mapped_column(Boolean, default=True)
    monitor_reviews: Mapped[bool] = mapped_column(Boolean, default=True)
    monitor_social: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    signals: Mapped[list["Signal"]] = relationship("Signal", back_populates="competitor", cascade="all, delete-orphan")
    battlecards: Mapped[list["Battlecard"]] = relationship("Battlecard", back_populates="competitor", cascade="all, delete-orphan")


class Signal(Base):
    """A detected competitive signal."""

    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id"), nullable=False, index=True)
    signal_type: Mapped[SignalType] = mapped_column(Enum(SignalType), nullable=False, index=True)
    severity: Mapped[SignalSeverity] = mapped_column(Enum(SignalSeverity), default=SignalSeverity.MEDIUM)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str] = mapped_column(String(2048), default="")
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    competitor: Mapped["Competitor"] = relationship("Competitor", back_populates="signals")


class Battlecard(Base):
    """A generated battlecard for a competitor."""

    __tablename__ = "battlecards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    overview: Mapped[str] = mapped_column(Text, default="")
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list)
    win_strategies: Mapped[list] = mapped_column(JSON, default=list)
    loss_risks: Mapped[list] = mapped_column(JSON, default=list)
    key_differentiators: Mapped[list] = mapped_column(JSON, default=list)
    pricing_intel: Mapped[str] = mapped_column(Text, default="")
    target_accounts: Mapped[list] = mapped_column(JSON, default=list)
    objection_handlers: Mapped[dict] = mapped_column(JSON, default=dict)
    talk_track: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    generated_by: Mapped[str] = mapped_column(String(50), default="ai")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    competitor: Mapped["Competitor"] = relationship("Competitor", back_populates="battlecards")


class Briefing(Base):
    """A competitive briefing / digest."""

    __tablename__ = "briefings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    signal_ids: Mapped[list] = mapped_column(JSON, default=list)
    competitor_ids: Mapped[list] = mapped_column(JSON, default=list)
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

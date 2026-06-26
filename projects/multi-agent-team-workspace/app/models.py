"""SQLAlchemy models for the workspace."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class AssigneeType(str, enum.Enum):
    HUMAN = "human"
    AGENT = "agent"


class TaskStatus(str, enum.Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"
    HANDOFF_PENDING = "handoff_pending"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.BACKLOG, nullable=False)
    assignee_name = Column(String(100), nullable=True)
    assignee_type = Column(SQLEnum(AssigneeType), nullable=True)
    priority = Column(Integer, default=0)  # 0=low, 1=medium, 2=high, 3=urgent
    context = Column(Text, default="")  # Shared context document
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)

    handoffs = relationship("Handoff", back_populates="task", cascade="all, delete-orphan")
    audit_entries = relationship("AuditEntry", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"


class HandoffStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Handoff(Base):
    __tablename__ = "handoffs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    from_assignee = Column(String(100), nullable=False)
    to_assignee = Column(String(100), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(SQLEnum(HandoffStatus), default=HandoffStatus.PENDING)
    rejection_reason = Column(Text, nullable=True)
    initiated_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    task = relationship("Task", back_populates="handoffs")

    def __repr__(self):
        return f"<Handoff(id={self.id}, task_id={self.task_id}, status='{self.status}')>"


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    actor = Column(String(100), nullable=False)
    actor_type = Column(SQLEnum(AssigneeType), nullable=False)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="audit_entries")

    def __repr__(self):
        return f"<AuditEntry(id={self.id}, actor='{self.actor}', action='{self.action}')>"

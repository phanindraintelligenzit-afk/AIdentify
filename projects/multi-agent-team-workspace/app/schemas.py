"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models import AssigneeType, TaskStatus, HandoffStatus


# --- Task Schemas ---

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    priority: int = Field(0, ge=0, le=3)


class TaskCreate(TaskBase):
    created_by: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = Field(None, ge=0, le=3)


class TaskAssign(BaseModel):
    assignee_name: str = Field(..., min_length=1, max_length=100)
    assignee_type: AssigneeType


class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    assignee_name: Optional[str]
    assignee_type: Optional[AssigneeType]
    context: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int


# --- Context Schemas ---

class ContextUpdate(BaseModel):
    content: str
    updated_by: str = Field(..., min_length=1, max_length=100)


class ContextResponse(BaseModel):
    task_id: int
    context: str
    updated_at: Optional[datetime] = None


# --- Handoff Schemas ---

class HandoffCreate(BaseModel):
    task_id: int
    to_assignee: str = Field(..., min_length=1, max_length=100)
    reason: str = Field(..., min_length=1)


class HandoffAccept(BaseModel):
    accepted_by: str = Field(..., min_length=1, max_length=100)


class HandoffReject(BaseModel):
    rejected_by: str = Field(..., min_length=1, max_length=100)
    reason: str = Field(..., min_length=1)


class HandoffResponse(BaseModel):
    id: int
    task_id: int
    from_assignee: str
    to_assignee: str
    reason: str
    status: HandoffStatus
    rejection_reason: Optional[str]
    initiated_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


# --- Audit Schemas ---

class AuditEntryResponse(BaseModel):
    id: int
    task_id: Optional[int]
    actor: str
    actor_type: AssigneeType
    action: str
    entity_type: str
    entity_id: Optional[int]
    details: Optional[dict]
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditTrailResponse(BaseModel):
    entries: List[AuditEntryResponse]
    total: int

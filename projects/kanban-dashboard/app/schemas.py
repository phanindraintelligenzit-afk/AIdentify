"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models import AgentType, TaskPriority, TaskStatus


# ─── Label Schemas ───────────────────────────────────────────────
class LabelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")


class LabelCreate(LabelBase):
    pass


class LabelResponse(LabelBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Tag Schemas ─────────────────────────────────────────────────
class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Column Schemas ──────────────────────────────────────────────
class ColumnBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    position: int = Field(default=0, ge=0)
    color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")


class ColumnCreate(ColumnBase):
    pass


class ColumnUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    position: Optional[int] = Field(None, ge=0)
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")


class ColumnResponse(ColumnBase):
    id: int
    board_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Board Schemas ───────────────────────────────────────────────
class BoardBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")


class BoardCreate(BoardBase):
    columns: Optional[List[ColumnCreate]] = None


class BoardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    slug: Optional[str] = Field(None, min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    is_active: Optional[bool] = None


class BoardResponse(BoardBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    columns: List[ColumnResponse] = []
    task_count: Optional[int] = None

    model_config = {"from_attributes": True}


# ─── Activity Log Schemas ────────────────────────────────────────
class ActivityLogResponse(BaseModel):
    id: int
    task_id: int
    action: str
    description: Optional[str]
    agent: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Task Schemas ────────────────────────────────────────────────
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.BACKLOG
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: AgentType = AgentType.OWL
    due_date: Optional[datetime] = None
    position: int = Field(default=0, ge=0)
    label_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None


class TaskCreate(TaskBase):
    board_id: Optional[int] = None
    column_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[AgentType] = None
    due_date: Optional[datetime] = None
    column_id: Optional[int] = None
    position: Optional[int] = Field(None, ge=0)
    is_completed: Optional[bool] = None
    label_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None


class TaskResponse(BaseModel):
    id: int
    board_id: int
    column_id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    assignee: str
    due_date: Optional[datetime]
    position: int
    is_completed: bool
    labels: List[LabelResponse] = []
    tags: List[TagResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskMove(BaseModel):
    column_id: int
    position: int


class TaskBulkUpdate(BaseModel):
    task_ids: List[int] = Field(..., min_length=1)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[AgentType] = None
    column_id: Optional[int] = None


class TaskBulkCreate(BaseModel):
    tasks: List[TaskCreate] = Field(..., min_length=1)


# ─── Stats Schemas ───────────────────────────────────────────────
class BoardStats(BaseModel):
    total_tasks: int
    by_status: dict
    by_assignee: dict
    by_priority: dict
    overdue_count: int


# ─── Webhook Schemas ─────────────────────────────────────────────
class WebhookBase(BaseModel):
    url: str = Field(..., min_length=1, max_length=500)
    events: str = Field(default="task.created,task.updated,task.deleted")
    secret: Optional[str] = None


class WebhookCreate(WebhookBase):
    pass


class WebhookResponse(WebhookBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Agent Schemas ───────────────────────────────────────────────
class AgentTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    board_id: Optional[int] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    labels: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class AgentTaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None

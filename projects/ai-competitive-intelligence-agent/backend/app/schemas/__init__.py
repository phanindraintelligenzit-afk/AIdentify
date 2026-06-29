"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

from models import SignalSeverity, SignalType


# ── Competitor schemas ──

class CompetitorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: HttpUrl
    description: str = ""
    industry: str = ""
    employee_count: str = ""
    funding_stage: str = ""
    logo_url: str = ""
    monitor_website: bool = True
    monitor_pricing: bool = True
    monitor_jobs: bool = True
    monitor_reviews: bool = True
    monitor_social: bool = False


class CompetitorCreate(CompetitorBase):
    def model_dump(self, **kwargs):
        """Convert HttpUrl to string for DB compatibility."""
        data = super().model_dump(**kwargs)
        if hasattr(data.get("domain"), "__str__"):
            data["domain"] = str(data["domain"])
        return data


class CompetitorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    employee_count: Optional[str] = None
    funding_stage: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None
    monitor_website: Optional[bool] = None
    monitor_pricing: Optional[bool] = None
    monitor_jobs: Optional[bool] = None
    monitor_reviews: Optional[bool] = None
    monitor_social: Optional[bool] = None


class CompetitorResponse(CompetitorBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompetitorListResponse(BaseModel):
    total: int
    items: list[CompetitorResponse]


# ── Signal schemas ──

class SignalResponse(BaseModel):
    id: int
    competitor_id: int
    competitor_name: str = ""
    signal_type: SignalType
    severity: SignalSeverity
    title: str
    description: str
    source_url: str
    confidence_score: float
    is_read: bool
    is_archived: bool
    detected_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class SignalListResponse(BaseModel):
    total: int
    unread: int
    items: list[SignalResponse]


class SignalMarkRead(BaseModel):
    signal_ids: list[int]


# ── Battlecard schemas ──

class BattlecardBase(BaseModel):
    title: str
    overview: str = ""
    strengths: list[str] = []
    weaknesses: list[str] = []
    win_strategies: list[str] = []
    loss_risks: list[str] = []
    key_differentiators: list[str] = []
    pricing_intel: str = ""
    target_accounts: list[str] = []
    objection_handlers: dict[str, str] = {}
    talk_track: str = ""


class BattlecardCreate(BattlecardBase):
    competitor_id: int


class BattlecardGenerateRequest(BaseModel):
    competitor_id: int
    include_pricing: bool = True
    include_reviews: bool = True


class BattlecardResponse(BattlecardBase):
    id: int
    competitor_id: int
    competitor_name: str = ""
    version: int
    is_published: bool
    generated_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Briefing schemas ──

class BriefingCreate(BaseModel):
    title: str
    period_days: int = Field(default=7, ge=1, le=90)


class BriefingResponse(BaseModel):
    id: int
    title: str
    summary: str
    signal_ids: list[int]
    competitor_ids: list[int]
    period_start: datetime
    period_end: datetime
    is_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Dashboard schemas ──

class DashboardStats(BaseModel):
    total_competitors: int
    active_monitors: int
    signals_today: int
    signals_this_week: int
    unread_signals: int
    battlecards_published: int
    latest_signals: list[SignalResponse]

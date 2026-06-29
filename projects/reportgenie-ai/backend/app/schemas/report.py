"""Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DataSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    source_type: str = Field(..., pattern="^(stripe|hubspot|ganalytics|jira|csv|api|postgres|mysql)$")
    config: dict = Field(default_factory=dict)


class DataSourceResponse(BaseModel):
    id: int
    name: str
    source_type: str
    config: dict
    status: str
    created_at: datetime
    last_synced_at: Optional[datetime] = None
    row_count: int = 0

    class Config:
        from_attributes = True


class ReportCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str = ""
    template_type: str = "executive_summary"
    data_source_ids: list[int] = Field(default_factory=list)
    output_format: str = "html"


class ReportUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ReportResponse(BaseModel):
    id: int
    title: str
    description: str
    template_type: str
    status: str
    output_format: str
    generated_content: Optional[str] = None
    metrics: dict
    created_at: datetime
    updated_at: datetime
    generated_at: Optional[datetime] = None
    data_sources: list[DataSourceResponse] = []

    class Config:
        from_attributes = True


class GenerateRequest(BaseModel):
    report_id: int
    prompt_override: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    total_reports: int
    total_data_sources: int
    scheduled_reports: int

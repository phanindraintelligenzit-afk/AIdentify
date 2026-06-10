"""API request/response models with validation."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Pipeline Models ──

class PipelineCreateRequest(BaseModel):
    """Request to create and run a pipeline."""

    name: str = Field(default="unnamed", description="Pipeline name")
    input: str = Field(..., description="Input text for the pipeline")
    constraints: list[str] = Field(default_factory=list)
    topology: str = Field(default="sequential", description="Topology type")
    agents: list[dict[str, Any]] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)


class PipelineResponse(BaseModel):
    """Response from a pipeline run."""

    pipeline_id: str
    trace_id: str
    status: str
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    agent_results: dict[str, Any] = Field(default_factory=dict)
    agents_executed: int = 0
    created_at: str = ""
    completed_at: str | None = None


class PipelineStatusResponse(BaseModel):
    """Pipeline status check response."""

    pipeline_id: str
    status: str
    current_step: int = 0
    total_steps: int = 0


# ── Agent Models ──

class AgentCreateRequest(BaseModel):
    """Request to register an agent."""

    agent_id: str
    role: str = ""
    model: str = "openrouter/owl-alpha"
    system_prompt: str = ""
    temperature: float = 0.0
    max_tokens: int = 2000
    tools: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)


class AgentResponse(BaseModel):
    """Agent information response."""

    agent_id: str
    role: str
    model: str
    status: str = "registered"


class AgentRunRequest(BaseModel):
    """Request to run a single agent."""

    input: str
    context: dict[str, Any] = Field(default_factory=dict)


class AgentRunResponse(BaseModel):
    """Response from a single agent run."""

    agent_id: str
    status: str
    output: dict[str, Any] = Field(default_factory=dict)
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    confidence: float = 0.0


# ── Eval Models ──

class EvalRunRequest(BaseModel):
    """Request to run an eval suite."""

    suite_name: str
    pipeline_config: dict[str, Any] = Field(default_factory=dict)


class EvalCaseRequest(BaseModel):
    """Request to add an eval case."""

    case_id: str
    input_text: str
    expected_output: dict[str, Any] = Field(default_factory=dict)
    expected_behavior: str = ""
    constraints: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class EvalSuiteResponse(BaseModel):
    """Eval suite information."""

    name: str
    case_count: int = 0
    baseline_score: float = 0.0
    pass_threshold: float = 0.8


class EvalResultResponse(BaseModel):
    """Eval run result."""

    suite: str
    total_cases: int = 0
    passed: int = 0
    failed: int = 0
    pass_rate: float = 0.0
    average_score: float = 0.0
    meets_baseline: bool = False
    results: list[dict[str, Any]] = Field(default_factory=list)


# ── Metrics Models ──

class MetricsSummaryResponse(BaseModel):
    """Metrics summary response."""

    total_runs: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    recent_runs: list[dict[str, Any]] = Field(default_factory=list)


class BudgetAlertResponse(BaseModel):
    """Budget alert information."""

    alert_type: str
    message: str
    value: float
    threshold: float
    timestamp: str = ""


# ── Error Models ──

class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str = ""
    status_code: int = 500


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    service: str = "AgentsFactory"

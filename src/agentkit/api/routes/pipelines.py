"""Pipeline API routes — CRUD + execution + tracing."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from agentkit.api.models import (
    ErrorResponse,
    PipelineCreateRequest,
    PipelineResponse,
    PipelineStatusResponse,
)
from agentkit.agents.roles import ResearcherAgent, AnalyzerAgent, WriterAgent, EvaluatorAgent
from agentkit.config import settings
from agentkit.core.context import ContextManager
from agentkit.models.topology import AgentConfig, TopologyConfig, TopologyType
from agentkit.observability.metrics import MetricsCollector
from agentkit.observability.tracer import PipelineTracer
from agentkit.orchestrator.engine import Orchestrator

router = APIRouter(prefix="/pipelines", tags=["pipelines"])

# In-memory store for active pipelines (would be DB in production)
_active_pipelines: dict[str, dict] = {}
_collector = MetricsCollector()


def _create_agent_from_config(agent_data: dict) -> Any:
    """Create an agent from config dict."""
    role = agent_data.get("role", "researcher")
    config = AgentConfig(
        agent_id=agent_data.get("id", f"agent_{role}"),
        role=role,
        model=agent_data.get("model", "openrouter/owl-alpha"),
        system_prompt=agent_data.get("system_prompt", ""),
        temperature=agent_data.get("temperature", 0.0),
        max_tokens=agent_data.get("max_tokens", 2000),
    )
    role_map = {
        "researcher": ResearcherAgent,
        "analyzer": AnalyzerAgent,
        "writer": WriterAgent,
        "evaluator": EvaluatorAgent,
    }
    agent_class = role_map.get(role, ResearcherAgent)
    return agent_class(config=config)


@router.post("/run", response_model=PipelineResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def run_pipeline(request: PipelineCreateRequest) -> dict:
    """Create and run a pipeline.

    Example request:
    ```json
    {
        "name": "research_pipeline",
        "input": "Explain circuit breakers",
        "topology": "sequential",
        "agents": [
            {"id": "researcher", "role": "researcher"},
            {"id": "analyzer", "role": "analyzer"},
            {"id": "writer", "role": "writer"}
        ]
    }
    ```
    """
    if not request.input:
        raise HTTPException(status_code=400, detail="Input is required")

    if not settings.openrouter_api_key:
        raise HTTPException(status_code=401, detail="OpenRouter API key not configured")

    try:
        # Create agents
        agents = [_create_agent_from_config(a) for a in request.agents]
        if not agents:
            # Default pipeline
            agents = [
                ResearcherAgent(config=AgentConfig(agent_id="researcher", role="researcher")),
                AnalyzerAgent(config=AgentConfig(agent_id="analyzer", role="analyzer")),
                WriterAgent(config=AgentConfig(agent_id="writer", role="writer")),
            ]

        # Create topology
        topology = TopologyConfig(
            name=request.name,
            topology_type=TopologyType(request.topology),
            agents=[a.config for a in agents],
        )

        # Execute
        tracer = PipelineTracer()
        orchestrator = Orchestrator(config=topology, agents=agents, tracer=tracer)
        state = await orchestrator.execute(
            input_text=request.input,
            constraints=request.constraints,
        )

        # Record metrics
        _collector.record_pipeline_start(state, name=request.name)
        for agent_id, result in state.agent_results.items():
            _collector.record_agent_result(state.pipeline_id, result)
        _collector.record_pipeline_end(state)

        # Build response
        agent_results = {}
        for aid, r in state.agent_results.items():
            agent_results[aid] = {
                "status": r.status.value,
                "output": r.output,
                "summary": r.summary,
                "confidence": r.confidence,
                "tokens_used": r.tokens_used,
                "cost_usd": r.cost_usd,
                "latency_ms": r.latency_ms,
            }

        return {
            "pipeline_id": state.pipeline_id,
            "trace_id": state.trace_id,
            "status": state.status,
            "total_tokens": state.total_tokens,
            "total_cost_usd": state.total_cost_usd,
            "total_latency_ms": state.total_latency_ms,
            "agent_results": agent_results,
            "agents_executed": len(state.agent_results),
            "created_at": state.created_at.isoformat() if state.created_at else "",
            "completed_at": state.completed_at.isoformat() if state.completed_at else None,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")


@router.get("/{pipeline_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(pipeline_id: str) -> dict:
    """Get pipeline status and results."""
    if pipeline_id in _active_pipelines:
        return _active_pipelines[pipeline_id]
    # Check metrics DB
    summary = _collector.get_summary(pipeline_id)
    if summary:
        return {
            "pipeline_id": pipeline_id,
            "status": summary.get("status", "unknown"),
            "current_step": summary.get("agent_count", 0),
            "total_steps": summary.get("agent_count", 0),
        }
    raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")


@router.get("/{pipeline_id}/trace")
async def get_pipeline_trace(pipeline_id: str) -> dict:
    """Get full execution trace for a pipeline."""
    summary = _collector.get_summary(pipeline_id)
    if summary:
        return {"pipeline_id": pipeline_id, "trace": summary}
    raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id} not found")


@router.get("/")
async def list_pipelines(limit: int = Query(default=20, le=100)) -> dict:
    """List recent pipeline runs."""
    runs = _collector.get_recent_runs(limit=limit)
    return {"pipelines": runs, "count": len(runs)}

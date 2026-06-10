"""Eval API routes — run eval suites, manage cases, view results."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from agentkit.api.models import (
    BudgetAlertResponse,
    ErrorResponse,
    EvalCaseRequest,
    EvalResultResponse,
    EvalRunRequest,
    EvalSuiteResponse,
    MetricsSummaryResponse,
)
from agentkit.config import settings
from agentkit.eval.runner import EvalCase, EvalRunner, EvalSuite
from agentkit.observability.metrics import MetricsCollector

router = APIRouter(prefix="/evals", tags=["evals"])

# Shared instances
_runner = EvalRunner()
_collector = MetricsCollector()


def _ensure_default_suite() -> None:
    """Create default eval suite if none exists."""
    if _runner.get_suite("default") is None:
        suite = EvalSuite(name="default", baseline_score=0.7, pass_threshold=0.7)
        suite.add_case(EvalCase(
            case_id="smoke_test",
            input_text="Explain what a circuit breaker pattern is in one paragraph.",
            expected_behavior="Should explain the pattern clearly",
            tags=["smoke_test"],
        ))
        _runner.register_suite(suite)


# Ensure default suite is created at import time
_ensure_default_suite()


@router.post("/run", response_model=EvalResultResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def run_eval(request: EvalRunRequest) -> dict:
    """Run an eval suite."""
    if not settings.openrouter_api_key:
        raise HTTPException(status_code=401, detail="OpenRouter API key not configured")

    suite = _runner.get_suite(request.suite_name)
    if not suite:
        raise HTTPException(status_code=404, detail=f"Suite '{request.suite_name}' not found")

    try:
        # Build orchestrator factory from pipeline config
        from agentkit.agents.roles import ResearcherAgent, AnalyzerAgent, WriterAgent
        from agentkit.core.context import ContextManager
        from agentkit.models.topology import AgentConfig, TopologyConfig, TopologyType
        from agentkit.observability.tracer import PipelineTracer
        from agentkit.orchestrator.engine import Orchestrator

        def orchestrator_factory():
            agents = [
                ResearcherAgent(config=AgentConfig(agent_id="researcher", role="researcher")),
                AnalyzerAgent(config=AgentConfig(agent_id="analyzer", role="analyzer")),
                WriterAgent(config=AgentConfig(agent_id="writer", role="writer")),
            ]
            topology = TopologyConfig(
                name="eval_pipeline",
                topology_type=TopologyType.SEQUENTIAL,
                agents=[a.config for a in agents],
            )
            return Orchestrator(config=topology, agents=agents, tracer=PipelineTracer())

        summary = await _runner.run_suite(request.suite_name, orchestrator_factory)
        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eval run failed: {str(e)}")


@router.post("/suites", response_model=EvalSuiteResponse)
async def create_suite(name: str, baseline_score: float = 0.7, pass_threshold: float = 0.8) -> dict:
    """Create a new eval suite."""
    suite = EvalSuite(name=name, baseline_score=baseline_score, pass_threshold=pass_threshold)
    _runner.register_suite(suite)
    return {"name": name, "case_count": 0, "baseline_score": baseline_score, "pass_threshold": pass_threshold}


@router.get("/suites")
async def list_suites() -> dict:
    """List all eval suites."""
    suites = []
    for name in ["default"]:  # Would iterate _runner._suites in production
        suite = _runner.get_suite(name)
        if suite:
            suites.append({
                "name": suite.name,
                "case_count": suite.case_count,
                "baseline_score": suite.baseline_score,
            })
    return {"suites": suites}


@router.post("/suites/{suite_name}/cases")
async def add_eval_case(suite_name: str, request: EvalCaseRequest) -> dict:
    """Add a test case to an eval suite."""
    suite = _runner.get_suite(suite_name)
    if not suite:
        raise HTTPException(status_code=404, detail=f"Suite '{suite_name}' not found")

    case = EvalCase(
        case_id=request.case_id,
        input_text=request.input_text,
        expected_output=request.expected_output,
        expected_behavior=request.expected_behavior,
        constraints=request.constraints,
        tags=request.tags,
    )
    suite.add_case(case)
    return {"status": "added", "case_id": request.case_id, "suite": suite_name}


@router.get("/metrics", response_model=MetricsSummaryResponse)
async def get_metrics(limit: int = Query(default=20, le=100)) -> dict:
    """Get metrics summary."""
    runs = _collector.get_recent_runs(limit=limit)
    total_tokens = sum(r.get("total_tokens", 0) for r in runs)
    total_cost = sum(r.get("total_cost_usd", 0) for r in runs)
    avg_latency = (
        sum(r.get("total_latency_ms", 0) for r in runs) / len(runs) if runs else 0
    )
    return {
        "total_runs": len(runs),
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "avg_latency_ms": round(avg_latency, 2),
        "recent_runs": runs,
    }


@router.get("/alerts", response_model=list[BudgetAlertResponse])
async def get_budget_alerts(limit: int = Query(default=20, le=100)) -> list[dict]:
    """Get recent budget alerts."""
    alerts = _collector.get_budget_alerts(limit=limit)
    return alerts

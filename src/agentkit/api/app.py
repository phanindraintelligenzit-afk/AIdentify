"""FastAPI application for AgentsFactory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from agentkit import __version__
from agentkit.api.middleware import add_middleware
from agentkit.api.models import HealthResponse
from agentkit.api.routes.agents import router as agents_router
from agentkit.api.routes.evals import router as evals_router
from agentkit.api.routes.pipelines import router as pipelines_router
from agentkit.observability.metrics import MetricsCollector

_metrics = MetricsCollector()

app = FastAPI(
    title="AgentsFactory",
    description=(
        "Production Multi-Agent Orchestration Framework.\n\n"
        "## Features\n"
        "- **Pipeline Execution**: Run multi-agent pipelines with 4 topology patterns\n"
        "- **Agent Management**: Register and run individual LLM-powered agents\n"
        "- **Eval Framework**: LLM-as-a-Judge evaluation with regression detection\n"
        "- **Observability**: Cost/latency tracking, structured traces, budget alerts\n"
        "- **LangGraph Integration**: Bridge to LangGraph's state graph\n\n"
        "## Quick Start\n"
        "```bash\n"
        "curl -X POST http://localhost:8000/pipelines/run \\\n"
        "  -H 'Content-Type: application/json' \\\n"
        "  -d '{\"input\": \"Explain circuit breakers\", \"topology\": \"sequential\"}'\n"
        "```"
    ),
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add middleware
add_middleware(app)

# Register routes
app.include_router(pipelines_router)
app.include_router(agents_router)
app.include_router(evals_router)


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": __version__, "service": "AgentsFactory"}


@app.get("/", tags=["system"])
async def root():
    """API root with links."""
    return {
        "service": "AgentsFactory",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "pipelines": "/pipelines",
            "agents": "/agents",
            "evals": "/evals",
            "metrics": "/metrics",
        },
    }


@app.get("/metrics", tags=["observability"])
async def metrics():
    """Get observability metrics."""
    recent = _metrics.get_recent_runs(limit=20)
    return {
        "recent_runs": recent,
        "total_recorded": len(recent),
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": str(exc)},
    )

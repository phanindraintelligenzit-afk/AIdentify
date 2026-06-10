"""Agent API routes — register, list, run individual agents."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from agentkit.api.models import (
    AgentCreateRequest,
    AgentResponse,
    AgentRunRequest,
    AgentRunResponse,
    ErrorResponse,
)
from agentkit.agents.roles import ResearcherAgent, AnalyzerAgent, WriterAgent, EvaluatorAgent
from agentkit.config import settings
from agentkit.models.topology import AgentConfig

router = APIRouter(prefix="/agents", tags=["agents"])

# In-memory agent registry
_registered_agents: dict[str, Any] = {}


def _create_agent(config: AgentCreateRequest) -> Any:
    """Create an agent from request config."""
    agent_config = AgentConfig(
        agent_id=config.agent_id,
        role=config.role,
        model=config.model,
        system_prompt=config.system_prompt,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        tools=config.tools,
        allowed_tools=config.allowed_tools,
    )
    role_map = {
        "researcher": ResearcherAgent,
        "analyzer": AnalyzerAgent,
        "writer": WriterAgent,
        "evaluator": EvaluatorAgent,
    }
    agent_class = role_map.get(config.role, ResearcherAgent)
    return agent_class(config=agent_config)


@router.post("/register", response_model=AgentResponse, responses={400: {"model": ErrorResponse}})
async def register_agent(request: AgentCreateRequest) -> dict:
    """Register an agent for use in pipelines."""
    if not request.agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")

    agent = _create_agent(request)
    _registered_agents[request.agent_id] = agent

    return {
        "agent_id": request.agent_id,
        "role": request.role,
        "model": request.model,
        "status": "registered",
    }


@router.get("/", response_model=list[AgentResponse])
async def list_agents() -> list[dict]:
    """List all registered agents."""
    return [
        {
            "agent_id": agent_id,
            "role": agent.config.role,
            "model": agent.config.model,
            "status": "registered",
        }
        for agent_id, agent in _registered_agents.items()
    ]


@router.get("/{agent_id}", response_model=AgentResponse, responses={404: {"model": ErrorResponse}})
async def get_agent(agent_id: str) -> dict:
    """Get agent details."""
    if agent_id not in _registered_agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    agent = _registered_agents[agent_id]
    return {
        "agent_id": agent_id,
        "role": agent.config.role,
        "model": agent.config.model,
        "status": "registered",
    }


@router.post("/{agent_id}/run", response_model=AgentRunResponse, responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def run_agent(agent_id: str, request: AgentRunRequest) -> dict:
    """Run a single agent with the given input."""
    if agent_id not in _registered_agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    if not settings.openrouter_api_key:
        raise HTTPException(status_code=401, detail="OpenRouter API key not configured")

    agent = _registered_agents[agent_id]
    try:
        from agentkit.models.pipeline import PipelineState
        state = PipelineState(original_input=request.input)
        result = await agent.execute(state, **request.context)

        return {
            "agent_id": agent_id,
            "status": result.status.value,
            "output": result.output,
            "tokens_used": result.tokens_used,
            "cost_usd": result.cost_usd,
            "latency_ms": result.latency_ms,
            "confidence": result.confidence,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.delete("/{agent_id}")
async def unregister_agent(agent_id: str) -> dict:
    """Unregister an agent."""
    if agent_id in _registered_agents:
        del _registered_agents[agent_id]
        return {"status": "unregistered", "agent_id": agent_id}
    raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

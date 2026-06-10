# 🔬 AgentsFactory

> **Production Multi-Agent Orchestration Framework**

Build, deploy, and observe multi-agent AI pipelines with confidence. AgentsFactory provides the production patterns that raw LLM frameworks are missing: circuit breakers, context budget management, fallback chains, structured observability, eval-driven deployment gates, and human-in-the-loop escalation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Why AgentsFactory?

Building multi-agent systems with raw LangGraph/LangChain gets you 60% of the way. The remaining 40% — the stuff that makes or breaks production — is what AgentsFactory provides:

| Problem | AgentsFactory Solution |
|---------|----------------------|
| One agent failure kills the pipeline | Circuit breakers + fallback chains |
| Context window explodes in multi-hop pipelines | Automatic summarization + structured state |
| Can't trace which agent caused a bad output | Structured tracing with trace_id per span |
| No way to know if a model change regressed quality | Eval suites with baseline comparison + deployment gates |
| Runaway API costs from retry loops | Token budget enforcement + cost circuit breakers |
| Humans don't know when to intervene | HITL gates with configurable escalation criteria |

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  REST API (FastAPI)               │
│   POST /pipelines/run  │  GET /agents  │  POST /evals/run  │
├─────────────────────────────────────────────────┤
│              Orchestrator Engine                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│  │ Topology  │ │ Context  │ │  Fallback    │    │
│  │ Builder   │ │ Manager  │ │  Chains      │    │
│  └──────────┘ └──────────┘ └──────────────┘    │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐    │
│  │ Circuit  │ │   HITL   │ │ Permissions  │    │
│  │ Breaker  │ │  Gates   │ │   Matrix     │    │
│  └──────────┘ └──────────┘ └──────────────┘    │
├─────────────────────────────────────────────────┤
│           LangGraph Integration Layer            │
├─────────────────────────────────────────────────┤
│  LLM Client (OpenRouter)  │  Eval Framework     │
│  Observability (Tracer + Metrics + Dashboard)   │
└─────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install

```bash
git clone https://github.com/phanindraintelligenzit-afk/AgentsFactory.git
cd AgentsFactory

# Using uv (recommended)
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your OpenRouter API key
# Get a free key at: https://openrouter.ai/keys
```

### 3. Run a Pipeline

**Via Python:**
```python
import asyncio
from agentkit.agents.roles import ResearcherAgent, AnalyzerAgent, WriterAgent
from agentkit.models.topology import AgentConfig, TopologyConfig, TopologyType
from agentkit.orchestrator.engine import Orchestrator

async def main():
    agents = [
        ResearcherAgent(config=AgentConfig(agent_id="researcher", role="researcher")),
        AnalyzerAgent(config=AgentConfig(agent_id="analyzer", role="analyzer")),
        WriterAgent(config=AgentConfig(agent_id="writer", role="writer")),
    ]
    topology = TopologyConfig(
        name="research",
        topology_type=TopologyType.SEQUENTIAL,
        agents=[a.config for a in agents],
    )
    orchestrator = Orchestrator(config=topology, agents=agents)
    state = await orchestrator.execute("Explain circuit breakers in distributed systems")
    print(f"Status: {state.status}, Tokens: {state.total_tokens}, Cost: ${state.total_cost_usd:.6f}")

asyncio.run(main())
```

**Via REST API:**
```bash
# Start the server
uv run uvicorn agentkit.api.app:app --reload

# Run a pipeline
curl -X POST http://localhost:8000/pipelines/run \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Explain circuit breakers in distributed systems",
    "topology": "sequential",
    "agents": [
      {"id": "researcher", "role": "researcher"},
      {"id": "analyzer", "role": "analyzer"},
      {"id": "writer", "role": "writer"}
    ]
  }'
```

**Via YAML:**
```bash
uv run python -c "
from agentkit.orchestrator.yaml_loader import load_pipeline_config
config = load_pipeline_config('examples/research_pipeline.yaml')
print(f'Loaded: {config.name} with {len(config.agents)} agents')
"
```

### 4. View the Dashboard

```bash
uv run streamlit run src/agentkit/observability/dashboard.py
```

Open http://localhost:8501 in your browser.

### 5. Run Evals

```bash
uv run python examples/eval_pipeline.py
```

## Topology Patterns

| Pattern | Structure | Best For |
|---------|-----------|----------|
| **Sequential** | A→B→C | Linear workflows (research→draft→review) |
| **Parallel** | Router→[A,B,C]→Synthesizer | Independent subtasks, low latency |
| **Hierarchical** | Orchestrator→Subagents | Dynamic task decomposition |
| **Evaluator-Optimizer** | Gen→Eval→loop | Iterative quality refinement |

## API Reference

### Pipelines

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/pipelines/run` | Create and run a pipeline |
| GET | `/pipelines/{id}` | Get pipeline status |
| GET | `/pipelines/{id}/trace` | Get execution trace |
| GET | `/pipelines` | List recent runs |

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agents/register` | Register an agent |
| GET | `/agents` | List registered agents |
| GET | `/agents/{id}` | Get agent details |
| POST | `/agents/{id}/run` | Run a single agent |
| DELETE | `/agents/{id}` | Unregister an agent |

### Evals

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/evals/run` | Run an eval suite |
| POST | `/evals/suites` | Create an eval suite |
| GET | `/evals/suites` | List eval suites |
| POST | `/evals/suites/{name}/cases` | Add test case |
| GET | `/evals/metrics` | Get metrics summary |
| GET | `/evals/alerts` | Get budget alerts |

## Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up --build

# API: http://localhost:8000
# Dashboard: http://localhost:8501
# Docs: http://localhost:8000/docs
```

## Configuration

All configuration via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | — | OpenRouter API key (required) |
| `AGENTSFACTORY_ENV` | `development` | Environment name |
| `AGENTSFACTORY_LOG_LEVEL` | `INFO` | Logging level |
| `AGENTSFACTORY_DATABASE_URL` | `sqlite+aiosqlite:///./agentsfactory.db` | Database URL |

## Safety Features

- **Circuit Breakers**: Per-agent failure tracking with CLOSED→OPEN→HALF-OPEN state machine
- **Context Budgets**: Token budget enforcement per agent with automatic compression
- **Fallback Chains**: Primary → Fallback → Degraded → Human escalation
- **HITL Gates**: Configurable human-in-the-loop escalation points
- **Permission Matrix**: Least-privilege tool access per agent role
- **Budget Alerts**: Cost/token/latency threshold monitoring

## License

MIT

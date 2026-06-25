# Setup Guide — Ai Powered Lead Generation Team Multi Agent System

## Prerequisites

- Python 3.11+
- Docker (optional)
- Git

## Installation

```bash
git clone https://github.com/phanindraintelligenzit-afk/ai-powered-lead-generation-team-multi-agent-system.git
cd ai-powered-lead-generation-team-multi-agent-system
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run Tests

```bash
pytest tests/ -v
```

## Run Locally

```bash
uvicorn src.pipeline:app --reload
```

## Deploy with Docker

```bash
docker build -t ai-powered-lead-generation-team-multi-agent-system .
docker run -p 8000:8000 ai-powered-lead-generation-team-multi-agent-system
```

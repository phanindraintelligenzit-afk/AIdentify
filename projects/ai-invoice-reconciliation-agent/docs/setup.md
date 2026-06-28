# Setup Guide — Ai Invoice Reconciliation Agent

## Prerequisites

- Python 3.11+
- Docker (optional)
- Git

## Installation

```bash
git clone https://github.com/phanindraintelligenzit-afk/ai-invoice-reconciliation-agent.git
cd ai-invoice-reconciliation-agent
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
docker build -t ai-invoice-reconciliation-agent .
docker run -p 8000:8000 ai-invoice-reconciliation-agent
```

# Setup Guide — Ai Team That Finds Leads Decision Makers Writes Ou

## Prerequisites

- Python 3.11+
- Docker (optional)
- Git

## Installation

```bash
git clone https://github.com/phanindraintelligenzit-afk/ai-team-that-finds-leads-decision-makers-writes-ou.git
cd ai-team-that-finds-leads-decision-makers-writes-ou
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
docker build -t ai-team-that-finds-leads-decision-makers-writes-ou .
docker run -p 8000:8000 ai-team-that-finds-leads-decision-makers-writes-ou
```

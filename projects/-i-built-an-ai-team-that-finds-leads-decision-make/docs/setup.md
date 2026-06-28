# Setup Guide —  I Built An Ai Team That Finds Leads Decision Make

## Prerequisites

- Python 3.11+
- Docker (optional)
- Git

## Installation

```bash
git clone https://github.com/phanindraintelligenzit-afk/-i-built-an-ai-team-that-finds-leads-decision-make.git
cd -i-built-an-ai-team-that-finds-leads-decision-make
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
docker build -t -i-built-an-ai-team-that-finds-leads-decision-make .
docker run -p 8000:8000 -i-built-an-ai-team-that-finds-leads-decision-make
```

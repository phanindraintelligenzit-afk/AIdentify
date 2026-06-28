# Setup Guide — Ai Content Repurposer

## Prerequisites

- Python 3.11+
- Docker (optional)
- Git

## Installation

```bash
git clone https://github.com/phanindraintelligenzit-afk/ai-content-repurposer.git
cd ai-content-repurposer
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
docker build -t ai-content-repurposer .
docker run -p 8000:8000 ai-content-repurposer
```

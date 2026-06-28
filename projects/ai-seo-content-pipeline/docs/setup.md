# Setup Guide — Ai Seo Content Pipeline

## Prerequisites

- Python 3.11+
- Docker (optional)
- Git

## Installation

```bash
git clone https://github.com/phanindraintelligenzit-afk/ai-seo-content-pipeline.git
cd ai-seo-content-pipeline
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
docker build -t ai-seo-content-pipeline .
docker run -p 8000:8000 ai-seo-content-pipeline
```

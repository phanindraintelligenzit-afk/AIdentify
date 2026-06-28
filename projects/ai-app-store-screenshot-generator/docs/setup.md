# Setup Guide — Ai App Store Screenshot Generator

## Prerequisites

- Python 3.11+
- Docker (optional)
- Git

## Installation

```bash
git clone https://github.com/phanindraintelligenzit-afk/ai-app-store-screenshot-generator.git
cd ai-app-store-screenshot-generator
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
docker build -t ai-app-store-screenshot-generator .
docker run -p 8000:8000 ai-app-store-screenshot-generator
```

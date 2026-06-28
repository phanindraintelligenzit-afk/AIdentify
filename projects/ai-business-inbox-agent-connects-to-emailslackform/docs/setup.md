# Setup Guide — Ai Business Inbox Agent Connects To Emailslackform

## Prerequisites

- Python 3.11+
- Docker (optional)
- Git

## Installation

```bash
git clone https://github.com/phanindraintelligenzit-afk/ai-business-inbox-agent-connects-to-emailslackform.git
cd ai-business-inbox-agent-connects-to-emailslackform
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
docker build -t ai-business-inbox-agent-connects-to-emailslackform .
docker run -p 8000:8000 ai-business-inbox-agent-connects-to-emailslackform
```

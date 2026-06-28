# Setup Guide — Mcp Server For Google Ads Meta Ads Ga4

## Prerequisites

- Python 3.11+
- Docker (optional)
- Git

## Installation

```bash
git clone https://github.com/phanindraintelligenzit-afk/mcp-server-for-google-ads-meta-ads-ga4.git
cd mcp-server-for-google-ads-meta-ads-ga4
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
docker build -t mcp-server-for-google-ads-meta-ads-ga4 .
docker run -p 8000:8000 mcp-server-for-google-ads-meta-ads-ga4
```

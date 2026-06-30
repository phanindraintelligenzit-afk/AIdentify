# Setup Guide — Nanoeuler Gpt 2 Scale Model In Pure Ccuda From Scr

## Prerequisites

- Python 3.11+
- Docker (optional)
- Git

## Installation

```bash
git clone https://github.com/phanindraintelligenzit-afk/nanoeuler-gpt-2-scale-model-in-pure-ccuda-from-scr.git
cd nanoeuler-gpt-2-scale-model-in-pure-ccuda-from-scr
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
docker build -t nanoeuler-gpt-2-scale-model-in-pure-ccuda-from-scr .
docker run -p 8000:8000 nanoeuler-gpt-2-scale-model-in-pure-ccuda-from-scr
```

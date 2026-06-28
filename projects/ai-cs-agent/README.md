# AIdentify AI Customer Service Agent

An AI-powered customer service platform (Intercom Fin / Zendesk AI clone) for the AIdentify marketplace. Resolves tickets from a knowledge base using RAG, triages conversations by intent/sentiment/priority, and provides a self-serve support dashboard.

## Features

- **Knowledge Base RAG**: Loads FAQ, troubleshooting, and policy docs; retrieves relevant sections to answer customer questions with citations
- **Ticket Triage**: Classifies incoming messages by intent (billing, technical, account, how_to, sales, data_export), sentiment (positive/negative/neutral), and priority (low/medium/high)
- **AI Auto-Response**: Generates helpful answers using Ollama (local LLM) with retrieved KB context
- **Escalation Detection**: Automatically flags conversations needing human handoff (legal threats, urgent issues, very negative sentiment)
- **Simple Dashboard**: Web UI showing live chat, conversation history, triage analysis, and analytics

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Web UI      │────▶│  FastAPI     │────▶│  Ollama LLM │
│  Dashboard   │◀────│  Backend     │◀────│  (qwen2.5)  │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────▼───────┐     ┌─────────────┐
                    │  Agent       │────▶│  Knowledge  │
                    │  (triage +   │◀────│  Base (RAG) │
                    │   retrieve)  │     └─────────────┘
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  SQLite DB   │
                    │  (conversations│
                    │   + messages) │
                    └──────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) installed and running locally
- The `qwen2.5-coder:7b` model pulled (or set `OLLAMA_MODEL` env var)

### Setup

```bash
# Navigate to the project
cd projects/ai-cs-agent

# Create virtual environment (or use the marketplace venv)
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install fastapi uvicorn httpx jinja2

# Pull the Ollama model (if not already)
ollama pull qwen2.5-coder:7b
```

### Run

```bash
# Start the server
python main.py
```

The dashboard will be available at **http://localhost:8765**

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Model to use for responses |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web dashboard |
| `POST` | `/api/chat` | Send a customer message, get AI response |
| `GET` | `/api/conversations` | List all conversations |
| `GET` | `/api/conversations/{id}` | Get messages in a conversation |
| `POST` | `/api/conversations/{id}/resolve` | Mark conversation as resolved |
| `GET` | `/api/analytics` | Get dashboard analytics |
| `GET` | `/api/health` | Health check |

### Example API Usage

```bash
# Send a message
curl -X POST http://localhost:8765/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I reset my password?"}'

# Get analytics
curl http://localhost:8765/api/analytics
```

## Running Tests

```bash
# From the project directory
python -m pytest tests/ -v

# Or run directly
python tests/test_agent.py
```

## Knowledge Base

The knowledge base lives in the `kb/` directory as markdown files:
- `faq.md` — Frequently asked questions
- `troubleshooting.md` — Technical troubleshooting guide
- `policies.md` — Refund, acceptable use, data retention policies

Add or edit these files to update what the AI agent knows. The system automatically splits documents by `##` headings into searchable sections.

## How It Works

1. **Customer sends a message** via the dashboard or API
2. **Triage engine** classifies intent, sentiment, and priority
3. **RAG retrieval** finds the top-3 most relevant KB sections
4. **LLM generates** a response using the retrieved context
5. **Escalation check** determines if human handoff is needed
6. **Everything is stored** in SQLite for analytics and history

## Tech Stack

- **Backend**: FastAPI (Python)
- **LLM**: Ollama with qwen2.5-coder:7b (local, free)
- **Storage**: SQLite
- **Frontend**: Vanilla HTML/CSS/JS (no frameworks)
- **RAG**: Simple keyword-based retrieval (no vector DB needed for demo)

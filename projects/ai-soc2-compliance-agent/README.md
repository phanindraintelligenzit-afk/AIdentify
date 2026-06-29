# AI SOC2 Compliance Agent

> Open-source alternative to Vanta ($1-5K/mo) and Drata

Automate SOC2 evidence collection, control mapping, and audit preparation with AI.

## Features

- **Control Management** — Map SOC2 Trust Services Criteria (TSC) controls across all 5 categories: Security, Availability, Processing Integrity, Confidentiality, Privacy
- **Evidence Collection** — Automated and manual evidence collection (policies, screenshots, logs, configs, tickets, attestations)
- **Audit Management** — Track SOC2 Type I and Type II audits with progress tracking
- **Policy Management** — Create, version, and approve security policies
- **Integrations** — Connect AWS, GCP, GitHub, Okta, Jira, Slack for automated evidence
- **Background Worker** — Continuous evidence scanning with configurable intervals
- **REST API** — Full API for integrations (Slack, GRC tools, ticketing)

## Quick Start

```bash
# Clone
git clone https://github.com/phanindraintelligenzit-afk/ai-soc2-compliance-agent.git
cd ai-soc2-compliance-agent

# Run with Docker
docker-compose up -d

# Or run locally
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`
API docs at `http://localhost:8000/docs`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/controls` | List controls |
| POST | `/api/v1/controls` | Create control |
| GET | `/api/v1/controls/{id}` | Get control |
| PATCH | `/api/v1/controls/{id}` | Update control |
| DELETE | `/api/v1/controls/{id}` | Delete control |
| GET | `/api/v1/evidence` | List evidence |
| POST | `/api/v1/evidence` | Upload evidence |
| GET | `/api/v1/evidence/{id}` | Get evidence |
| PATCH | `/api/v1/evidence/{id}` | Update evidence |
| DELETE | `/api/v1/evidence/{id}` | Delete evidence |
| GET | `/api/v1/audits` | List audits |
| POST | `/api/v1/audits` | Create audit |
| GET | `/api/v1/audits/{id}` | Get audit |
| PATCH | `/api/v1/audits/{id}` | Update audit |
| POST | `/api/v1/audits/{id}/update-progress` | Update progress |
| DELETE | `/api/v1/audits/{id}` | Delete audit |
| GET | `/api/v1/policies` | List policies |
| POST | `/api/v1/policies` | Create policy |
| GET | `/api/v1/policies/{id}` | Get policy |
| PATCH | `/api/v1/policies/{id}` | Update policy |
| DELETE | `/api/v1/policies/{id}` | Delete policy |
| GET | `/api/v1/integrations` | List integrations |
| POST | `/api/v1/integrations` | Connect integration |
| PATCH | `/api/v1/integrations/{id}` | Update integration |
| DELETE | `/api/v1/integrations/{id}` | Disconnect integration |
| POST | `/api/v1/integrations/{id}/sync` | Trigger sync |

## Architecture

```
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes (controls, evidence, audits, policies, integrations)
│   │   ├── core/         # Config, database
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # AI evidence analysis engine
│   │   ├── workers/      # Background evidence scanner
│   │   └── main.py       # FastAPI app
│   ├── tests/            # pytest
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── docker-compose.yml
├── frontend/             # React + Vite dashboard
├── .github/workflows/    # CI
└── .gitignore
```

## SOC2 Trust Services Criteria (TSC) Categories

- **Security (CC)** — CC6.1, CC6.2, CC7.1, CC7.2, CC8.1, etc.
- **Availability (A)** — A1.1, A1.2, A1.3
- **Processing Integrity (PI)** — PI1.1, PI1.2, PI1.3, PI1.4, PI1.5
- **Confidentiality (C)** — C1.1, C1.2
- **Privacy (P)** — P1.0, P2.0, P3.0, P4.0, P5.0, P6.0, P7.0, P8.0

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./soc2_agent.db` | Database connection |
| `EVIDENCE_SCAN_INTERVAL_HOURS` | `24` | How often to scan for evidence |
| `MAX_EVIDENCE_PER_CONTROL` | `50` | Max evidence items per control |
| `LLM_API_KEY` | `` | API key for AI evidence analysis |
| `SLACK_WEBHOOK_URL` | `` | Slack notifications |
| `AWS_S3_BUCKET` | `` | S3 bucket for evidence storage |

## Testing

```bash
cd backend
pip install -e ".[dev]"
python -m pytest tests/ -v --noconftest
```

## Built By

Autonomously built and published by the [AIdentify](https://github.com/phanindraintelligenzit-afk/AIdentify) agent swarm.

Part of the [AIdentify Marketplace](https://phanindraintelligenzit-afk.github.io/AIdentify/) — open-source AI agents for business operations.

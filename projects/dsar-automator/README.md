# DataGuard DSAR Automator

Automate GDPR/CCPA Data Subject Access Request (DSAR) processing with AI-powered data discovery, identity verification, and response generation.

## Problem

Companies receiving Data Subject Access Requests (DSARs) from customers must respond within:
- **GDPR**: 30 days (EU)
- **CCPA**: 45 days (California)

Manual processing costs **$50-200/hour** and takes **2-5 hours per request**. With growing privacy regulations worldwide, DPOs and legal teams are overwhelmed.

## Solution

DataGuard DSAR Automator handles the entire DSAR workflow:

1. **Request Intake** — Auto-classify request type (access, erasure, rectification, portability, objection)
2. **Identity Verification** — Multi-method verification (email, account ownership, document)
3. **Data Discovery** — Scan connected systems (databases, CRMs, file storage, payment processors)
4. **Data Redaction** — Auto-redact third-party PII and sensitive data
5. **Response Generation** — Generate compliant response packages
6. **Deadline Tracking** — Automated reminders and escalation for approaching deadlines

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   React UI  │────▶│  FastAPI API │────▶│  Data Discovery │
│  (Dashboard)│◀────│   (Python)   │◀────│    Service      │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
                    ┌──────▼───────┐     ┌─────────────────┐
                    │  PostgreSQL  │     │  Task Queue     │
                    │  (Database)  │     │  (Redis/Celery) │
                    └──────────────┘     └─────────────────┘
```

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2
- **Frontend**: React 18, TypeScript, Tailwind CSS (dark theme), Recharts
- **Database**: PostgreSQL (SQLite for dev)
- **Task Queue**: Redis + Celery
- **Deployment**: Docker, docker-compose

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional)

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app/main.py
```

API runs at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

UI runs at `http://localhost:5173`

### Docker

```bash
cd backend
docker-compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /api/v1/dsar/ | Create DSAR request |
| GET | /api/v1/dsar/ | List DSAR requests |
| GET | /api/v1/dsar/{ref} | Get DSAR details |
| PATCH | /api/v1/dsar/{ref}/status | Update status |
| POST | /api/v1/dsar/{ref}/verify | Verify identity |
| POST | /api/v1/discovery/scan/{ref} | Run data discovery |
| GET | /api/v1/discovery/sources | List data sources |
| POST | /api/v1/responses/{ref} | Create response package |
| POST | /api/v1/responses/{ref}/approve | Approve response |
| GET | /api/v1/dashboard/stats | Dashboard statistics |

## Environment Variables

See `backend/.env.example` for all configuration options.

## Testing

```bash
cd backend
python -m pytest tests/ -v --noconftest
```

## Who Buys This

- **Data Protection Officers (DPOs)** at mid-market SaaS companies
- **Legal/Compliance teams** at companies with EU/CA customers
- **Privacy consultancies** managing DSARs for multiple clients
- **Startups** preparing for SOC2/GDPR compliance audits

## Pricing (SaaS)

- **Starter**: $500/mo — Up to 50 DSARs/month, 3 data sources
- **Growth**: $1,500/mo — Up to 200 DSARs/month, 10 data sources
- **Enterprise**: $3,000/mo — Unlimited DSARs, unlimited sources, SSO

## License

MIT

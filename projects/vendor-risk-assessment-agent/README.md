# 🛡️ Vendor Risk Assessment Agent

AI-powered third-party vendor risk assessment automation. Automate vendor due diligence, risk scoring, and continuous monitoring — replacing expensive GRC platforms at 80% lower cost.

## Problem

Mid-market companies (100-1000 employees) managing 50+ vendors spend:
- **10-20 hrs/week** sending security questionnaires
- **$15K-50K/year** on GRC platforms (OneTrust, Prevalent, BitSight)
- **3-4 weeks** to onboard a single vendor's risk review

This AI agent automates: vendor profiling → assessment distribution → response scoring → risk flagging → report generation.

## Who Buys This

| Segment | Companies | Current Spend | WTP |
|---------|-----------|--------------|-----|
| Mid-market SaaS | 100-1000 employees, 50+ vendors | $20-40K/yr GRC | $2,000-3,000/mo |
| Fintech startups | Compliance-heavy, 30+ vendors | $15-30K/yr manual + tools | $1,500-2,500/mo |
| Healthcare SaaS | HIPAA BAA management | $25-50K/yr manual | $2,000-4,000/mu |
| Managed service providers | Client vendor due diligence | $5-10K/vendor engagement | $1,500-3,000/mo |

## Features

- **Multi-template assessments**: Standard (15 questions), Quick (5 questions), Critical (18 questions)
- **AI risk scoring**: Weighted algorithm across 6 categories (Security, Compliance, Financial, Operational, Data Privacy, Business Continuity)
- **Automatic escalation**: Vendors scoring 75+ auto-flagged as high-risk
- **Finding management**: Track and resolve risk findings per vendor
- **Real-time dashboard**: Risk distribution, stats, vendor lineup
- **REST API**: Full API for integration with procurement systems
- **Critical vendor flagging**: Extra scrutiny for business-critical dependencies

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy async |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Frontend | React 18, Tailwind CSS, dark theme |
| Tests | pytest, httpx |
| Deploy | Docker, GitHub Actions CI |
| API Docs | Swagger UI at `/docs` |

## Quick Start

### Local Development

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[test]"
uvicorn app.main:app --reload  # → http://localhost:8000

# Frontend (just open index.html or serve)
cd frontend
python -m http.server 3000  # → http://localhost:3000
```

### Docker

```bash
cd backend
docker compose up --build  # → http://localhost:8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/api/vendors` | List vendors (filter by risk_level, category) |
| POST | `/api/vendors` | Create vendor |
| GET | `/api/vendors/{id}` | Get vendor details |
| PATCH | `/api/vendors/{id}` | Update vendor |
| DELETE | `/api/vendors/{id}` | Remove vendor |
| POST | `/api/vendors/{id}/findings` | Add risk finding |
| GET | `/api/vendors/{id}/findings` | List findings |
| GET | `/api/assessments/templates` | List assessment templates |
| GET | `/api/assessments/templates/{name}` | Get template questions |
| POST | `/api/assessments` | Create assessment |
| POST | `/api/assessments/{id}/send` | Mark as sent |
| POST | `/api/assessments/{id}/submit` | Submit responses & auto-score |
| GET | `/api/dashboard/stats` | Dashboard statistics |
| GET | `/api/dashboard/health` | Health check |

## Risk Scoring Algorithm

```
Score = (assessment_base + finding_penalties + critical_bonus)
- Assessment base: weighted average of category scores (inverted 1-5 → 0-100 risk)
- Finding penalties: critical=25, high=15, medium=8, low=3 (capped at 40)
- Critical vendor bonus: +10 for business-critical vendors
- Auto-critical: score >= 90 → critical level
```

## Assessment Templates

1. **Standard** — 5 categories, 15 questions. For regular vendor reviews.
2. **Quick** — 3 categories, 5 questions. For initial screening.
3. **Critical** — 6 categories, 18 questions. For business-critical vendors.

## Architecture

```
┌─────────────────────────────────────────┐
│           React Dashboard               │
│    (Risk overview, vendor management)   │
└─────────────────┬───────────────────────┘
                  │ REST API
┌─────────────────▼───────────────────────┐
│           FastAPI Backend               │
│  ┌──────────┬──────────┬──────────────┐ │
│  │ Vendors  │Assessment│  Dashboard   │ │
│  │  Router  │ Router   │   Router     │ │
│  └────┬─────┴────┬─────┴──────┬───────┘ │
│       │          │            │          │
│  ┌────▼──────────▼────────────▼───────┐ │
│  │        Risk Scoring Engine         │ │
│  │  (Weighted multi-category algo)    │ │
│  └────────────────┬───────────────────┘ │
│                   │                      │
│  ┌────────────────▼───────────────────┐ │
│  │     SQLAlchemy + SQLite/PG         │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Testing

```bash
cd backend
python -m pytest tests/ -v --noconftest
```

20+ tests covering: risk scoring, assessment processing, API endpoints, full workflow.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./vendor_risk.db` | Database connection |
| `HIGH_RISK_THRESHOLD` | 75 | Score threshold for high risk |
| `MEDIUM_RISK_THRESHOLD` | 45 | Score threshold for medium risk |
| `AUTO_ESCALATE_DAYS` | 14 | Days before auto-escalation |
| `DEBUG` | false | Enable debug mode |

## Roadmap

- [ ] Email integration (auto-send assessments)
- [ ] SOC 2 report parsing (upload PDF → auto-extract)
- [ ] Continuous monitoring (security rating APIs)
- [ ] Slack/Teams notifications
- [ ] Bulk vendor import (CSV)
- [ ] PDF report generation
- [ ] Multi-tenancy support

## License

MIT

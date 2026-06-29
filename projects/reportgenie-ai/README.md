# ReportGenie AI

**Automated multi-source report generation with AI-powered insights.**

Connect your data sources (Stripe, HubSpot, Google Analytics, Jira, CSV, PostgreSQL, MySQL) and generate executive reports with AI-driven insights and recommendations — in seconds, not days.

## Problem

Mid-market companies spend **$3,000-8,000/month** on:
- Manual analyst time pulling data from multiple tools
- BI tools (Looker, Tableau, Metabase) that still need human interpretation
- Weekly/monthly report creation that takes 2-3 days of staff time

## Solution

ReportGenie AI connects to your data sources, pulls metrics, and generates narrative reports with:
- **Revenue metrics** (MRR, ARR, churn, growth)
- **Sales pipeline** (leads, conversion, deal size)
- **Web analytics** (sessions, bounce rate, traffic sources)
- **Engineering metrics** (tickets, velocity, bugs)
- **AI-generated insights** and **actionable recommendations**

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (Dark Dashboard)                       │
│  - Connect data sources                          │
│  - Create & manage reports                       │
│  - View generated reports with insights          │
└──────────────────────┬──────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────┐
│  Backend (FastAPI + SQLAlchemy async)            │
│  - /api/data-sources  (CRUD)                     │
│  - /api/reports       (CRUD + generate)          │
│  - /api/generate      (AI report engine)         │
│  - /api/health        (status)                   │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  Report Generation Engine                        │
│  - Data connectors (Stripe, HubSpot, GA, Jira)   │
│  - Metric aggregation & formatting               │
│  - Insight generation (threshold-based rules)    │
│  - Recommendation engine                         │
└─────────────────────────────────────────────────┘
```

## Quick Start

### Option 1: Docker
```bash
cd backend
docker-compose up --build
# Frontend: http://localhost:3000
# API: http://localhost:8000/api
```

### Option 2: Local Python
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[test]"
uvicorn app.main:app --reload
# API: http://localhost:8000/api
```

### Option 3: Frontend only
```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check + stats |
| GET | `/api/templates` | List report templates |
| POST | `/api/data-sources` | Connect a data source |
| GET | `/api/data-sources` | List all sources |
| DELETE | `/api/data-sources/{id}` | Remove a source |
| POST | `/api/reports` | Create a report |
| GET | `/api/reports` | List all reports |
| GET | `/api/reports/{id}` | Get report details |
| PATCH | `/api/reports/{id}` | Update report |
| DELETE | `/api/reports/{id}` | Delete report |
| POST | `/api/generate` | Generate report content |
| GET | `/api/reports/{id}/content` | Get generated content |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./reportgenie.db` | Database connection |
| `DEBUG` | `true` | Enable debug mode |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |
| `REPORT_OUTPUT_DIR` | `./generated_reports` | Report output directory |

## Data Sources Supported

- **Stripe** — Revenue, MRR, ARR, churn metrics
- **HubSpot** — Leads, deals, conversion rates
- **Google Analytics** — Sessions, users, traffic sources
- **Jira** — Tickets, velocity, bug counts
- **CSV** — Generic file upload processing
- **PostgreSQL / MySQL** — Direct database queries
- **Generic API** — Any REST endpoint

## Testing

```bash
cd backend
python -m pytest tests/ -v
```

## License

MIT

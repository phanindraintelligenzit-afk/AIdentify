# CodeShield SAST

**AI-powered Static Application Security Testing — scan code for vulnerabilities in seconds.**

Open-source alternative to Snyk, Semgrep, and SonarQube for teams that want fast, pattern-based security scanning without the enterprise price tag.

## 🎯 Problem

- **Snyk** costs $100-500/mo per developer seat
- **Semgrep** enterprise starts at $5K/yr
- **SonarQube** requires dedicated infrastructure
- Most startups and small teams have ZERO automated security scanning

## ✅ Solution

CodeShield SAST provides 25+ security detection rules covering OWASP Top 10, runs in seconds, and costs nothing to self-host. Paste code or point it at a repo — get actionable findings with remediation guidance.

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Web UI      │────▶│  FastAPI     │────▶│  SAST Engine    │
│  (HTML/JS)   │     │  Backend     │     │  (25+ rules)    │
└─────────────┘     └──────────────┘     └─────────────────┘
                           │
                    ┌──────▼──────┐
                    │  SQLite DB  │
                    │  (async)    │
                    └─────────────┘
```

## 🚀 Quick Start

### Option 1: Docker (recommended)
```bash
docker-compose up -d
# Open http://localhost:8000
```

### Option 2: Local Python
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# Open http://localhost:8000
```

### Option 3: Run tests
```bash
cd backend
python -m pytest tests/ -v --noconftest
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/rules` | List all detection rules |
| POST | `/api/v1/scan/code` | Scan a code snippet |
| POST | `/api/v1/scan` | Scan a repository |
| GET | `/api/v1/scans` | List scan history |
| GET | `/api/v1/scans/{id}` | Get scan details + findings |
| GET | `/api/v1/scans/{id}/findings` | Get findings for a scan |
| GET | `/api/v1/dashboard` | Dashboard statistics |

### Example: Scan code via API
```bash
curl -X POST http://localhost:8000/api/v1/scan/code \
  -H "Content-Type: application/json" \
  -d '{"code": "eval(user_input)", "filename": "test.py"}'
```

## 🔍 Detection Rules (25+)

| Category | Rules | Severity |
|----------|-------|----------|
| Injection (SQL, CMD, SSTI) | CSAST-001 to CSAST-006, 090 | CRITICAL |
| Cryptographic Failures | CSAST-010 to CSAST-013 | HIGH |
| XSS | CSAST-020 to CSAST-021 | HIGH |
| Security Misconfiguration | CSAST-030 to CSAST-032 | MEDIUM |
| Vulnerable Components | CSAST-040 to CSAST-041 | MEDIUM |
| Auth Failures | CSAST-050 to CSAST-052 | CRITICAL/HIGH |
| SSRF / Path Traversal | CSAST-080 to CSAST-081 | HIGH |
| Sensitive Logging | CSAST-070 | MEDIUM |

## 📊 Risk Score

CodeShield calculates a 0-100 risk score per scan:
- **0-20**: Low risk — minor issues
- **20-40**: Medium — needs attention
- **40-70**: High — fix before production
- **70-100**: Critical — immediate action required

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: Vanilla HTML/JS (dark theme, no build step)
- **Deployment**: Docker, Docker Compose
- **CI**: GitHub Actions

## 📝 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./codeshield.db` | Database connection |
| `DEBUG` | `false` | Enable debug mode |
| `SECRET_KEY` | `dev-secret...` | App secret |
| `MAX_SCAN_DEPTH` | `50` | Max files per scan |

## 🤖 Agents Pipeline

This project was built by the AIdentify AI agent swarm:
1. **OWL** (Orchestrator) — selected the opportunity, designed architecture
2. **Builder Agent** — implemented backend, frontend, tests
3. **CI Agent** — configured Docker, GitHub Actions

## 📄 License

MIT

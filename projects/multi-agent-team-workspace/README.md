# Multi-Agent Team Workspace

> A workspace where tasks are assigned to humans OR AI agents — with shared context, handoff protocols, and audit trails. Think Linear/Asana for mixed human-agent teams.

## Features

- **Task CRUD** — Create, read, update, and delete tasks via REST API
- **Dual assignment** — Assign tasks to humans or AI agents
- **Shared context** — Tasks have a shared context document that both humans and agents can read and update
- **Handoff protocol** — Transfer tasks between agents and humans with reason logging and acceptance tracking
- **Audit trail** — Full record of who/what performed each action and when
- **Kanban dashboard** — Simple HTML dashboard with columns grouped by task status
- **Docker-ready** — Dockerfile and docker-compose.yml for easy deployment

## Architecture

```
multi-agent-team-workspace/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entrypoint
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── database.py          # Database engine, session, base
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── tasks.py         # Task CRUD endpoints
│   │   ├── context.py       # Shared context endpoints
│   │   ├── handoffs.py      # Handoff protocol endpoints
│   │   └── audit.py         # Audit trail query endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── task_service.py  # Business logic for tasks
│   │   ├── context_service.py
│   │   ├── handoff_service.py
│   │   └── audit_service.py
│   └── templates/
│       └── dashboard.html   # Kanban board dashboard
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_tasks.py
│   ├── test_context.py
│   ├── test_handoffs.py
│   └── test_audit.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
└── README.md
```

## Tech Stack

- **FastAPI** — Web framework
- **SQLAlchemy** — ORM with SQLite (dev) / PostgreSQL (prod)
- **Pydantic** — Data validation
- **Uvicorn** — ASGI server
- **Jinja2** — HTML templating

## Quick Start

```bash
# Clone and set up
cd multi-agent-team-workspace

# Option 1: Local development
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Option 2: Docker
docker-compose up --build
```

The API will be available at `http://localhost:8000`
The dashboard at `http://localhost:8000/dashboard`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tasks/` | Create a task |
| GET | `/api/tasks/` | List all tasks |
| GET | `/api/tasks/{id}` | Get a task |
| PUT | `/api/tasks/{id}` | Update a task |
| DELETE | `/api/tasks/{id}` | Delete a task |
| POST | `/api/tasks/{id}/assign` | Assign task to human/agent |
| POST | `/api/context/{task_id}` | Update task shared context |
| GET | `/api/context/{task_id}` | Get task shared context |
| POST | `/api/handoffs/` | Initiate a handoff |
| POST | `/api/handoffs/{id}/accept` | Accept a handoff |
| POST | `/api/handoffs/{id}/reject` | Reject a handoff |
| GET | `/api/audit/` | Get audit trail (filterable) |

## Task Statuses

- `backlog` — Not yet started
- `in_progress` — Actively being worked on
- `review` — Awaiting review/approval
- `done` — Completed
- `blocked` — Blocked by external factor

## Handoff Protocol

1. Current assignee initiates a handoff via `POST /api/handoffs/` with a target assignee and reason
2. Task enters `handoff_pending` state
3. Target assignee accepts or rejects the handoff
4. On acceptance: assignment transfers, task returns to `in_progress`
5. On rejection: task returns to original assignee with rejection reason logged
6. All steps are recorded in the audit trail

## Audit Trail

Every mutation action is recorded with:
- `actor` — Who performed it (human username or agent name)
- `action` — What was done (e.g., `task.created`, `handoff.accepted`)
- `entity_type` — The type of entity affected
- `entity_id` — The ID of the entity
- `timestamp` — When it happened
- `details` — JSON blob with additional context

## Running Tests

```bash
# Local
pytest tests/ -v --cov=app

# Docker
docker-compose exec api pytest tests/ -v --cov=app
```

## Production Notes

- Switch to PostgreSQL by setting `DATABASE_URL` environment variable
- Set `SECRET_KEY` for production
- Use a reverse proxy (nginx/traefik) in front of the API
- Consider adding authentication (OAuth2/JWT) for multi-user deployments

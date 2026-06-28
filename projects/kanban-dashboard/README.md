# AIdentify Kanban Dashboard

Production-ready Kanban board API server with a modern dark-themed frontend, built with FastAPI and WebSocket support for real-time updates.

## Features

- **Full CRUD** for boards, columns, and tasks
- **Agent Integration** - Assign tasks to researcher, writer, outreach, social, and owl agents
- **Task Management** - Statuses (backlog, in_progress, review, done), priorities, due dates, labels, and tags
- **Real-time Updates** - WebSocket-based live sync across clients
- **REST API** with JSON responses
- **API Key Authentication** - Simple header-based auth
- **Activity Log** - Full audit trail of task changes
- **Webhook Support** - HTTP callbacks for task events
- **Drag & Drop** - Modern Kanban board UI
- **Dark Theme** - Linear/Notion-inspired aesthetic
- **Responsive Design** - Works on desktop and mobile

## Quick Start

### Using Docker (Recommended)

```bash
docker-compose up --build
```

The dashboard will be available at `http://localhost:8000`

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m app.main
```

## API Documentation

Once running, visit:
- **Dashboard UI**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

## API Key Authentication

Include the API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: kanban-dev-key-2024" http://localhost:8000/api/boards
```

### Default API Keys

| Key | Role | Agent |
|-----|------|-------|
| `kanban-dev-key-2024` | admin | owl |
| `kanban-agent-researcher` | agent | researcher |
| `kanban-agent-writer` | agent | writer |
| `kanban-agent-outreach` | agent | outreach |
| `kanban-agent-social` | agent | social |

### Custom API Keys

Set via environment variable:
```bash
export KANBAN_API_KEYS="my-custom-key:admin,another-key:agent"
```

## API Endpoints

### Boards
- `GET /api/boards` - List all boards
- `GET /api/boards/{id}` - Get board details
- `POST /api/boards` - Create board (admin)
- `PATCH /api/boards/{id}` - Update board (admin)
- `DELETE /api/boards/{id}` - Delete board (admin)
- `GET /api/boards/{id}/stats` - Board statistics
- `POST /api/boards/{id}/columns` - Add column (admin)
- `PATCH /api/boards/{id}/columns/{col_id}` - Update column (admin)
- `DELETE /api/boards/{id}/columns/{col_id}` - Delete column (admin)

### Tasks
- `GET /api/tasks` - List tasks (with filters)
- `GET /api/tasks/{id}` - Get task details
- `POST /api/tasks` - Create task
- `PATCH /api/tasks/{id}` - Update task
- `DELETE /api/tasks/{id}` - Delete task
- `POST /api/tasks/{id}/move` - Move task to column
- `POST /api/tasks/bulk` - Bulk create tasks
- `PATCH /api/tasks/bulk` - Bulk update tasks
- `GET /api/tasks/{id}/activities` - Task activity log
- `GET /api/tasks/labels` - List labels
- `POST /api/tasks/labels` - Create label (admin)
- `GET /api/tasks/tags` - List tags
- `POST /api/tasks/tags` - Create tag (admin)

### Agents
- `GET /api/agents/tasks` - List agent's tasks
- `POST /api/agents/tasks` - Create task (agent context)
- `PATCH /api/agents/tasks/{id}` - Update task (agent context)
- `GET /api/agents/workload` - Agent workload summary
- `GET /api/agents/info` - Agent information
- `GET /api/agents/webhooks` - List webhooks (admin)
- `POST /api/agents/webhooks` - Register webhook (admin)
- `DELETE /api/agents/webhooks/{id}` - Delete webhook (admin)

## WebSocket

Connect to receive real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/1'); // Board-specific
// or
const ws = new WebSocket('ws://localhost:8000/ws'); // Global

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Update:', data);
};
```

### Message Types
- `task.created` - New task created
- `task.updated` - Task updated
- `task.deleted` - Task deleted
- `task_moved` - Task moved between columns
- `board_updated` - Board configuration changed
- `tasks_bulk_updated` - Bulk operation completed

## Webhooks

Register webhooks to receive HTTP callbacks on task events:

```bash
curl -X POST http://localhost:8000/api/agents/webhooks \
  -H "X-API-Key: kanban-dev-key-2024" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-server.com/webhook", "events": "task.created,task.updated"}'
```

## Agent Types

| Agent | Color | Icon | Description |
|-------|-------|------|-------------|
| Researcher | `#8b5cf6` | 🔬 | Research & analysis |
| Writer | `#ec4899` | ✍️ | Content creation |
| Outreach | `#f59e0b` | 📧 | Communications |
| Social | `#10b981` | 📱 | Social media |
| Owl | `#6366f1` | 🦉 | Default orchestrator |

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `PORT` | 8000 | Server port |
| `HOST` | 0.0.0.0 | Server host |
| `KANBAN_DATABASE_URL` | sqlite+aiosqlite:///./kanban.db | Database URL |
| `KANBAN_API_KEYS` | (built-in keys) | Comma-separated key:role pairs |

## Project Structure

```
kanban-dashboard/
├── app/
│   ├── main.py          # FastAPI application
│   ├── database.py      # Database configuration
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── auth.py          # API key authentication
│   ├── websocket.py     # WebSocket manager
│   ├── services.py      # Webhook service
│   ├── routers/
│   │   ├── boards.py    # Board endpoints
│   │   ├── tasks.py     # Task endpoints
│   │   └── agents.py    # Agent endpoints
│   └── static/
│       ├── index.html   # Dashboard UI
│       ├── style.css    # Styles
│       └── app.js       # Frontend logic
├── tests/               # Test suite
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker image
├── docker-compose.yml   # Docker Compose config
├── README.md           # This file
└── .gitignore
```

## Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## License

MIT

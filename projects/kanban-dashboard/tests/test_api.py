"""
Tests for Kanban Dashboard API.
"""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import init_db, close_db, async_session_factory, engine, Base


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def setup_db():
    """Create tables before each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    """Async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def admin_headers():
    return {"X-API-Key": "kanban-dev-key-2024"}


@pytest.fixture
def agent_headers():
    return {"X-API-Key": "kanban-agent-researcher"}


class TestHealth:
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    async def test_config(self, client: AsyncClient, admin_headers):
        response = await client.get("/api/config", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "statuses" in data
        assert "priorities" in data


class TestAuth:
    async def test_missing_api_key(self, client: AsyncClient):
        response = await client.get("/api/boards")
        assert response.status_code == 401

    async def test_invalid_api_key(self, client: AsyncClient):
        response = await client.get("/api/boards", headers={"X-API-Key": "invalid-key"})
        assert response.status_code == 403

    async def test_valid_api_key(self, client: AsyncClient, admin_headers):
        response = await client.get("/api/boards", headers=admin_headers)
        assert response.status_code == 200


class TestBoards:
    async def test_create_board(self, client: AsyncClient, admin_headers):
        response = await client.post(
            "/api/boards",
            headers=admin_headers,
            json={
                "name": "Test Board",
                "description": "A test board",
                "slug": "test-board",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Board"
        assert data["slug"] == "test-board"
        assert len(data["columns"]) == 4  # Default columns

    async def test_list_boards(self, client: AsyncClient, admin_headers):
        # Create a board first
        await client.post(
            "/api/boards",
            headers=admin_headers,
            json={"name": "Board 1", "slug": "board-1"},
        )
        response = await client.get("/api/boards", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_get_board(self, client: AsyncClient, admin_headers):
        create_resp = await client.post(
            "/api/boards",
            headers=admin_headers,
            json={"name": "Specific Board", "slug": "specific-board"},
        )
        board_id = create_resp.json()["id"]
        response = await client.get(f"/api/boards/{board_id}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["id"] == board_id

    async def test_update_board(self, client: AsyncClient, admin_headers):
        create_resp = await client.post(
            "/api/boards",
            headers=admin_headers,
            json={"name": "Old Name", "slug": "update-test"},
        )
        board_id = create_resp.json()["id"]
        response = await client.patch(
            f"/api/boards/{board_id}",
            headers=admin_headers,
            json={"name": "New Name"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    async def test_delete_board_requires_admin(self, client: AsyncClient, agent_headers):
        response = await client.delete("/api/boards/1", headers=agent_headers)
        assert response.status_code == 403

    async def test_board_stats(self, client: AsyncClient, admin_headers):
        create_resp = await client.post(
            "/api/boards",
            headers=admin_headers,
            json={"name": "Stats Board", "slug": "stats-board"},
        )
        board_id = create_resp.json()["id"]
        response = await client.get(f"/api/boards/{board_id}/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "by_status" in data
        assert "by_assignee" in data
        assert "by_priority" in data


class TestTasks:
    async def _create_board_and_get_column(self, client, headers):
        board_resp = await client.post(
            "/api/boards",
            headers=headers,
            json={"name": "Task Test Board", "slug": f"task-test-{__import__('uuid').uuid4().hex[:8]}"},
        )
        board_id = board_resp.json()["id"]
        column_id = board_resp.json()["columns"][0]["id"]
        return board_id, column_id

    async def test_create_task(self, client: AsyncClient, admin_headers):
        board_id, column_id = await self._create_board_and_get_column(client, admin_headers)
        response = await client.post(
            "/api/tasks",
            headers=admin_headers,
            json={
                "title": "Test Task",
                "description": "A test task",
                "board_id": board_id,
                "column_id": column_id,
                "priority": "high",
                "assignee": "researcher",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["priority"] == "high"
        assert data["assignee"] == "researcher"

    async def test_list_tasks(self, client: AsyncClient, admin_headers):
        response = await client.get("/api/tasks", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_update_task(self, client: AsyncClient, admin_headers):
        board_id, column_id = await self._create_board_and_get_column(client, admin_headers)
        create_resp = await client.post(
            "/api/tasks",
            headers=admin_headers,
            json={
                "title": "Update Me",
                "board_id": board_id,
                "column_id": column_id,
            },
        )
        task_id = create_resp.json()["id"]
        update_resp = await client.patch(
            f"/api/tasks/{task_id}",
            headers=admin_headers,
            json={"title": "Updated Title", "status": "in_progress"},
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "in_progress"

    async def test_delete_task(self, client: AsyncClient, admin_headers):
        board_id, column_id = await self._create_board_and_get_column(client, admin_headers)
        create_resp = await client.post(
            "/api/tasks",
            headers=admin_headers,
            json={
                "title": "Delete Me",
                "board_id": board_id,
                "column_id": column_id,
            },
        )
        task_id = create_resp.json()["id"]
        delete_resp = await client.delete(f"/api/tasks/{task_id}", headers=admin_headers)
        assert delete_resp.status_code == 204

    async def test_bulk_create_tasks(self, client: AsyncClient, admin_headers):
        board_id, column_id = await self._create_board_and_get_column(client, admin_headers)
        response = await client.post(
            "/api/tasks/bulk",
            headers=admin_headers,
            json={
                "tasks": [
                    {"title": "Bulk 1", "board_id": board_id, "column_id": column_id},
                    {"title": "Bulk 2", "board_id": board_id, "column_id": column_id},
                ],
            },
        )
        assert response.status_code == 201
        assert len(response.json()) == 2

    async def test_move_task(self, client: AsyncClient, admin_headers):
        board_id, column_id = await self._create_board_and_get_column(client, admin_headers)
        # Get second column
        board_resp = await client.get(f"/api/boards/{board_id}", headers=admin_headers)
        columns = board_resp.json()["columns"]
        if len(columns) >= 2:
            second_col_id = columns[1]["id"]
            task_resp = await client.post(
                "/api/tasks",
                headers=admin_headers,
                json={
                    "title": "Move Me",
                    "board_id": board_id,
                    "column_id": column_id,
                },
            )
            task_id = task_resp.json()["id"]
            move_resp = await client.post(
                f"/api/tasks/{task_id}/move",
                headers=admin_headers,
                json={"column_id": second_col_id, "position": 0},
            )
            assert move_resp.status_code == 200
            assert move_resp.json()["column_id"] == second_col_id


class TestLabels:
    async def test_create_label(self, client: AsyncClient, admin_headers):
        response = await client.post(
            "/api/tasks/labels",
            headers=admin_headers,
            json={"name": "bug", "color": "#ef4444"},
        )
        assert response.status_code == 201
        assert response.json()["name"] == "bug"

    async def test_list_labels(self, client: AsyncClient, admin_headers):
        response = await client.get("/api/tasks/labels", headers=admin_headers)
        assert response.status_code == 200


class TestTags:
    async def test_create_tag(self, client: AsyncClient, admin_headers):
        response = await client.post(
            "/api/tasks/tags",
            headers=admin_headers,
            json={"name": "frontend"},
        )
        assert response.status_code == 201
        assert response.json()["name"] == "frontend"

    async def test_list_tags(self, client: AsyncClient, admin_headers):
        response = await client.get("/api/tasks/tags", headers=admin_headers)
        assert response.status_code == 200


class TestAgentEndpoints:
    async def test_agent_info(self, client: AsyncClient, agent_headers):
        response = await client.get("/api/agents/info", headers=agent_headers)
        assert response.status_code == 200
        data = response.json()
        assert "agent" in data
        assert "details" in data

    async def test_agent_create_task(self, client: AsyncClient, agent_headers):
        # Create a board first
        board_resp = await client.post(
            "/api/boards",
            headers={"X-API-Key": "kanban-dev-key-2024"},
            json={"name": "Agent Board", "slug": f"agent-board-{__import__('uuid').uuid4().hex[:8]}"},
        )
        board_id = board_resp.json()["id"]

        response = await client.post(
            "/api/agents/tasks",
            headers=agent_headers,
            json={
                "title": "Agent Task",
                "description": "Created by agent",
                "priority": "medium",
                "board_id": board_id,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Agent Task"

    async def test_agent_workload(self, client: AsyncClient, agent_headers):
        response = await client.get("/api/agents/workload", headers=agent_headers)
        assert response.status_code == 200
        data = response.json()
        assert "agent" in data
        assert "workload" in data

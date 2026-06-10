"""API integration tests."""

import pytest
from httpx import AsyncClient, ASGITransport

from agentkit.api.app import app


@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.mark.asyncio
async def test_health(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "AgentsFactory"


@pytest.mark.asyncio
async def test_root(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "endpoints" in data


@pytest.mark.asyncio
async def test_list_pipelines_empty(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/pipelines/")
        assert resp.status_code == 200
        data = resp.json()
        assert "pipelines" in data


@pytest.mark.asyncio
async def test_list_agents_empty(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/agents/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_register_agent(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/agents/register", json={
            "agent_id": "test_researcher",
            "role": "researcher",
            "model": "openrouter/owl-alpha",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == "test_researcher"
        assert data["status"] == "registered"


@pytest.mark.asyncio
async def test_get_agent(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register first
        await client.post("/agents/register", json={
            "agent_id": "get_test_agent",
            "role": "analyzer",
        })
        # Get
        resp = await client.get("/agents/get_test_agent")
        assert resp.status_code == 200
        assert resp.json()["agent_id"] == "get_test_agent"


@pytest.mark.asyncio
async def test_get_agent_not_found(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/agents/nonexistent")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_agent(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register first
        await client.post("/agents/register", json={
            "agent_id": "delete_test_agent",
            "role": "writer",
        })
        # Delete
        resp = await client.delete("/agents/delete_test_agent")
        assert resp.status_code == 200
        assert resp.json()["status"] == "unregistered"


@pytest.mark.asyncio
async def test_run_pipeline_no_api_key(transport):
    """Pipeline run should fail without API key."""
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/pipelines/run", json={
            "input": "Test input",
            "topology": "sequential",
            "agents": [{"id": "r", "role": "researcher"}],
        })
        # Should get 401 (no API key) or 500 (no key configured)
        assert resp.status_code in (401, 500)


@pytest.mark.asyncio
async def test_run_pipeline_no_input(transport):
    """Pipeline run should fail without input."""
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/pipelines/run", json={
            "topology": "sequential",
        })
        assert resp.status_code in (400, 422)


@pytest.mark.asyncio
async def test_eval_suites(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/evals/suites")
        assert resp.status_code == 200
        data = resp.json()
        assert "suites" in data


@pytest.mark.asyncio
async def test_create_eval_suite(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/evals/suites?name=test_suite&baseline_score=0.7")
        assert resp.status_code == 200
        assert resp.json()["name"] == "test_suite"


@pytest.mark.asyncio
async def test_metrics(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/evals/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_runs" in data


@pytest.mark.asyncio
async def test_request_id_header(transport):
    """Every response should have X-Request-ID header."""
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert "x-request-id" in resp.headers
        assert "x-response-time-ms" in resp.headers


@pytest.mark.asyncio
async def test_custom_request_id(transport):
    """Custom X-Request-ID should be preserved."""
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health", headers={"X-Request-ID": "test-123"})
        assert resp.headers["x-request-id"] == "test-123"

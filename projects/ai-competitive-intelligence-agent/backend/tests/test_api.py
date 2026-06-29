"""Tests for the Competitive Intelligence Agent backend."""

import os
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

# Set test DB before importing app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_ci.db"

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from app.main import app
from core.database import init_db, close_db, engine
from core.database import Base


@pytest.fixture(autouse=True)
async def setup_db():
    """Create fresh tables before each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client(setup_db):
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_health_check(client):
    """Health endpoint returns ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai-competitive-intelligence-agent"


@pytest.mark.anyio
async def test_create_competitor(client):
    """Create a competitor."""
    payload = {
        "name": "Test Competitor Inc",
        "domain": "https://testcompetitor.example.com",
        "description": "A test competitor for unit tests",
        "industry": "SaaS",
        "employee_count": "50-200",
        "funding_stage": "Series B",
    }
    response = await client.post("/api/v1/competitors", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Competitor Inc"
    assert data["domain"] == "https://testcompetitor.example.com/"
    assert data["is_active"] is True
    assert data["monitor_website"] is True


@pytest.mark.anyio
async def test_list_competitors(client):
    """List competitors returns created items."""
    # Create one first
    await client.post("/api/v1/competitors", json={
        "name": "List Test Co",
        "domain": "https://listtest.example.com",
    })

    response = await client.get("/api/v1/competitors")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.anyio
async def test_get_competitor(client):
    """Get a specific competitor by ID."""
    create_resp = await client.post("/api/v1/competitors", json={
        "name": "Get Test Co",
        "domain": "https://gettest.example.com",
    })
    comp_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/competitors/{comp_id}")
    assert response.status_code == 200
    assert response.json()["id"] == comp_id


@pytest.mark.anyio
async def test_update_competitor(client):
    """Update competitor monitoring settings."""
    create_resp = await client.post("/api/v1/competitors", json={
        "name": "Update Test Co",
        "domain": "https://updatetest.example.com",
    })
    comp_id = create_resp.json()["id"]

    response = await client.patch(f"/api/v1/competitors/{comp_id}", json={
        "monitor_social": True,
        "monitor_jobs": False,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["monitor_social"] is True
    assert data["monitor_jobs"] is False


@pytest.mark.anyio
async def test_delete_competitor(client):
    """Delete a competitor."""
    create_resp = await client.post("/api/v1/competitors", json={
        "name": "Delete Test Co",
        "domain": "https://deletetest.example.com",
    })
    comp_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/competitors/{comp_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_resp = await client.get(f"/api/v1/competitors/{comp_id}")
    assert get_resp.status_code == 404


@pytest.mark.anyio
async def test_generate_battlecard(client):
    """Generate a battlecard for a competitor."""
    # Create competitor
    comp_resp = await client.post("/api/v1/competitors", json={
        "name": "Battlecard Test Co",
        "domain": "https://battlecardtest.example.com",
    })
    comp_id = comp_resp.json()["id"]

    # Generate battlecard
    response = await client.post("/api/v1/battlecards/generate", json={
        "competitor_id": comp_id,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["competitor_id"] == comp_id
    assert "Battlecard" in data["title"]
    assert len(data["strengths"]) > 0
    assert len(data["win_strategies"]) > 0
    assert data["generated_by"] == "ai"


@pytest.mark.anyio
async def test_publish_battlecard(client):
    """Publish a battlecard."""
    # Create competitor + battlecard
    comp_resp = await client.post("/api/v1/competitors", json={
        "name": "Publish Test Co",
        "domain": "https://publishtest.example.com",
    })
    comp_id = comp_resp.json()["id"]

    card_resp = await client.post("/api/v1/battlecards/generate", json={
        "competitor_id": comp_id,
    })
    card_id = card_resp.json()["id"]

    # Publish
    response = await client.post(f"/api/v1/battlecards/{card_id}/publish")
    assert response.status_code == 200
    assert response.json()["is_published"] is True
    assert response.json()["version"] == 2


@pytest.mark.anyio
async def test_generate_briefing(client):
    """Generate a competitive briefing."""
    response = await client.post("/api/v1/briefings/generate", json={
        "title": "Test Weekly Briefing",
        "period_days": 7,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Weekly Briefing"
    assert "summary" in data


@pytest.mark.anyio
async def test_signals_feed(client):
    """Signal feed endpoint works."""
    response = await client.get("/api/v1/signals/feed?hours=24")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "period_hours" in data


@pytest.mark.anyio
async def test_list_battlecards(client):
    """List battlecards endpoint."""
    response = await client.get("/api/v1/battlecards")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_list_briefings(client):
    """List briefings endpoint."""
    response = await client.get("/api/v1/briefings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

"""Tests for DSAR API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "dsar-automator"


@pytest.mark.anyio
async def test_create_dsar(client):
    payload = {
        "requester_name": "John Doe",
        "requester_email": "john@example.com",
        "request_type": "access",
        "regulation": "gdpr",
        "description": "I want to know what data you have on me.",
    }
    resp = await client.post("/api/v1/dsar/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["reference_number"].startswith("DSAR-")
    assert data["status"] == "received"
    assert data["days_remaining"] == 30
    assert data["risk_level"] == "low"


@pytest.mark.anyio
async def test_create_dsar_ccpa(client):
    payload = {
        "requester_name": "Jane Smith",
        "requester_email": "jane@example.com",
        "request_type": "erasure",
        "regulation": "ccpa",
        "description": "Delete all my personal data.",
    }
    resp = await client.post("/api/v1/dsar/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["days_remaining"] == 45


@pytest.mark.anyio
async def test_list_dsars(client):
    resp = await client.get("/api/v1/dsar/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.anyio
async def test_get_dsar_not_found(client):
    resp = await client.get("/api/v1/dsar/DSAR-99999999-9999")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_dashboard_stats(client):
    resp = await client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_requests" in data
    assert "pending_requests" in data
    assert "compliance_rate" in data


@pytest.mark.anyio
async def test_discovery_sources(client):
    resp = await client.get("/api/v1/discovery/sources")
    assert resp.status_code == 200
    data = resp.json()
    assert "sources" in data
    assert len(data["sources"]) == 6


@pytest.mark.anyio
async def test_discovery_scan(client):
    resp = await client.post("/api/v1/discovery/scan/DSAR-20260628-0001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["systems_scanned"] == 5
    assert data["total_records"] == 577


@pytest.mark.anyio
async def test_response_package(client):
    payload = {"included_data": ["personal_info", "transactions"], "format": "json"}
    resp = await client.post("/api/v1/responses/DSAR-20260628-0001", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["approved_by"] is None
    assert data["redactions_count"] == 3

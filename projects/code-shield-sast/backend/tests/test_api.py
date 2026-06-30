"""Tests for API endpoints."""
import os
import sys
import pytest
from pathlib import Path

# Set test DB BEFORE importing app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_codeshield.db"

sys.path.insert(0, str(Path(__file__).parent.parent))

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import engine, Base


@pytest.fixture(autouse=True)
async def setup_db():
    """Create fresh tables before each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(setup_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    
    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_health_has_uptime(self, client):
        response = await client.get("/api/v1/health")
        data = response.json()
        assert "uptime_seconds" in data


class TestRulesEndpoint:
    
    @pytest.mark.asyncio
    async def test_list_rules(self, client):
        response = await client.get("/api/v1/rules")
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert data["total"] > 0
    
    @pytest.mark.asyncio
    async def test_rules_have_required_fields(self, client):
        response = await client.get("/api/v1/rules")
        data = response.json()
        for rule in data["rules"]:
            assert "rule_id" in rule
            assert "name" in rule
            assert "severity" in rule


class TestScanCodeEndpoint:
    
    @pytest.mark.asyncio
    async def test_scan_clean_code(self, client):
        response = await client.post("/api/v1/scan/code", json={
            "code": "def hello(): return 'world'",
            "filename": "test.py"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["total_findings"] == 0
    
    @pytest.mark.asyncio
    async def test_scan_vulnerable_code(self, client):
        response = await client.post("/api/v1/scan/code", json={
            "code": "eval(user_input)\napi_key = 'sk_liv...cdef'",
            "filename": "vuln.py"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["total_findings"] > 0
    
    @pytest.mark.asyncio
    async def test_scan_empty_code_returns_400(self, client):
        response = await client.post("/api/v1/scan/code", json={
            "code": "",
            "filename": "empty.py"
        })
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_scan_returns_risk_score(self, client):
        response = await client.post("/api/v1/scan/code", json={
            "code": "eval(user_input)\nos.system('cmd ' + user_input)",
            "filename": "danger.py"
        })
        data = response.json()
        assert "risk_score" in data
        assert data["risk_score"] > 0


class TestScansListEndpoint:
    
    @pytest.mark.asyncio
    async def test_list_scans_empty(self, client):
        response = await client.get("/api/v1/scans")
        assert response.status_code == 200
        assert response.json() == []
    
    @pytest.mark.asyncio
    async def test_list_scans_after_creating(self, client):
        # Create a scan first
        await client.post("/api/v1/scan/code", json={
            "code": "x = 1",
            "filename": "simple.py"
        })
        response = await client.get("/api/v1/scans")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestScanDetailEndpoint:
    
    @pytest.mark.asyncio
    async def test_get_scan_detail(self, client):
        # Create a scan
        create_resp = await client.post("/api/v1/scan/code", json={
            "code": "eval(input)",
            "filename": "test.py"
        })
        scan_id = create_resp.json()["id"]
        
        # Get detail
        response = await client.get(f"/api/v1/scans/{scan_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == scan_id
        assert "findings" in data
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_scan(self, client):
        response = await client.get("/api/v1/scans/99999")
        assert response.status_code == 404


class TestDashboardEndpoint:
    
    @pytest.mark.asyncio
    async def test_dashboard_stats(self, client):
        # Create a scan first
        await client.post("/api/v1/scan/code", json={
            "code": "eval(input)",
            "filename": "test.py"
        })
        
        response = await client.get("/api/v1/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_scans" in data
        assert "total_findings" in data
        assert "severity_distribution" in data
        assert data["total_scans"] >= 1

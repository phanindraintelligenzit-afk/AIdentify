"""Tests for the AI SOC2 Compliance Agent backend."""

import os
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

# Set test DB before importing app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_soc2.db"

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


# ── Health Tests ──

@pytest.mark.anyio
async def test_health_check(client):
    """Health endpoint returns ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai-soc2-compliance-agent"
    assert data["version"] == "1.0.0"


# ── Control Tests ──

@pytest.mark.anyio
async def test_create_control(client):
    """Create a compliance control."""
    payload = {
        "control_id": "CC6.1",
        "name": "Logical and Physical Access Controls",
        "description": "Implement logical and physical access controls",
        "category": "Security",
        "subcategory": "Access Control",
        "tsc_criterion": "CC6.1",
        "status": "not_started",
        "assignee": "security@example.com",
        "notes": "Initial control setup",
    }
    response = await client.post("/api/v1/controls", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["control_id"] == "CC6.1"
    assert data["name"] == "Logical and Physical Access Controls"
    assert data["category"] == "Security"
    assert data["status"] == "not_started"
    assert data["is_active"] is True


@pytest.mark.anyio
async def test_list_controls(client):
    """List controls returns created items."""
    await client.post("/api/v1/controls", json={
        "control_id": "CC7.1",
        "name": "System Monitoring",
        "category": "Security",
        "tsc_criterion": "CC7.1",
    })

    response = await client.get("/api/v1/controls")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.anyio
async def test_get_control(client):
    """Get a specific control by ID."""
    create_resp = await client.post("/api/v1/controls", json={
        "control_id": "CC7.2",
        "name": "Incident Response",
        "category": "Security",
        "tsc_criterion": "CC7.2",
    })
    control_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/controls/{control_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == control_id
    assert data["control_id"] == "CC7.2"


@pytest.mark.anyio
async def test_update_control(client):
    """Update a control's status and assignee."""
    create_resp = await client.post("/api/v1/controls", json={
        "control_id": "CC8.1",
        "name": "Change Management",
        "category": "Security",
        "tsc_criterion": "CC8.1",
    })
    control_id = create_resp.json()["id"]

    response = await client.patch(f"/api/v1/controls/{control_id}", json={
        "status": "in_progress",
        "assignee": "devops@example.com",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["assignee"] == "devops@example.com"


@pytest.mark.anyio
async def test_delete_control(client):
    """Delete a control."""
    create_resp = await client.post("/api/v1/controls", json={
        "control_id": "CC9.1",
        "name": "Risk Assessment",
        "category": "Security",
        "tsc_criterion": "CC9.1",
    })
    control_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/controls/{control_id}")
    assert response.status_code == 204

    get_resp = await client.get(f"/api/v1/controls/{control_id}")
    assert get_resp.status_code == 404


# ── Evidence Tests ──

@pytest.mark.anyio
async def test_create_evidence_for_control(client):
    """Attach evidence to a control."""
    control_resp = await client.post("/api/v1/controls", json={
        "control_id": "CC6.2",
        "name": "MFA Enforcement",
        "category": "Security",
        "tsc_criterion": "CC6.2",
    })
    control_id = control_resp.json()["id"]

    payload = {
        "control_id": control_id,
        "evidence_type": "policy",
        "title": "MFA Policy Document",
        "description": "Company-wide MFA enforcement policy",
        "source": "Internal",
        "collected_by": "manual",
        "is_valid": True,
    }
    response = await client.post("/api/v1/evidence", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "MFA Policy Document"
    assert data["evidence_type"] == "policy"
    assert data["control_id"] == control_id
    assert data["is_valid"] is True


@pytest.mark.anyio
async def test_list_evidence_for_control(client):
    """List evidence filtered by control."""
    control_resp = await client.post("/api/v1/controls", json={
        "control_id": "CC6.3",
        "name": "Access Reviews",
        "category": "Security",
        "tsc_criterion": "CC6.3",
    })
    control_id = control_resp.json()["id"]

    await client.post("/api/v1/evidence", json={
        "control_id": control_id,
        "evidence_type": "screenshot",
        "title": "Access Review Screenshot",
        "source": "Okta",
    })

    response = await client.get(f"/api/v1/evidence?control_id={control_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["items"][0]["control_id"] == control_id


# ── Audit Tests ──

@pytest.mark.anyio
async def test_create_audit(client):
    """Create a SOC2 audit engagement."""
    payload = {
        "name": "SOC2 Type II 2026 Audit",
        "audit_type": "SOC2 Type II",
        "status": "preparation",
        "auditor_name": "Acme Audit Partners",
        "auditor_contact": "auditor@acme-audit.com",
        "completion_percentage": 10.0,
        "notes": "Initial preparation phase",
    }
    response = await client.post("/api/v1/audits", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "SOC2 Type II 2026 Audit"
    assert data["audit_type"] == "SOC2 Type II"
    assert data["status"] == "preparation"
    assert data["auditor_name"] == "Acme Audit Partners"
    assert data["completion_percentage"] == 10.0


@pytest.mark.anyio
async def test_list_audits(client):
    """List all audits."""
    await client.post("/api/v1/audits", json={
        "name": "SOC2 Type I Q1 2026",
        "audit_type": "SOC2 Type I",
    })

    response = await client.get("/api/v1/audits")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.anyio
async def test_update_audit_progress(client):
    """Update audit completion progress."""
    create_resp = await client.post("/api/v1/audits", json={
        "name": "SOC2 Type II Progress Test",
        "audit_type": "SOC2 Type II",
        "status": "evidence_collection",
        "completion_percentage": 25.0,
    })
    audit_id = create_resp.json()["id"]

    response = await client.patch(f"/api/v1/audits/{audit_id}", json={
        "completion_percentage": 50.0,
        "notes": "Evidence collection halfway complete",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["completion_percentage"] == 50.0
    assert data["notes"] == "Evidence collection halfway complete"


# ── Policy Tests ──

@pytest.mark.anyio
async def test_create_policy(client):
    """Create a security policy."""
    payload = {
        "name": "Information Security Policy",
        "policy_type": "security",
        "version": "2.0",
        "content": "# Information Security Policy\n\nAll employees must...",
        "status": "draft",
        "owner": "CISO",
    }
    response = await client.post("/api/v1/policies", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Information Security Policy"
    assert data["policy_type"] == "security"
    assert data["version"] == "2.0"
    assert data["status"] == "draft"
    assert data["owner"] == "CISO"


@pytest.mark.anyio
async def test_list_policies(client):
    """List all policies."""
    await client.post("/api/v1/policies", json={
        "name": "Acceptable Use Policy",
        "policy_type": "acceptable_use",
        "status": "approved",
        "owner": "IT",
    })

    response = await client.get("/api/v1/policies")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.anyio
async def test_get_policy(client):
    """Get a specific policy."""
    create_resp = await client.post("/api/v1/policies", json={
        "name": "Data Retention Policy",
        "policy_type": "data_retention",
        "version": "1.0",
    })
    policy_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/policies/{policy_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == policy_id
    assert data["name"] == "Data Retention Policy"


# ── Integration Tests ──

@pytest.mark.anyio
async def test_list_integrations(client):
    """List integrations endpoint."""
    response = await client.get("/api/v1/integrations")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)

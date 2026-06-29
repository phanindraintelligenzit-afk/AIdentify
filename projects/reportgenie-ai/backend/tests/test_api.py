"""Tests for ReportGenie AI backend."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.core.database import Base, get_db

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_reportgenie.db"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with test_session_maker() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data


@pytest.mark.anyio
async def test_list_templates():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert "templates" in data
        assert len(data["templates"]) >= 3


@pytest.mark.anyio
async def test_create_data_source():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "name": "Test Stripe Account",
            "source_type": "stripe",
            "config": {"api_key": "sk_test_xxx", "days": 30}
        }
        resp = await client.post("/api/data-sources", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Stripe Account"
        assert data["source_type"] == "stripe"
        assert data["status"] == "active"
        assert "id" in data


@pytest.mark.anyio
async def test_list_data_sources():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create one first
        await client.post("/api/data-sources", json={
            "name": "HubSpot Prod", "source_type": "hubspot", "config": {}
        })
        resp = await client.get("/api/data-sources")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1


@pytest.mark.anyio
async def test_create_report():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create data sources first
        ds1 = await client.post("/api/data-sources", json={
            "name": "Stripe", "source_type": "stripe", "config": {}
        })
        ds2 = await client.post("/api/data-sources", json={
            "name": "GA4", "source_type": "ganalytics", "config": {}
        })
        ds1_id = ds1.json()["id"]
        ds2_id = ds2.json()["id"]

        payload = {
            "title": "Q2 Executive Report",
            "description": "Quarterly business review",
            "template_type": "executive_summary",
            "data_source_ids": [ds1_id, ds2_id],
            "output_format": "html"
        }
        resp = await client.post("/api/reports", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Q2 Executive Report"
        assert data["status"] == "draft"
        assert len(data["data_sources"]) == 2


@pytest.mark.anyio
async def test_generate_report():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Setup: create DS + report
        ds = await client.post("/api/data-sources", json={
            "name": "Jira Board", "source_type": "jira", "config": {}
        })
        ds_id = ds.json()["id"]

        report = await client.post("/api/reports", json={
            "title": "Weekly Engineering Report",
            "template_type": "engineering_metrics",
            "data_source_ids": [ds_id],
        })
        report_id = report.json()["id"]

        # Generate
        resp = await client.post("/api/generate", json={"report_id": report_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["generated_content"] is not None
        assert "Engineering" in data["generated_content"]


@pytest.mark.anyio
async def test_get_report_content():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Setup
        ds = await client.post("/api/data-sources", json={
            "name": "Stripe", "source_type": "stripe", "config": {}
        })
        report = await client.post("/api/reports", json={
            "title": "Revenue Report",
            "data_source_ids": [ds.json()["id"]],
        })
        report_id = report.json()["id"]
        await client.post("/api/generate", json={"report_id": report_id})

        # Get content
        resp = await client.get(f"/api/reports/{report_id}/content")
        assert resp.status_code == 200
        data = resp.json()
        assert "content" in data
        assert data["format"] == "html"


@pytest.mark.anyio
async def test_delete_data_source():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        ds = await client.post("/api/data-sources", json={
            "name": "Temp Source", "source_type": "csv", "config": {}
        })
        ds_id = ds.json()["id"]
        resp = await client.delete(f"/api/data-sources/{ds_id}")
        assert resp.status_code == 204


@pytest.mark.anyio
async def test_report_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/reports/99999")
        assert resp.status_code == 404


@pytest.mark.anyio
async def test_invalid_source_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"name": "Bad", "source_type": "invalid_type", "config": {}}
        resp = await client.post("/api/data-sources", json=payload)
        assert resp.status_code == 422  # Validation error

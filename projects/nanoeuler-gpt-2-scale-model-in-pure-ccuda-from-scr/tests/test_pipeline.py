"""Integration test for the full pipeline."""
import pytest
from src.pipeline import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200

def test_pipeline_end_to_end():
    """Test the full pipeline: agent_1, agent_2, agent_3."""
    response = client.post("/run", json={"input": "test"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "complete"

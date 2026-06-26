"""Tests for shared context endpoints."""

import pytest


class TestContext:
    def test_get_context(self, client):
        create_resp = client.post("/api/tasks/", json={"title": "Context test", "created_by": "tester"})
        task_id = create_resp.json()["id"]

        response = client.get(f"/api/context/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["context"] == ""

    def test_update_context(self, client):
        create_resp = client.post("/api/tasks/", json={"title": "Context update", "created_by": "tester"})
        task_id = create_resp.json()["id"]

        context_text = "This is important context shared with all assignees."

        response = client.post(f"/api/context/{task_id}", json={
            "content": context_text,
            "updated_by": "alice"
        })
        assert response.status_code == 200
        assert response.json()["context"] == context_text

        # Verify persistence
        get_resp = client.get(f"/api/context/{task_id}")
        assert get_resp.json()["context"] == context_text

    def test_update_context_nonexistent_task(self, client):
        response = client.post("/api/context/9999", json={
            "content": "Won't work",
            "updated_by": "tester"
        })
        assert response.status_code == 404

    def test_get_context_nonexistent_task(self, client):
        response = client.get("/api/context/9999")
        assert response.status_code == 404

    def test_context_persists_across_updates(self, client):
        create_resp = client.post("/api/tasks/", json={"title": "Persist test", "created_by": "tester"})
        task_id = create_resp.json()["id"]

        # Update context
        client.post(f"/api/context/{task_id}", json={
            "content": "Version 1",
            "updated_by": "alice"
        })

        # Update again
        client.post(f"/api/context/{task_id}", json={
            "content": "Version 2",
            "updated_by": "gpt-4"
        })

        # Check final state
        resp = client.get(f"/api/context/{task_id}")
        assert resp.json()["context"] == "Version 2"

"""Tests for task CRUD endpoints."""

import pytest


class TestTaskCRUD:
    def test_create_task(self, client):
        response = client.post("/api/tasks/", json={
            "title": "Test task",
            "description": "A test task",
            "priority": 1,
            "created_by": "tester"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test task"
        assert data["description"] == "A test task"
        assert data["priority"] == 1
        assert data["status"] == "backlog"
        assert data["created_by"] == "tester"
        assert "id" in data

    def test_create_task_no_title_fails(self, client):
        response = client.post("/api/tasks/", json={
            "description": "No title",
            "priority": 0
        })
        assert response.status_code == 422

    def test_get_task(self, client):
        # Create a task first
        create_resp = client.post("/api/tasks/", json={
            "title": "Get test",
            "created_by": "tester"
        })
        task_id = create_resp.json()["id"]

        # Get it
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["id"] == task_id
        assert response.json()["title"] == "Get test"

    def test_get_nonexistent_task(self, client):
        response = client.get("/api/tasks/9999")
        assert response.status_code == 404

    def test_list_tasks(self, client):
        # Create multiple tasks
        client.post("/api/tasks/", json={"title": "Task 1", "created_by": "tester"})
        client.post("/api/tasks/", json={"title": "Task 2", "created_by": "tester"})

        response = client.get("/api/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert len(data["tasks"]) >= 2

    def test_list_tasks_filter_by_status(self, client):
        client.post("/api/tasks/", json={"title": "Filtered task", "created_by": "tester"})
        response = client.get("/api/tasks/?status=backlog")
        assert response.status_code == 200
        tasks = response.json()["tasks"]
        assert all(t["status"] == "backlog" for t in tasks)

    def test_update_task(self, client):
        create_resp = client.post("/api/tasks/", json={"title": "Update me", "created_by": "tester"})
        task_id = create_resp.json()["id"]

        response = client.put(f"/api/tasks/{task_id}", json={
            "title": "Updated title",
            "status": "in_progress",
            "actor": "tester"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated title"
        assert data["status"] == "in_progress"

    def test_update_nonexistent_task(self, client):
        response = client.put("/api/tasks/9999", json={"title": "Nope"})
        assert response.status_code == 404

    def test_delete_task(self, client):
        create_resp = client.post("/api/tasks/", json={"title": "Delete me", "created_by": "tester"})
        task_id = create_resp.json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 204

        # Verify it's deleted
        get_resp = client.get(f"/api/tasks/{task_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_task(self, client):
        response = client.delete("/api/tasks/9999")
        assert response.status_code == 404


class TestTaskAssignment:
    def test_assign_to_human(self, client):
        create_resp = client.post("/api/tasks/", json={"title": "Assign me", "created_by": "tester"})
        task_id = create_resp.json()["id"]

        response = client.post(f"/api/tasks/{task_id}/assign", json={
            "assignee_name": "alice",
            "assignee_type": "human"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["assignee_name"] == "alice"
        assert data["assignee_type"] == "human"
        assert data["status"] == "in_progress"

    def test_assign_to_agent(self, client):
        create_resp = client.post("/api/tasks/", json={"title": "Agent task", "created_by": "tester"})
        task_id = create_resp.json()["id"]

        response = client.post(f"/api/tasks/{task_id}/assign", json={
            "assignee_name": "gpt-4",
            "assignee_type": "agent"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["assignee_name"] == "gpt-4"
        assert data["assignee_type"] == "agent"

    def test_assign_nonexistent_task(self, client):
        response = client.post("/api/tasks/9999/assign", json={
            "assignee_name": "alice",
            "assignee_type": "human"
        })
        assert response.status_code == 404

    def test_assign_invalid_type(self, client):
        create_resp = client.post("/api/tasks/", json={"title": "Test", "created_by": "tester"})
        task_id = create_resp.json()["id"]

        response = client.post(f"/api/tasks/{task_id}/assign", json={
            "assignee_name": "alice",
            "assignee_type": "robot"
        })
        assert response.status_code == 422


class TestHealthCheck:
    def test_health(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "docs" in response.json()

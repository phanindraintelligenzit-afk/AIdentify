"""Tests for audit trail endpoints."""

import pytest


class TestAuditTrail:
    def _create_assigned_task(self, client, title="Audit task"):
        """Helper to create and assign a task."""
        create_resp = client.post("/api/tasks/", json={
            "title": title,
            "created_by": "tester"
        })
        task_id = create_resp.json()["id"]

        client.post(f"/api/tasks/{task_id}/assign", json={
            "assignee_name": "alice",
            "assignee_type": "human"
        })
        return task_id

    def test_audit_trail_exists_after_create(self, client):
        create_resp = client.post("/api/tasks/", json={
            "title": "Audited task",
            "created_by": "tester"
        })
        task_id = create_resp.json()["id"]

        response = client.get("/api/audit/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

        # Check that the creation audit entry exists
        task_entries = [e for e in data["entries"] if e["task_id"] == task_id]
        creation_entries = [e for e in task_entries if e["action"] == "task.created"]
        assert len(creation_entries) >= 1
        assert creation_entries[0]["actor"] == "tester"

    def test_audit_trail_after_assignment(self, client):
        task_id = self._create_assigned_task(client)

        response = client.get("/api/audit/")
        entries = response.json()["entries"]
        task_entries = [e for e in entries if e["task_id"] == task_id]
        assign_entries = [e for e in task_entries if e["action"] == "task.assigned"]
        assert len(assign_entries) >= 1

    def test_audit_trail_filter_by_task(self, client):
        task_id = self._create_assigned_task(client, "Filtered audit")

        response = client.get(f"/api/audit/?task_id={task_id}")
        assert response.status_code == 200
        data = response.json()
        assert all(e["task_id"] == task_id for e in data["entries"])

    def test_audit_trail_filter_by_action(self, client):
        response = client.get("/api/audit/?action=task.created")
        assert response.status_code == 200
        entries = response.json()["entries"]
        assert all(e["action"] == "task.created" for e in entries)

    def test_audit_trail_after_handoff(self, client):
        task_id = self._create_assigned_task(client)

        # Initiate handoff
        client.post(f"/api/handoffs/?actor=alice", json={
            "task_id": task_id,
            "to_assignee": "bob",
            "reason": "Transfer"
        })

        response = client.get("/api/audit/")
        entries = response.json()["entries"]
        handoff_entries = [e for e in entries if e["action"] == "handoff.initiated" and e["task_id"] == task_id]
        assert len(handoff_entries) >= 1

    def test_audit_trail_pagination(self, client):
        response = client.get("/api/audit/?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) <= 5

    def test_audit_nonempty_total(self, client):
        # Generate some activity
        client.post("/api/tasks/", json={"title": "Audit test", "created_by": "tester"})
        client.post("/api/tasks/", json={"title": "Audit test 2", "created_by": "tester"})

        response = client.get("/api/audit/")
        assert response.json()["total"] >= 2

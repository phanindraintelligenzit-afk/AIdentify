"""Tests for handoff protocol endpoints."""

import pytest


class TestHandoff:
    def _create_assigned_task(self, client, title="Handoff task"):
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

    def test_initiate_handoff(self, client):
        task_id = self._create_assigned_task(client)

        response = client.post(f"/api/handoffs/?actor=alice", json={
            "task_id": task_id,
            "to_assignee": "gpt-4",
            "reason": "Needs AI processing"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["task_id"] == task_id
        assert data["from_assignee"] == "alice"
        assert data["to_assignee"] == "gpt-4"
        assert data["reason"] == "Needs AI processing"
        assert data["status"] == "pending"

        # Verify task is now handoff_pending
        task_resp = client.get(f"/api/tasks/{task_id}")
        assert task_resp.json()["status"] == "handoff_pending"

    def test_accept_handoff(self, client):
        task_id = self._create_assigned_task(client)

        # Initiate
        handoff_resp = client.post(f"/api/handoffs/?actor=alice", json={
            "task_id": task_id,
            "to_assignee": "gpt-4",
            "reason": "Transfer to AI"
        })
        handoff_id = handoff_resp.json()["id"]

        # Accept
        accept_resp = client.post(f"/api/handoffs/{handoff_id}/accept", json={
            "accepted_by": "gpt-4"
        })
        assert accept_resp.status_code == 200
        data = accept_resp.json()
        assert data["status"] == "accepted"

        # Verify task now assigned to new assignee
        task_resp = client.get(f"/api/tasks/{task_id}")
        assert task_resp.json()["assignee_name"] == "gpt-4"
        assert task_resp.json()["status"] == "in_progress"

    def test_reject_handoff(self, client):
        task_id = self._create_assigned_task(client)

        # Initiate
        handoff_resp = client.post(f"/api/handoffs/?actor=alice", json={
            "task_id": task_id,
            "to_assignee": "bob",
            "reason": "Please review"
        })
        handoff_id = handoff_resp.json()["id"]

        # Reject
        reject_resp = client.post(f"/api/handoffs/{handoff_id}/reject", json={
            "rejected_by": "bob",
            "reason": "Not my responsibility"
        })
        assert reject_resp.status_code == 200
        assert reject_resp.json()["status"] == "rejected"
        assert reject_resp.json()["rejection_reason"] == "Not my responsibility"

    def test_initiate_handoff_unassigned_task_fails(self, client):
        create_resp = client.post("/api/tasks/", json={
            "title": "Unassigned task",
            "created_by": "tester"
        })
        task_id = create_resp.json()["id"]

        response = client.post(f"/api/handoffs/?actor=system", json={
            "task_id": task_id,
            "to_assignee": "alice",
            "reason": "Try to handoff"
        })
        assert response.status_code == 400
        assert "unassigned" in response.json()["detail"].lower()

    def test_handoff_nonexistent_task(self, client):
        response = client.post("/api/handoffs/?actor=alice", json={
            "task_id": 99999,
            "to_assignee": "bob",
            "reason": "Nope"
        })
        assert response.status_code == 404

    def test_accept_nonexistent_handoff(self, client):
        response = client.post("/api/handoffs/99999/accept", json={
            "accepted_by": "bob"
        })
        assert response.status_code == 404

    def test_get_handoff(self, client):
        task_id = self._create_assigned_task(client)
        handoff_resp = client.post(f"/api/handoffs/?actor=alice", json={
            "task_id": task_id,
            "to_assignee": "gpt-4",
            "reason": "Test"
        })
        handoff_id = handoff_resp.json()["id"]

        get_resp = client.get(f"/api/handoffs/{handoff_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == handoff_id

    def test_double_accept_fails(self, client):
        task_id = self._create_assigned_task(client)
        handoff_resp = client.post(f"/api/handoffs/?actor=alice", json={
            "task_id": task_id,
            "to_assignee": "gpt-4",
            "reason": "Test"
        })
        handoff_id = handoff_resp.json()["id"]

        # Accept first
        client.post(f"/api/handoffs/{handoff_id}/accept", json={
            "accepted_by": "gpt-4"
        })

        # Try to accept again - should fail
        second_resp = client.post(f"/api/handoffs/{handoff_id}/accept", json={
            "accepted_by": "gpt-4"
        })
        assert second_resp.status_code == 400

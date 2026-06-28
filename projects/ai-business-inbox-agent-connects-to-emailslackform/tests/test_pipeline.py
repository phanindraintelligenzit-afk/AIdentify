"""Tests for the full pipeline."""
from src.pipeline import process_message, process_batch
from src.models import IncomingMessage, RequestType


def test_pipeline_lead():
    msg = IncomingMessage(
        source="email",
        sender="prospect@bigco.com",
        subject="Demo request for enterprise",
        body="Hi, I'm Jane Doe from BigCo. We need a solution for 200 users. Please send pricing and schedule a demo next week.",
    )
    result = process_message(msg)
    assert result.request_type == RequestType.LEAD
    assert result.action == "create_lead"
    assert result.handler == "crm"
    assert result.data.company is not None
    assert "BigCo" in result.data.company
    assert len(result.draft_reply) > 20


def test_pipeline_invoice():
    msg = IncomingMessage(
        source="email",
        sender="billing@client.com",
        subject="Invoice #5678 - $10,000 due",
        body="Invoice #5678 for $10,000 is due by July 15. Please confirm receipt.",
    )
    result = process_message(msg)
    assert result.request_type == RequestType.INVOICE
    assert result.handler == "accounting"
    assert result.data.amount == 10000.0


def test_pipeline_support_urgent():
    msg = IncomingMessage(
        source="slack",
        sender="@devteam",
        subject="CRITICAL: Production down",
        body="Our production server is returning 500 errors. This is critical and blocking all users. Need immediate help!",
    )
    result = process_message(msg)
    assert result.request_type == RequestType.SUPPORT
    assert result.data.priority == "urgent"
    assert result.action == "create_ticket"


def test_process_batch():
    messages = [
        {"source": "email", "sender": "a@b.com", "subject": "Pricing?", "body": "What's your pricing?"},
        {"source": "email", "sender": "c@d.com", "subject": "Help needed", "body": "I need help with my account."},
    ]
    results = process_batch(messages)
    assert len(results) == 2
    assert results[0]["type"] == "lead"
    assert results[1]["type"] == "support"


def test_router_generates_reply():
    msg = IncomingMessage(
        source="email",
        sender="user@test.com",
        subject="Demo request",
        body="Hi, I'd like to schedule a demo. We're looking at your platform.",
    )
    result = process_message(msg)
    assert "demo" in result.draft_reply.lower() or "Hi" in result.draft_reply

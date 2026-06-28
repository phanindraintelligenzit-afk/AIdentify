"""Tests for the classifier agent."""
from src.models import IncomingMessage, RequestType
from src.agents.classifier import classify


def test_classify_lead():
    msg = IncomingMessage(
        source="email",
        sender="buyer@company.com",
        subject="Interested in your pricing",
        body="Hi, I'd like to learn more about your enterprise plan. Can we schedule a demo?",
    )
    result = classify(msg)
    assert result.request_type == RequestType.LEAD
    assert result.confidence > 0.3


def test_classify_support():
    msg = IncomingMessage(
        source="email",
        sender="user@client.com",
        subject="Help: dashboard not loading",
        body="The dashboard shows a 500 error when I try to export. This is urgent!",
    )
    result = classify(msg)
    assert result.request_type == RequestType.SUPPORT
    assert result.confidence > 0.3


def test_classify_invoice():
    msg = IncomingMessage(
        source="email",
        sender="ap@vendor.com",
        subject="Invoice #1234 overdue - $5000",
        body="This is a reminder that invoice #1234 for $5,000 USD is overdue. Please remit payment.",
    )
    result = classify(msg)
    assert result.request_type == RequestType.INVOICE


def test_classify_scheduling():
    msg = IncomingMessage(
        source="email",
        sender="prospect@co.com",
        subject="Schedule a call next week",
        body="Hi, I'd like to book a meeting for next Tuesday at 2pm to discuss the project.",
    )
    result = classify(msg)
    assert result.request_type == RequestType.SCHEDULING


def test_classify_general():
    msg = IncomingMessage(
        source="email",
        sender="random@person.com",
        subject="Hello",
        body="Just wanted to say hi and connect.",
    )
    result = classify(msg)
    assert result.request_type == RequestType.GENERAL


def test_confidence_range():
    """Confidence should always be between 0 and 1."""
    msg = IncomingMessage(
        source="email",
        sender="test@test.com",
        subject="Test",
        body="Test message with demo pricing help invoice meeting",
    )
    result = classify(msg)
    assert 0 <= result.confidence <= 1.0

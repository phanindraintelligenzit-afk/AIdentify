"""Tests for the extractor agent."""
from src.models import IncomingMessage, ClassifiedRequest, RequestType
from src.agents.extractor import extract
from src.agents.classifier import classify


def _make_request(body: str, subject: str = "", req_type: RequestType = None) -> ClassifiedRequest:
    msg = IncomingMessage(source="email", sender="test@test.com", subject=subject, body=body)
    classified = classify(msg)
    if req_type:
        classified.request_type = req_type
    return classified


def test_extract_email():
    req = _make_request("Contact me at john@acme.com for details.")
    data = extract(req)
    assert data.email == "john@acme.com"


def test_extract_name():
    req = _make_request("Hi, I'm Sarah Johnson from Acme Corp.", subject="Hello")
    data = extract(req)
    assert data.name is not None
    assert "Sarah" in data.name


def test_extract_amount():
    req = _make_request("Please pay invoice for $2,500.00 USD", subject="Invoice", req_type=RequestType.INVOICE)
    data = extract(req)
    assert data.amount == 2500.0


def test_extract_phone():
    req = _make_request("Call me at 555-123-4567 anytime.")
    data = extract(req)
    assert data.phone is not None


def test_extract_priority_urgent():
    req = _make_request("This is URGENT! Our system is down!", subject="URGENT: Help needed")
    data = extract(req)
    assert data.priority == "urgent"


def test_extract_priority_low():
    req = _make_request("No rush, just FYI for whenever you get a chance.")
    data = extract(req)
    assert data.priority == "low"


def test_extract_tags():
    req = _make_request("I need help with my account", subject="Support request", req_type=RequestType.SUPPORT)
    data = extract(req)
    assert "support" in data.tags

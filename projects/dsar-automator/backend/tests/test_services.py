"""Tests for DSAR processing services."""
import pytest
from app.services.dsar_processor import dsar_processor
from app.services.identity_verifier import identity_verifier
from app.services.data_redactor import data_redactor
from datetime import datetime, timezone, timedelta


class TestDSARProcessor:
    def test_calculate_deadline_gdpr(self):
        now = datetime.now(timezone.utc)
        deadline = dsar_processor.calculate_deadline(now, "gdpr")
        delta = deadline - now
        assert delta.days == 30

    def test_calculate_deadline_ccpa(self):
        now = datetime.now(timezone.utc)
        deadline = dsar_processor.calculate_deadline(now, "ccpa")
        delta = deadline - now
        assert delta.days == 45

    def test_calculate_days_remaining(self):
        future = datetime.now(timezone.utc) + timedelta(days=10)
        assert dsar_processor.calculate_days_remaining(future) == 10

    def test_assess_risk_low(self):
        data = {"records_found_count": 10, "data_categories_found": ["personal_info"]}
        assert dsar_processor.assess_risk(data) == "low"

    def test_assess_risk_high_sensitive_data(self):
        data = {
            "records_found_count": 100,
            "data_categories_found": ["health_data", "financial_data"],
            "description": "My lawyer will handle this",
        }
        assert dsar_processor.assess_risk(data) == "high"

    def test_classify_request_type_erasure(self):
        assert dsar_processor.classify_request_type("Please delete all my data") == "erasure"

    def test_classify_request_type_rectification(self):
        assert dsar_processor.classify_request_type("I need to correct my address") == "rectification"

    def test_classify_request_type_portability(self):
        assert dsar_processor.classify_request_type("Export my data as JSON") == "portability"

    def test_classify_request_type_access(self):
        assert dsar_processor.classify_request_type("What info do you have?") == "access"

    def test_should_escalate_close_deadline(self):
        data = {"days_remaining": 2, "status": "reviewing", "risk_level": "low"}
        assert dsar_processor.should_escalate(data) is True

    def test_should_escalate_high_risk(self):
        data = {"days_remaining": 20, "status": "reviewing", "risk_level": "high"}
        assert dsar_processor.should_escalate(data) is True

    def test_should_not_escalate_normal(self):
        data = {"days_remaining": 20, "status": "reviewing", "risk_level": "low"}
        assert dsar_processor.should_escalate(data) is False


class TestIdentityVerifier:
    def test_verify_by_email_match(self):
        result = identity_verifier.verify_by_email("user@example.com", "user@example.com")
        assert result["verified"] is True
        assert result["confidence"] == "high"

    def test_verify_by_email_mismatch(self):
        result = identity_verifier.verify_by_email("other@example.com", "user@example.com")
        assert result["verified"] is False

    def test_verify_by_account(self):
        result = identity_verifier.verify_by_account("acc_123", "user@example.com")
        assert result["verified"] is True

    def test_recommend_method_with_account(self):
        result = identity_verifier.recommend_verification_method({"has_account": True})
        assert result == "account_ownership"

    def test_recommend_method_no_info(self):
        result = identity_verifier.recommend_verification_method({})
        assert result == "document_upload"


class TestDataRedactor:
    def test_redact_email(self):
        text = "Contact john.doe@example.com for info"
        result = data_redactor.redact_pii(text)
        assert "john.doe@example.com" not in result
        assert "[EMAIL REDACTED]" in result

    def test_redact_phone(self):
        text = "Call +1-800-555-1234"
        result = data_redactor.redact_pii(text)
        assert "[PHONE REDACTED]" in result

    def test_redact_ssn(self):
        text = "SSN: 123-45-6789"
        result = data_redactor.redact_pii(text)
        assert "[SSN REDACTED]" in result

    def test_redact_credit_card(self):
        text = "Card: 4111-1111-1111-1111"
        result = data_redactor.redact_pii(text)
        assert "[CARD REDACTED]" in result

    def test_redact_third_party_fields(self):
        records = [{"name": "John", "third_party_name": "Jane", "data": "test"}]
        result = data_redactor.redact_third_party_data(records)
        assert result[0]["third_party_name"] == "[THIRD-PARTY REDACTED]"

    def test_redact_dataset_fields(self):
        records = [{"a": 1, "b": 2, "c": 3}]
        result, count = data_redactor.redact_dataset(records, ["b", "c"])
        assert count == 2
        assert result[0]["b"] == "[REDACTED]"

    def test_redaction_report(self):
        report = data_redactor.generate_redaction_report(10, 3)
        assert report["redacted_fields"] == 3
        assert report["redaction_percentage"] == 30.0

"""Data redaction service - removes PII and third-party data from responses."""
import re
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DataRedactor:
    """Redacts sensitive information from DSAR response data."""

    EMAIL_PATTERN = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
    PHONE_PATTERN = re.compile(r'\+?[\d\s\-\(\)]{10,}')
    SSN_PATTERN = re.compile(r'\d{3}-\d{2}-\d{4}')
    CREDIT_CARD_PATTERN = re.compile(r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}')
    IP_PATTERN = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')

    def redact_pii(self, text: str) -> str:
        """Remove PII from text content."""
        text = self.EMAIL_PATTERN.sub('[EMAIL REDACTED]', text)
        text = self.SSN_PATTERN.sub('[SSN REDACTED]', text)
        text = self.CREDIT_CARD_PATTERN.sub('[CARD REDACTED]', text)
        text = self.PHONE_PATTERN.sub('[PHONE REDACTED]', text)
        text = self.IP_PATTERN.sub('[IP REDACTED]', text)
        return text

    def redact_third_party_data(self, records: List[Dict]) -> List[Dict]:
        """Remove data belonging to third parties from records."""
        redacted = []
        for record in records:
            cleaned = {}
            for key, value in record.items():
                if key in ("third_party_name", "third_party_email", "other_user_data"):
                    cleaned[key] = "[THIRD-PARTY REDACTED]"
                elif isinstance(value, str):
                    cleaned[key] = self.redact_pii(value)
                else:
                    cleaned[key] = value
            redacted.append(cleaned)
        return redacted

    def redact_dataset(self, data: List[Dict], fields_to_redact: List[str]) -> tuple:
        """Redact specific fields across a dataset."""
        redaction_count = 0
        redacted_data = []
        for record in data:
            new_record = {}
            for key, value in record.items():
                if key in fields_to_redact:
                    new_record[key] = "[REDACTED]"
                    redaction_count += 1
                else:
                    new_record[key] = value
            redacted_data.append(new_record)
        return redacted_data, redaction_count

    def generate_redaction_report(self, original_count: int, redacted_count: int) -> dict:
        """Generate a report of what was redacted for audit purposes."""
        return {
            "total_fields": original_count,
            "redacted_fields": redacted_count,
            "redaction_percentage": round((redacted_count / max(original_count, 1)) * 100, 2),
            "redaction_categories": ["third_party_pii", "contact_info", "financial_data"],
        }


data_redactor = DataRedactor()

"""
PII Detector — Regex-based scanning for personally identifiable information.

Detects: email addresses, phone numbers, SSNs, credit card numbers.
Returns detection results with types found and redacted previews.
"""

import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class PIIDetectionResult:
    """Result of a PII scan."""
    pii_detected: bool
    pii_types: List[str] = field(default_factory=list)
    redacted_text: str = ""


# Regex patterns for PII detection
PATTERNS = {
    "email": re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    ),
    "phone": re.compile(
        r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    ),
    "ssn": re.compile(
        r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'
    ),
    "credit_card": re.compile(
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
    ),
}

# Mapping of pattern names to risk weights
PII_RISK_WEIGHTS = {
    "email": 10,
    "phone": 15,
    "ssn": 30,
    "credit_card": 25,
}


def scan_text(text: str) -> PIIDetectionResult:
    """
    Scan text for PII patterns.

    Args:
        text: The text to scan.

    Returns:
        PIIDetectionResult with detection status, types found, and redacted text.
    """
    if not text:
        return PIIDetectionResult(pii_detected=False)

    detected_types = []
    redacted = text

    for pii_type, pattern in PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            detected_types.append(pii_type)
            # Redact matches in the text
            for match in matches:
                redacted = redacted.replace(match, f"[REDACTED_{pii_type.upper()}]")

    return PIIDetectionResult(
        pii_detected=len(detected_types) > 0,
        pii_types=detected_types,
        redacted_text=redacted,
    )


def calculate_pii_risk(pii_types: List[str]) -> int:
    """
    Calculate a risk contribution score based on detected PII types.

    Args:
        pii_types: List of detected PII type strings.

    Returns:
        Integer risk contribution (0-100 scale).
    """
    if not pii_types:
        return 0
    total = sum(PII_RISK_WEIGHTS.get(t, 5) for t in pii_types)
    return min(total, 100)

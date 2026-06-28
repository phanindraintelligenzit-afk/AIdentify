"""Classifier Agent — determines what type of business request an incoming message is."""
import re
from src.models import IncomingMessage, ClassifiedRequest, RequestType

# Keyword patterns for classification
PATTERNS = {
    RequestType.LEAD: [
        r'\b(interest(ed)?|demo|trial|pricing|quote|proposal|partnership|integrat)\b',
        r'\b(buy|purchase|sign up|subscribe|upgrade|plan)\b',
        r'\b(sales|revenue|pipeline|opportunity|deal)\b',
    ],
    RequestType.SUPPORT: [
        r'\b(help|issue|bug|error|broken|not working|problem|troubleshoot)\b',
        r'\b(refund|cancel|complaint|escalate|urgent)\b',
        r'\b(how do I|how can I|can you help|support)\b',
    ],
    RequestType.INVOICE: [
        r'\b(invoice|payment|receipt|bill|charge|due|overdue|pay now)\b',
        r'\b(purchase order|PO\s*\d|amount due|balance)\b',
        r'\$\s*\d+[\d,]*\.?\d*',
    ],
    RequestType.SCHEDULING: [
        r'\b(meeting|call|schedule|book|appointment|calendar|available)\b',
        r'\b(next week|tomorrow|monday|tuesday|wednesday|thursday|friday)\b',
        r'\b(\d{1,2}:\d{2}\s*(am|pm)?)\b',
    ],
}


def classify(message: IncomingMessage) -> ClassifiedRequest:
    """Classify an incoming message into a request type.

    Uses keyword matching + scoring. In production, this would use LLM classification.
    """
    text = f"{message.subject} {message.body}".lower()
    scores = {}

    for req_type, patterns in PATTERNS.items():
        score = 0
        matched = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                score += len(matches)
                matched.append(pattern[:30])
        scores[req_type] = (score, matched)

    # Pick highest scoring type
    best_type = max(scores, key=lambda k: scores[k][0])
    best_score, best_signals = scores[best_type]

    # Normalize confidence
    total_signals = sum(s[0] for s in scores.values()) or 1
    confidence = min(best_score / max(total_signals, 1), 1.0)

    # Default to GENERAL if no strong signal
    if best_score == 0:
        best_type = RequestType.GENERAL
        confidence = 0.5

    return ClassifiedRequest(
        message=message,
        request_type=best_type,
        confidence=confidence,
        signals=best_signals,
    )


if __name__ == "__main__":
    # Quick test
    msg = IncomingMessage(
        source="email",
        sender="john@acme.com",
        subject="Interested in your enterprise plan",
        body="Hi, I'd like to schedule a demo for next week. We're looking at solutions for our team of 50.",
    )
    result = classify(msg)
    print(f"Type: {result.request_type.value} (confidence: {result.confidence:.2f})")
    print(f"Signals: {result.signals}")

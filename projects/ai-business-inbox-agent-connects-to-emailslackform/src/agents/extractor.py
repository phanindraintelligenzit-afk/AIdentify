"""Extractor Agent — pulls structured data from classified messages."""
import re
from src.models import ClassifiedRequest, ExtractedData, RequestType


def extract(request: ClassifiedRequest) -> ExtractedData:
    """Extract structured data from a classified request.

    Uses regex patterns. In production, use LLM extraction for complex messages.
    """
    text = f"{request.message.subject} {request.message.body}"
    text_lower = text.lower()

    # Email extraction
    email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', text)
    email = email_match.group(0) if email_match else request.message.sender

    # Name extraction
    name = None
    # Pattern: "I'm Name" or "my name is Name" — with word boundaries
    name_match = re.search(r"\b(i'?m|name is|this is)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b", text, re.IGNORECASE)
    if name_match:
        name = name_match.group(2).strip()
    else:
        # Try "Name <email>"
        name_match = re.search(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*<', text)
        if name_match:
            name = name_match.group(1).strip()
        else:
            # Try sender name from email (john@acme.com -> John)
            sender_name = request.message.sender.split('@')[0]
            if '.' in sender_name:
                parts = sender_name.split('.')
                name = ' '.join(p.capitalize() for p in parts)
            elif sender_name and not sender_name.startswith('@'):
                name = sender_name.capitalize()

    # Company extraction
    company = None
    company_match = re.search(r'(?:at|from|with|company|organization)\s+([A-Z][\w&\s]{2,30}?)(?:,|\.|\s+and|\s+we|\s+is)', text)
    if company_match:
        company = company_match.group(1).strip()

    # Phone extraction
    phone = None
    phone_match = re.search(r'(?:\+?1?[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phone_match:
        phone = phone_match.group(0).strip()

    # Amount extraction (for invoices)
    amount = None
    amount_match = re.search(r'(?:USD|EUR|GBP|\$)\s*([\d,]+\.?\d*)', text)
    if not amount_match:
        amount_match = re.search(r'([\d,]+\.?\d{0,2})\s*(?:USD|EUR|GBP|dollars?|euros?)', text, re.IGNORECASE)
    if amount_match:
        amount = float(amount_match.group(1).replace(',', ''))

    # Date extraction (simple patterns)
    due_date = None
    meeting_date = None
    date_patterns = [
        r'(?:due|by|before|until)\s+(\w+\s+\d{1,2}(?:,?\s+\d{4})?)',
        r'(?:on|at)\s+(\w+\s+\d{1,2}(?:,?\s+\d{4})?)',
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    ]
    for pattern in date_patterns:
        date_match = re.search(pattern, text, re.IGNORECASE)
        if date_match:
            if request.request_type == RequestType.SCHEDULING:
                meeting_date = date_match.group(1)
            elif request.request_type == RequestType.INVOICE:
                due_date = date_match.group(1)
            break

    # Priority detection
    priority = "medium"
    if any(w in text_lower for w in ['urgent', 'asap', 'immediately', 'critical', 'emergency']):
        priority = "urgent"
    elif any(w in text_lower for w in ['important', 'priority', 'high priority']):
        priority = "high"
    elif any(w in text_lower for w in ['low priority', 'no rush', 'whenever', 'fyi']):
        priority = "low"

    # Intent summary (first sentence)
    intent = text.split('.')[0].strip()[:100]

    # Tags
    tags = []
    if request.request_type == RequestType.LEAD:
        tags.append('sales')
    elif request.request_type == RequestType.SUPPORT:
        tags.append('support')
    elif request.request_type == RequestType.INVOICE:
        tags.append('finance')
    elif request.request_type == RequestType.SCHEDULING:
        tags.append('calendar')

    return ExtractedData(
        name=name,
        email=email,
        company=company,
        phone=phone,
        amount=amount,
        due_date=due_date,
        meeting_date=meeting_date,
        intent=intent,
        priority=priority,
        tags=tags,
    )

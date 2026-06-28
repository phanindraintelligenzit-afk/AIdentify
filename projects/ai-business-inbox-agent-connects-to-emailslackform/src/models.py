"""Business Inbox Agent — unified intake pipeline.

Agents:
  1. Classifier — determines request type (lead, support, invoice, scheduling, other)
  2. Extractor — pulls structured data (name, email, company, amount, dates, intent)
  3. Router — dispatches to correct downstream handler
  4. Responder — drafts context-aware replies or action summaries
"""

from pydantic import BaseModel
from typing import Optional
from enum import Enum


class RequestType(str, Enum):
    LEAD = "lead"
    SUPPORT = "support"
    INVOICE = "invoice"
    SCHEDULING = "scheduling"
    GENERAL = "general"


class IncomingMessage(BaseModel):
    """Raw inbound message from any channel."""
    source: str  # email, slack, form, webhook
    sender: str
    subject: str = ""
    body: str
    raw: dict = {}


class ClassifiedRequest(BaseModel):
    """Message after classification."""
    message: IncomingMessage
    request_type: RequestType
    confidence: float  # 0-1
    signals: list[str] = []


class ExtractedData(BaseModel):
    """Structured data pulled from the message."""
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "USD"
    due_date: Optional[str] = None
    meeting_date: Optional[str] = None
    intent: str = ""
    priority: str = "medium"  # low, medium, high, urgent
    tags: list[str] = []


class RoutedAction(BaseModel):
    """Final routed action with context."""
    request_type: RequestType
    data: ExtractedData
    action: str  # create_lead, create_ticket, create_invoice, schedule_meeting, draft_reply
    handler: str  # which downstream system
    draft_reply: str = ""
    notes: str = ""

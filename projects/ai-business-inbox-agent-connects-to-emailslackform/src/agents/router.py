"""Router Agent — determines what action to take and where to send it."""
from src.models import ClassifiedRequest, ExtractedData, RoutedAction, RequestType


# Map request types to downstream handlers
HANDLERS = {
    RequestType.LEAD: {
        "action": "create_lead",
        "handler": "crm",
        "description": "Create a new lead in CRM and trigger follow-up sequence",
    },
    RequestType.SUPPORT: {
        "action": "create_ticket",
        "handler": "helpdesk",
        "description": "Create support ticket and assign to appropriate team",
    },
    RequestType.INVOICE: {
        "action": "create_invoice",
        "handler": "accounting",
        "description": "Create invoice record and send payment reminder",
    },
    RequestType.SCHEDULING: {
        "action": "schedule_meeting",
        "handler": "calendar",
        "description": "Find available slots and send calendar invite",
    },
    RequestType.GENERAL: {
        "action": "draft_reply",
        "handler": "email",
        "description": "Draft a response for human review",
    },
}


def route(request: ClassifiedRequest, data: ExtractedData) -> RoutedAction:
    """Route a classified + extracted request to the right downstream action."""
    handler_info = HANDLERS[request.request_type]

    # Generate draft reply based on type
    draft = _generate_draft(request, data)

    # Build routing notes
    notes = (
        f"Classified as {request.request_type.value} "
        f"(confidence: {request.confidence:.0%}). "
        f"Handler: {handler_info['handler']}. "
        f"Priority: {data.priority}."
    )

    if data.company:
        notes += f" Company: {data.company}."
    if data.amount:
        notes += f" Amount: ${data.amount:.2f}."

    return RoutedAction(
        request_type=request.request_type,
        data=data,
        action=handler_info["action"],
        handler=handler_info["handler"],
        draft_reply=draft,
        notes=notes,
    )


def _generate_draft(request: ClassifiedRequest, data: ExtractedData) -> str:
    """Generate a draft reply based on request type."""
    name = (data.name or "there").split()[0]  # First name only
    company = data.company or "your company"
    amount_str = f"{data.amount:.2f}" if data.amount else "N/A"

    drafts = {
        RequestType.LEAD: (
            f"Hi {name},\n\n"
            f"Thanks for your interest! I'd love to learn more about what "
            f"{company} is looking for. Would you be open to a 15-minute call this week?\n\n"
            f"Best regards"
        ),
        RequestType.SUPPORT: (
            f"Hi {name},\n\n"
            f"Thanks for reaching out. I've created a ticket for your issue "
            f"and our team will look into it shortly. "
            f"{'This has been marked as urgent.' if data.priority == 'urgent' else 'We typically respond within 24 hours.'}\n\n"
            f"Best regards"
        ),
        RequestType.INVOICE: (
            f"Hi {name},\n\n"
            f"{'This is a friendly reminder that' if data.due_date else 'Regarding'} "
            f"invoice amount of ${amount_str} "
            f"{'is due ' + data.due_date if data.due_date else 'requires attention'}. "
            f"Please let us know if you have any questions.\n\n"
            f"Best regards"
        ),
        RequestType.SCHEDULING: (
            f"Hi {name},\n\n"
            f"I'd be happy to meet! I'll send over a calendar link with "
            f"available time slots. Looking forward to connecting.\n\n"
            f"Best regards"
        ),
        RequestType.GENERAL: (
            f"Hi {name},\n\n"
            f"Thanks for your message. I'll look into this and get back to you soon.\n\n"
            f"Best regards"
        ),
    }

    return drafts.get(request.request_type, drafts[RequestType.GENERAL])

"""Business Inbox Agent — unified intake pipeline.

Connects to email/Slack/forms, classifies incoming requests,
extracts structured data, and routes to the right workflow.
"""
from src.models import IncomingMessage, RoutedAction
from src.agents.classifier import classify
from src.agents.extractor import extract
from src.agents.router import route


def process_message(message: IncomingMessage) -> RoutedAction:
    """Process a single incoming message through the full pipeline.

    Pipeline: Classify → Extract → Route
    """
    # Step 1: Classify the request type
    classified = classify(message)

    # Step 2: Extract structured data
    data = extract(classified)

    # Step 3: Route to appropriate action
    action = route(classified, data)

    return action


def process_batch(messages: list[dict]) -> list[dict]:
    """Process multiple messages. Returns JSON-serializable results."""
    results = []
    for msg_data in messages:
        msg = IncomingMessage(**msg_data)
        action = process_message(msg)
        results.append({
            "sender": msg.sender,
            "subject": msg.subject,
            "type": action.request_type.value,
            "action": action.action,
            "handler": action.handler,
            "priority": action.data.priority,
            "company": action.data.company,
            "amount": action.data.amount,
            "draft_reply": action.draft_reply,
            "notes": action.notes,
        })
    return results


if __name__ == "__main__":
    # Demo with sample messages
    samples = [
        {
            "source": "email",
            "sender": "sarah@techcorp.com",
            "subject": "Interested in enterprise plan",
            "body": "Hi, I'm Sarah from TechCorp. We're looking for a solution for our team of 100. Could you share pricing and schedule a demo for next Tuesday?",
        },
        {
            "source": "email",
            "sender": "mike@startup.io",
            "subject": "URGENT: Payment failed",
            "body": "Hi, I'm Mike from Startup.io. Our payment for invoice #1234 ($2,500 USD) failed yesterday. Our service was interrupted. Please help!",
        },
        {
            "source": "slack",
            "sender": "@alex",
            "subject": "",
            "body": "Hey, the dashboard is showing a 500 error when I try to export reports. This is blocking my team. Can someone help?",
        },
        {
            "source": "form",
            "sender": "john@bigco.com",
            "subject": "Partnership inquiry",
            "body": "Hello, I'm John Smith, VP of Engineering at BigCo. We'd like to discuss a partnership opportunity. You can reach me at john@bigco.com or 555-123-4567.",
        },
    ]

    print("=" * 60)
    print("  Business Inbox Agent — Demo")
    print("=" * 60)

    results = process_batch(samples)
    for r in results:
        print(f"\n📨 {r['sender']}: {r['subject'] or '(no subject)'}")
        print(f"   → Type: {r['type'].upper()} | Action: {r['action']} → {r['handler']}")
        print(f"   → Priority: {r['priority']}")
        if r['company']:
            print(f"   → Company: {r['company']}")
        if r['amount']:
            print(f"   → Amount: ${r['amount']:.2f}")
        print(f"   → Draft: {r['draft_reply'][:80]}...")

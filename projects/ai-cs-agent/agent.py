"""Knowledge Base RAG engine for the AI Customer Service Agent."""
import os
import re
from pathlib import Path
from typing import Optional

import httpx

KB_DIR = Path(__file__).parent / "kb"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b")


def load_knowledge_base() -> list[dict]:
    """Load all markdown files from the knowledge base directory."""
    documents = []
    if not KB_DIR.exists():
        return documents

    for filepath in KB_DIR.glob("*.md"):
        content = filepath.read_text(encoding="utf-8")
        # Split into sections by ## headings
        sections = re.split(r"^## ", content, flags=re.MULTILINE)
        for section in sections:
            if not section.strip():
                continue
            lines = section.strip().split("\n", 1)
            heading = lines[0].strip()
            body = lines[1].strip() if len(lines) > 1 else ""
            documents.append({
                "source": filepath.name,
                "section": heading,
                "content": f"{heading}\n{body}",
            })
    return documents


def simple_retrieve(query: str, documents: list[dict], top_k: int = 3) -> list[dict]:
    """Simple keyword-based retrieval (TF-like scoring)."""
    query_words = set(query.lower().split())
    scored = []
    for doc in documents:
        content_lower = doc["content"].lower()
        # Score by number of query words found in the document
        score = sum(1 for w in query_words if w in content_lower)
        # Bonus for exact phrase match
        if query.lower() in content_lower:
            score += 5
        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


async def generate_response(query: str, context_docs: list[dict]) -> str:
    """Generate a response using Ollama with the retrieved context."""
    if not context_docs:
        return (
            "I don't have enough information to answer that question. "
            "Let me connect you with a human agent who can help."
        )

    context_text = "\n\n".join(
        f"[Source: {doc['source']} - {doc['section']}]\n{doc['content']}"
        for doc in context_docs
    )

    prompt = f"""You are a helpful customer service agent for AIdentify, an AI agent marketplace.
Answer the customer's question using ONLY the knowledge base context below.
Be concise, friendly, and accurate. If the context doesn't contain the answer, say so.

KNOWLEDGE BASE CONTEXT:
{context_text}

CUSTOMER QUESTION: {query}

ANSWER (include the source citation at the end):"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 512},
                },
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "Sorry, I couldn't generate a response.")
    except Exception as e:
        # Fallback: return the most relevant context directly
        best = context_docs[0]
        return (
            f"Based on our documentation ({best['source']} - {best['section']}):\n\n"
            f"{best['content']}\n\n"
            f"[Note: AI model temporarily unavailable, showing direct KB match]"
        )


def triage_message(message: str) -> dict:
    """Classify incoming message by intent, sentiment, and priority."""
    msg_lower = message.lower()

    # Intent classification
    intents = {
        "billing": ["bill", "charge", "payment", "invoice", "refund", "subscription", "cancel", "price", "cost"],
        "technical": ["error", "bug", "broken", "not working", "failed", "issue", "problem", "deploy", "integration"],
        "account": ["password", "login", "locked", "account", "reset", "sign in", "access"],
        "how_to": ["how do i", "how to", "how can", "where do", "guide", "tutorial", "setup"],
        "sales": ["pricing", "demo", "enterprise", "plan", "upgrade", "features"],
        "data_export": ["export", "download data", "gdpr", "delete my data", "data request"],
    }

    detected_intent = "general"
    max_matches = 0
    for intent, keywords in intents.items():
        matches = sum(1 for kw in keywords if kw in msg_lower)
        if matches > max_matches:
            max_matches = matches
            detected_intent = intent

    # Sentiment analysis (simple keyword-based)
    negative_words = ["angry", "frustrated", "terrible", "worst", "hate", "awful", "unacceptable", "ridiculous", "furious", "urgent"]
    positive_words = ["thanks", "thank you", "great", "awesome", "love", "helpful", "good", "excellent", "perfect"]
    
    neg_count = sum(1 for w in negative_words if w in msg_lower)
    pos_count = sum(1 for w in positive_words if w in msg_lower)
    
    if neg_count > pos_count:
        sentiment = "negative"
    elif pos_count > neg_count:
        sentiment = "positive"
    else:
        sentiment = "neutral"

    # Priority assignment
    urgency_keywords = ["urgent", "asap", "immediately", "critical", "down", "emergency", "locked out"]
    is_urgent = any(kw in msg_lower for kw in urgency_keywords)
    
    if is_urgent or (detected_intent == "billing" and sentiment == "negative"):
        priority = "high"
    elif detected_intent in ("technical", "account") or sentiment == "negative":
        priority = "medium"
    else:
        priority = "low"

    # Escalation detection
    escalation_triggers = [
        "sue", "lawyer", "legal action", "complaint", "manager",
        "human", "real person", "speak to someone", "escalate",
        "cancel everything", "delete my account", "data breach",
    ]
    needs_escalation = any(kw in msg_lower for kw in escalation_triggers)
    # Also escalate if very negative + high priority
    if sentiment == "negative" and priority == "high":
        needs_escalation = True

    return {
        "intent": detected_intent,
        "sentiment": sentiment,
        "priority": priority,
        "needs_escalation": needs_escalation,
    }

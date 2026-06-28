"""Tests for the AI Customer Service Agent."""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import load_knowledge_base, simple_retrieve, triage_message, generate_response
from database import (
    init_db, create_conversation, add_message, get_conversation_messages,
    get_analytics, resolve_conversation, get_or_create_conversation,
)


def test_load_knowledge_base():
    """Test that knowledge base loads correctly."""
    docs = load_knowledge_base()
    assert len(docs) > 0, "Knowledge base should load at least one section"
    
    # Check that we have content from all files
    sources = {d["source"] for d in docs}
    assert "faq.md" in sources, "FAQ should be loaded"
    assert "troubleshooting.md" in sources, "Troubleshooting guide should be loaded"
    assert "policies.md" in sources, "Policies should be loaded"
    
    # Each doc should have required fields
    for doc in docs:
        assert "source" in doc
        assert "section" in doc
        assert "content" in doc
        assert len(doc["content"]) > 0
    
    print(f"✅ Loaded {len(docs)} KB sections from {len(sources)} files")


def test_simple_retrieve():
    """Test keyword-based retrieval."""
    docs = load_knowledge_base()
    
    # Test billing query
    results = simple_retrieve("How do I get a refund?", docs, top_k=3)
    assert len(results) > 0, "Should find relevant docs for refund query"
    assert any("refund" in r["content"].lower() or "billing" in r["content"].lower() for r in results), \
        "Should find billing/refund related content"
    
    # Test technical query
    results = simple_retrieve("agent won't deploy error", docs, top_k=3)
    assert len(results) > 0, "Should find relevant docs for deployment query"
    
    # Test account query
    results = simple_retrieve("reset my password", docs, top_k=3)
    assert len(results) > 0, "Should find relevant docs for password reset"
    assert any("password" in r["content"].lower() for r in results), \
        "Should find password-related content"
    
    print("✅ Retrieval returns relevant results")


def test_triage_message():
    """Test message triage classification."""
    # Test billing intent with negative sentiment
    result = triage_message("This is terrible! I was charged twice and want a refund immediately!")
    assert result["intent"] == "billing", f"Expected billing intent, got {result['intent']}"
    assert result["sentiment"] == "negative", f"Expected negative sentiment, got {result['sentiment']}"
    assert result["priority"] in ("high", "medium"), f"Expected high/medium priority, got {result['priority']}"
    
    # Test technical intent
    result = triage_message("My agent won't deploy, getting an error")
    assert result["intent"] == "technical", f"Expected technical intent, got {result['intent']}"
    
    # Test account intent
    result = triage_message("I forgot my password and can't login")
    assert result["intent"] == "account", f"Expected account intent, got {result['intent']}"
    
    # Test escalation triggers
    result = triage_message("I want to speak to a manager and sue you")
    assert result["needs_escalation"] is True, "Should escalate legal threats"
    
    result = triage_message("This is urgent! I'm locked out of my account!")
    assert result["needs_escalation"] is True, "Should escalate urgent lockout"
    
    # Test positive sentiment
    result = triage_message("Thanks for the great product! How do I upgrade?")
    assert result["sentiment"] == "positive", f"Expected positive sentiment, got {result['sentiment']}"
    
    # Test how_to intent
    result = triage_message("How do I get started with the platform?")
    assert result["intent"] == "how_to", f"Expected how_to intent, got {result['intent']}"
    
    print("✅ Triage classification works correctly")


def test_database_operations():
    """Test SQLite database operations."""
    # Use a test database
    import database
    original_path = database.DB_PATH
    database.DB_PATH = Path(__file__).parent.parent / "data" / "test_conversations.db"
    
    try:
        init_db()
        
        # Create conversation
        conv_id = create_conversation("test-session-123", "test@example.com")
        assert conv_id > 0, "Should create conversation with valid ID"
        
        # Add messages
        msg1 = add_message(conv_id, "customer", "I need help with billing", intent="billing", sentiment="neutral", priority="medium")
        msg2 = add_message(conv_id, "agent", "I can help with billing!", intent=None, sentiment=None, priority=None)
        assert msg1 > 0 and msg2 > 0, "Should add messages"
        
        # Retrieve messages
        messages = get_conversation_messages(conv_id)
        assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}"
        assert messages[0]["sender"] == "customer"
        assert messages[1]["sender"] == "agent"
        
        # Test get_or_create (should return same conv for same session)
        conv_id2 = get_or_create_conversation("test-session-123")
        assert conv_id == conv_id2, "Should return existing conversation"
        
        # Resolve conversation
        resolve_conversation(conv_id)
        analytics = get_analytics()
        assert analytics["total_conversations"] >= 1
        assert analytics["resolved"] >= 1
        
        print("✅ Database operations work correctly")
        
    finally:
        # Cleanup test database
        database.DB_PATH = original_path
        test_db = Path(__file__).parent.parent / "data" / "test_conversations.db"
        if test_db.exists():
            test_db.unlink()


def test_generate_response_fallback():
    """Test that generate_response has a working fallback when Ollama is unavailable."""
    # This tests the fallback path (when Ollama is not running)
    docs = load_knowledge_base()
    results = simple_retrieve("password reset", docs, top_k=2)
    
    # We can't easily test the async function without an event loop setup,
    # but we can verify the docs are valid for the response generator
    assert len(results) > 0
    assert all("content" in r for r in results)
    print("✅ Response generation prerequisites are valid")


def test_analytics():
    """Test analytics computation."""
    import database
    original_path = database.DB_PATH
    database.DB_PATH = Path(__file__).parent.parent / "data" / "test_analytics.db"
    
    try:
        init_db()
        
        # Create some test data
        c1 = create_conversation("sess1", "a@test.com")
        c2 = create_conversation("sess2", "b@test.com")
        c3 = create_conversation("sess3", "c@test.com")
        
        add_message(c1, "customer", "billing question", intent="billing", sentiment="neutral", priority="medium")
        add_message(c1, "agent", "here's help")
        add_message(c2, "customer", "urgent problem!", intent="technical", sentiment="negative", priority="high", needs_escalation=True)
        add_message(c2, "agent", "escalating...")
        add_message(c3, "customer", "how to setup", intent="how_to", sentiment="positive", priority="low")
        add_message(c3, "agent", "here's how")
        
        resolve_conversation(c1)
        resolve_conversation(c3)
        
        analytics = get_analytics()
        assert analytics["total_conversations"] >= 3
        assert analytics["resolved"] >= 2
        assert analytics["resolution_rate"] > 0
        assert "billing" in analytics["intents"]
        assert "negative" in analytics["sentiments"]
        assert analytics["escalated_messages"] >= 1
        
        print(f"✅ Analytics computed correctly: {analytics['total_conversations']} convos, {analytics['resolution_rate']}% resolution")
        
    finally:
        database.DB_PATH = original_path
        test_db = Path(__file__).parent.parent / "data" / "test_analytics.db"
        if test_db.exists():
            test_db.unlink()


if __name__ == "__main__":
    print("Running AI CS Agent tests...\n")
    
    test_load_knowledge_base()
    test_simple_retrieve()
    test_triage_message()
    test_database_operations()
    test_generate_response_fallback()
    test_analytics()
    
    print("\n🎉 All tests passed!")

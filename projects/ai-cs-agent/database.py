"""SQLite storage for conversations and tickets."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "conversations.db"


def get_db() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize the database schema."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            customer_email TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            resolved INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            intent TEXT,
            sentiment TEXT,
            priority TEXT,
            needs_escalation INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        );

        CREATE INDEX IF NOT EXISTS idx_messages_conversation 
            ON messages(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_conversations_status 
            ON conversations(status);
    """)
    conn.commit()
    conn.close()


def create_conversation(session_id: str, customer_email: str | None = None) -> int:
    """Create a new conversation and return its ID."""
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO conversations (session_id, customer_email, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (session_id, customer_email, now, now),
    )
    conn.commit()
    conv_id = cursor.lastrowid
    conn.close()
    return conv_id


def get_conversation(conversation_id: int) -> dict | None:
    """Get a conversation by ID."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_or_create_conversation(session_id: str, customer_email: str | None = None) -> int:
    """Get existing open conversation or create new one."""
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM conversations WHERE session_id = ? AND status = 'open' ORDER BY updated_at DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    conn.close()
    if row:
        return row["id"]
    return create_conversation(session_id, customer_email)


def add_message(
    conversation_id: int,
    sender: str,
    content: str,
    intent: str | None = None,
    sentiment: str | None = None,
    priority: str | None = None,
    needs_escalation: bool = False,
) -> int:
    """Add a message to a conversation."""
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO messages 
           (conversation_id, sender, content, intent, sentiment, priority, needs_escalation, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (conversation_id, sender, content, intent, sentiment, priority, int(needs_escalation), now),
    )
    conn.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (now, conversation_id),
    )
    conn.commit()
    msg_id = cursor.lastrowid
    conn.close()
    return msg_id


def get_conversation_messages(conversation_id: int) -> list[dict]:
    """Get all messages in a conversation."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY id ASC",
        (conversation_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_conversations(limit: int = 50) -> list[dict]:
    """List recent conversations."""
    conn = get_db()
    rows = conn.execute(
        """SELECT c.*, 
                  (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as message_count,
                  (SELECT content FROM messages m WHERE m.conversation_id = c.id ORDER BY m.id DESC LIMIT 1) as last_message
           FROM conversations c 
           ORDER BY c.updated_at DESC 
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolve_conversation(conversation_id: int):
    """Mark a conversation as resolved."""
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    conn.execute(
        "UPDATE conversations SET status = 'resolved', resolved = 1, updated_at = ? WHERE id = ?",
        (now, conversation_id),
    )
    conn.commit()
    conn.close()


def get_analytics() -> dict:
    """Get dashboard analytics."""
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) as cnt FROM conversations").fetchone()["cnt"]
    resolved = conn.execute("SELECT COUNT(*) as cnt FROM conversations WHERE resolved = 1").fetchone()["cnt"]
    open_count = conn.execute("SELECT COUNT(*) as cnt FROM conversations WHERE status = 'open'").fetchone()["cnt"]
    escalated = conn.execute("SELECT COUNT(*) as cnt FROM messages WHERE needs_escalation = 1").fetchone()["cnt"]
    
    # Intent distribution
    intent_rows = conn.execute(
        "SELECT intent, COUNT(*) as cnt FROM messages WHERE intent IS NOT NULL GROUP BY intent ORDER BY cnt DESC"
    ).fetchall()
    
    # Sentiment distribution
    sentiment_rows = conn.execute(
        "SELECT sentiment, COUNT(*) as cnt FROM messages WHERE sentiment IS NOT NULL GROUP BY sentiment ORDER BY cnt DESC"
    ).fetchall()
    
    # Priority distribution
    priority_rows = conn.execute(
        "SELECT priority, COUNT(*) as cnt FROM messages WHERE priority IS NOT NULL GROUP BY priority ORDER BY cnt DESC"
    ).fetchall()
    
    conn.close()
    
    resolution_rate = (resolved / total * 100) if total > 0 else 0
    
    return {
        "total_conversations": total,
        "resolved": resolved,
        "open": open_count,
        "escalated_messages": escalated,
        "resolution_rate": round(resolution_rate, 1),
        "intents": {r["intent"]: r["cnt"] for r in intent_rows},
        "sentiments": {r["sentiment"]: r["cnt"] for r in sentiment_rows},
        "priorities": {r["priority"]: r["cnt"] for r in priority_rows},
    }

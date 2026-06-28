"""AI Customer Service Agent - FastAPI application."""
import asyncio
import json
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from agent import load_knowledge_base, simple_retrieve, generate_response, triage_message
from database import (
    init_db, get_or_create_conversation, add_message,
    get_conversation_messages, get_analytics, list_conversations,
    resolve_conversation,
)


# Load KB on startup
knowledge_docs = load_knowledge_base()

# Initialize database on import (safe to call multiple times)
init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global knowledge_docs
    knowledge_docs = load_knowledge_base()
    print(f"[Startup] Loaded {len(knowledge_docs)} KB sections")
    yield


app = FastAPI(title="AIdentify AI Customer Service Agent", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# --- API Models ---

class CustomerMessage(BaseModel):
    message: str
    session_id: str | None = None
    email: str | None = None


class ResolveRequest(BaseModel):
    conversation_id: int


# --- Web Dashboard ---

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


# --- API Endpoints ---

@app.post("/api/chat")
async def chat(req: CustomerMessage):
    """Handle a customer message and return an AI response."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = req.session_id or str(uuid.uuid4())
    
    # Get or create conversation
    conv_id = get_or_create_conversation(session_id, req.email)
    
    # Triage the message
    triage = triage_message(req.message)
    
    # Store customer message
    add_message(
        conv_id, "customer", req.message,
        intent=triage["intent"],
        sentiment=triage["sentiment"],
        priority=triage["priority"],
        needs_escalation=triage["needs_escalation"],
    )
    
    # Retrieve relevant KB docs
    relevant_docs = simple_retrieve(req.message, knowledge_docs, top_k=3)
    
    # Generate AI response
    ai_response = await generate_response(req.message, relevant_docs)
    
    # Store agent response
    add_message(conv_id, "agent", ai_response)
    
    return JSONResponse({
        "response": ai_response,
        "conversation_id": conv_id,
        "session_id": session_id,
        "triage": triage,
        "sources": [
            {"source": d["source"], "section": d["section"]}
            for d in relevant_docs
        ],
    })


@app.get("/api/conversations")
async def get_conversations():
    """List all conversations."""
    convs = list_conversations()
    return {"conversations": convs}


@app.get("/api/conversations/{conversation_id}")
async def get_conversation_detail(conversation_id: int):
    """Get messages in a conversation."""
    messages = get_conversation_messages(conversation_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"messages": messages}


@app.post("/api/conversations/{conversation_id}/resolve")
async def resolve(conversation_id: int):
    """Mark a conversation as resolved."""
    resolve_conversation(conversation_id)
    return {"status": "resolved"}


@app.get("/api/analytics")
async def analytics():
    """Get dashboard analytics."""
    return get_analytics()


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "kb_sections": len(knowledge_docs),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8765, reload=True)

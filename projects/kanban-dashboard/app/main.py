"""
AIdentify Kanban Dashboard - Main FastAPI Application
Production-ready Kanban board for agent swarm management.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth import verify_api_key
from app.database import close_db, init_db
from app.routers import agents, boards, tasks
from app.websocket import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title="AIdentify Kanban Dashboard",
    description="Production-ready Kanban board for AIdentify's agent swarm",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(boards.router)
app.include_router(tasks.router)
app.include_router(agents.router)


# ─── WebSocket Endpoint ───────────────────────────────────────────

@app.websocket("/ws/{board_id}")
async def websocket_endpoint(websocket: WebSocket, board_id: int):
    """WebSocket endpoint for real-time board updates."""
    await manager.connect(websocket, board_id)
    try:
        while True:
            # Keep connection alive, receive pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, board_id)


@app.websocket("/ws")
async def websocket_global(websocket: WebSocket):
    """Global WebSocket endpoint for all-board updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ─── Health & Info ────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "kanban-dashboard", "version": "1.0.0"}


@app.get("/api/config")
async def get_config(auth: dict = Depends(verify_api_key)):
    """Get frontend configuration."""
    return {
        "agents": ["researcher", "writer", "outreach", "social", "owl"],
        "statuses": ["backlog", "in_progress", "review", "done"],
        "priorities": ["low", "medium", "high", "urgent"],
        "agent_colors": {
            "researcher": "#8b5cf6",
            "writer": "#ec4899",
            "outreach": "#f59e0b",
            "social": "#10b981",
            "owl": "#6366f1",
        },
        "priority_colors": {
            "low": "#6b7280",
            "medium": "#3b82f6",
            "high": "#f59e0b",
            "urgent": "#ef4444",
        },
    }


# ─── Static Files ─────────────────────────────────────────────────

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )

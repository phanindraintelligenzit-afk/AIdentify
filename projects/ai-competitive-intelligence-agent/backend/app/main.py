"""AI Competitive Intelligence Agent — Backend

An open-source alternative to Crayon/Klue ($500-2K/mo).
Monitors competitor signals 24/7 and auto-generates battlecards + briefings.
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add app directory to path for absolute imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import close_db, init_db
from api.health import router as health
from api.competitors import router as competitors
from api.signals import router as signals
from api.battlecards import router as battlecards
from api.briefings import router as briefings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="AI Competitive Intelligence Agent",
    description="Monitor competitors, detect signals, generate battlecards — open-source Crayon/Klue alternative.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health, tags=["health"])
app.include_router(competitors, prefix="/api/v1/competitors", tags=["competitors"])
app.include_router(signals, prefix="/api/v1/signals", tags=["signals"])
app.include_router(battlecards, prefix="/api/v1/battlecards", tags=["battlecards"])
app.include_router(briefings, prefix="/api/v1/briefings", tags=["briefings"])

"""AI SOC2 Compliance Agent — Backend

An open-source alternative to Vanta ($1-5K/mo) and Drata.
Automates evidence collection, control mapping, and audit preparation.
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import close_db, init_db
from api.health import router as health
from api.controls import router as controls
from api.evidence import router as evidence
from api.audits import router as audits
from api.policies import router as policies
from api.integrations import router as integrations


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="AI SOC2 Compliance Agent",
    description="Automate SOC2 evidence collection, control mapping, and audit preparation — open-source Vanta/Drata alternative.",
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

app.include_router(health, tags=["health"])
app.include_router(controls, prefix="/api/v1/controls", tags=["controls"])
app.include_router(evidence, prefix="/api/v1/evidence", tags=["evidence"])
app.include_router(audits, prefix="/api/v1/audits", tags=["audits"])
app.include_router(policies, prefix="/api/v1/policies", tags=["policies"])
app.include_router(integrations, prefix="/api/v1/integrations", tags=["integrations"])

"""
DataGuard DSAR Automator - Main FastAPI Application
Automates GDPR/CCPA Data Subject Access Request processing.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from app.core.config import settings
from app.api.v1.router import api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("DataGuard DSAR Automator starting up...")
    yield
    logger.info("DataGuard DSAR Automator shutting down...")


app = FastAPI(
    title="DataGuard DSAR Automator",
    description="Automate GDPR/CCPA Data Subject Access Request processing",
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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - {response.status_code}")
    return response


app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "dsar-automator", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

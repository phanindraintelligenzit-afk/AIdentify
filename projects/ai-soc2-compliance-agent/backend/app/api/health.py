"""Health check endpoint."""

from fastapi import APIRouter

from schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Return service health status."""
    return HealthResponse()

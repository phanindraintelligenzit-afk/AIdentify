"""API v1 router aggregation."""
from fastapi import APIRouter
from app.api.v1 import dsar, discovery, responses, dashboard

api_router = APIRouter()

api_router.include_router(dsar.router, prefix="/dsar", tags=["DSAR Requests"])
api_router.include_router(discovery.router, prefix="/discovery", tags=["Data Discovery"])
api_router.include_router(responses.router, prefix="/responses", tags=["Response Packages"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

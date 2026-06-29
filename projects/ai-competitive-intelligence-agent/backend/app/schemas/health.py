from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "ai-competitive-intelligence-agent"
    version: str = "1.0.0"

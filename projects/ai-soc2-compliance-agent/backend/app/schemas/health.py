from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "ai-soc2-compliance-agent"
    version: str = "1.0.0"

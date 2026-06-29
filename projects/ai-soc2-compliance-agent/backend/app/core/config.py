"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI SOC2 Compliance Agent"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite:///./soc2_agent.db"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Worker settings
    EVIDENCE_SCAN_INTERVAL_HOURS: int = 24
    MAX_EVIDENCE_PER_CONTROL: int = 50

    # LLM settings
    LLM_PROVIDER: str = "openrouter"
    LLM_MODEL: str = "openrouter/owl-alpha"
    LLM_API_KEY: str = ""

    # Integration settings
    SLACK_WEBHOOK_URL: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "AI Competitive Intelligence Agent"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./ci_agent.db"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Worker settings
    SCAN_INTERVAL_MINUTES: int = 60
    MAX_COMPETITORS: int = 50
    MAX_SIGNALS_PER_SCAN: int = 200

    # LLM settings (for battlecard generation)
    LLM_PROVIDER: str = "openrouter"
    LLM_MODEL: str = "openrouter/owl-alpha"
    LLM_API_KEY: str = ""

    # Notification settings
    SLACK_WEBHOOK_URL: str = ""
    EMAIL_SMTP_HOST: str = ""
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

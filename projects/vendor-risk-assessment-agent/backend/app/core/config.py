"""Application configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """App settings loaded from environment variables."""
    APP_NAME: str = "Vendor Risk Assessment Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./vendor_risk.db"
    
    # Security
    SECRET_KEY: str = "dev-secret-change-in-production"
    API_KEY_HEADER: str = "X-API-Key"
    
    # Risk scoring thresholds
    HIGH_RISK_THRESHOLD: int = 75
    MEDIUM_RISK_THRESHOLD: int = 45
    
    # Assessment settings
    AUTO_ESCALATE_DAYS: int = 14
    REMINDER_INTERVAL_DAYS: int = 3
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

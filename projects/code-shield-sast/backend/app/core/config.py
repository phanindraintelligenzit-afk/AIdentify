"""Application configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """App settings loaded from environment."""
    APP_NAME: str = "CodeShield SAST"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./codeshield.db"
    SECRET_KEY: str = "dev-secret-change-in-production"
    
    # Scanning
    MAX_SCAN_DEPTH: int = 50  # max files per scan
    SCAN_TIMEOUT_SECONDS: int = 300
    
    # Severity thresholds
    CRITICAL_CVSS_MIN: float = 9.0
    HIGH_CVSS_MIN: float = 7.0
    MEDIUM_CVSS_MIN: float = 4.0
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

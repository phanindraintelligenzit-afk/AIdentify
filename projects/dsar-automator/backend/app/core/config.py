"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "DataGuard DSAR Automator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./dsar.db"
    
    # Redis / Task Queue
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # DSAR Config
    GDPR_DEADLINE_DAYS: int = 30
    CCPA_DEADLINE_DAYS: int = 45
    AUTO_REMINDER_DAYS_BEFORE: int = 5
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50


settings = Settings()

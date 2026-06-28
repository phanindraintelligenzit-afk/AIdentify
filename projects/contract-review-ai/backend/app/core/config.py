import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Contract Review AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/contract_review",
        validation_alias="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL"
    )
    
    # Celery
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="CELERY_RESULT_BACKEND"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        validation_alias="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30 days
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # AI/LLM
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        validation_alias="OLLAMA_BASE_URL"
    )
    OLLAMA_MODEL: str = Field(
        default="llama3.1:8b",
        validation_alias="OLLAMA_MODEL"
    )
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        validation_alias="OPENAI_API_KEY"
    )
    OPENAI_BASE_URL: Optional[str] = Field(
        default=None,
        validation_alias="OPENAI_BASE_URL"
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4o-mini",
        validation_alias="OPENAI_MODEL"
    )
    USE_LOCAL_LLM: bool = Field(
        default=True,
        validation_alias="USE_LOCAL_LLM"
    )
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".docx", ".doc"]
    
    # Playbooks
    PLAYBOOKS_DIR: str = "./playbooks"
    
    # Celery
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 30 * 60  # 30 minutes
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
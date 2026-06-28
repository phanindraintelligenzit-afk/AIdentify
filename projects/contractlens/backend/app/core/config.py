"""
ContractLens Configuration Settings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "ContractLens"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # Database (using SQLite for simplicity)
    DATABASE_URL: str = "sqlite:///./contractlens.db"
    
    # AI Model settings (using local/transformers)
    MODEL_NAME: str = "microsoft/deberta-v3-base"
    MAX_TOKENS: int = 512
    
    # Analysis settings
    RISK_THRESHOLD_HIGH: float = 0.75
    RISK_THRESHOLD_MEDIUM: float = 0.4
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
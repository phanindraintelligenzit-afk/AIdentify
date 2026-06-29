"""Application configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "ReportGenie AI"
    app_version: str = "1.0.0"
    database_url: str = "sqlite+aiosqlite:///./reportgenie.db"
    debug: bool = True
    cors_origins: list[str] = ["*"]
    report_output_dir: str = "./generated_reports"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

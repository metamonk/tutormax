"""
Configuration settings for the TutorMax API.

Uses pydantic-settings for environment variable management.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables can be set in .env file or system environment.
    """

    # Application settings
    app_name: str = "TutorMax Data Ingestion API"
    app_version: str = "0.1.0"
    debug: bool = False

    # API settings
    api_prefix: str = "/api"
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS settings
    cors_origins: List[str] = [
        "http://localhost:3000",  # React default dev server
        "http://localhost:5173",  # Vite default dev server
        "http://localhost:8080",  # Alternative frontend port
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]

    # Redis settings
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 10

    # Logging settings
    log_level: str = "INFO"

    # Rate limiting (sessions per day target)
    max_sessions_per_day: int = 3000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()

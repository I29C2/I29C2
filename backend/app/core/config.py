# backend/app/core/config.py
from __future__ import annotations

from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "BetBot AI"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://betbot:betbot@localhost:5432/betbot"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "changeme-use-a-long-random-string-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # External APIs
    API_FOOTBALL_KEY: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None

    # Business logic
    VALUE_BET_THRESHOLD: float = 3.0      # Minimum edge percentage to flag as value
    INTEGRITY_RISK_THRESHOLD: float = 70.0  # Score above which value bet is blocked
    FREE_DAILY_PICKS_LIMIT: int = 3

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: object) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        if isinstance(v, list):
            return v
        return v  # let pydantic handle it


settings = Settings()

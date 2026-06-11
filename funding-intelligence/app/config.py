"""Configurare centralizată (pydantic-settings). Toate secretele vin din .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # DB
    database_url: str = "postgresql+psycopg://funding:changeme_local@db:5432/funding"

    # Redis / Celery
    redis_url: str = "redis://redis:6379/0"

    # LLM
    anthropic_api_key: str = ""
    llm_extraction_model: str = "claude-haiku-4-5-20251001"

    # Auth (MVP: token static unic)
    api_static_token: str = "changeme_generate_a_random_token"

    # Storage local
    storage_dir: str = "/app/data/storage"

    # Comportament
    log_level: str = "INFO"
    scraper_rate_limit_seconds: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

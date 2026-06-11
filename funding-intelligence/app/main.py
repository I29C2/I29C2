"""Punctul de intrare FastAPI. Monolit modular: un singur app, module separate."""

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.logging_config import setup_logging

setup_logging()

app = FastAPI(
    title="TeamILabs Funding Intelligence — MVP",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    """Healthcheck de bază (DevOps §5.3). Verificarea DB/Redis se adaugă în deps."""
    return {"status": "ok"}

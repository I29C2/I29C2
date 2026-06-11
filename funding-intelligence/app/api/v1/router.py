"""Agregă rutele v1. Un singur punct de includere în main.py."""

from fastapi import APIRouter

from app.api.v1 import calls, documents, health, validation

api_router = APIRouter()
api_router.include_router(health.router, tags=["ops"])
api_router.include_router(calls.router, prefix="/calls", tags=["calls"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(validation.router, prefix="/validation", tags=["validation"])

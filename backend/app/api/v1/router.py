# backend/app/api/v1/router.py
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import admin, alerts, auth, leagues, matches, predictions, users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(matches.router)
api_router.include_router(leagues.router)
api_router.include_router(predictions.router)
api_router.include_router(users.router)
api_router.include_router(alerts.router)
api_router.include_router(admin.router)

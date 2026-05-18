# backend/app/api/v1/users.py
from __future__ import annotations

from typing import List

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.alert import Alert
from app.models.prediction import Prediction, PredictionStatus
from app.models.user import User
from app.schemas.alert import AlertResponse
from app.schemas.prediction import PredictionResponse
from app.schemas.user import UserResponse, UserUpdate

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me/settings", response_model=UserResponse)
def get_my_settings(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Return the current user's profile and settings."""
    return current_user


@router.put("/me/settings", response_model=UserResponse)
def update_my_settings(
    update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Update the current user's mutable settings."""
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    logger.info("user_settings_updated", user_id=current_user.id, fields=list(update_data.keys()))
    return current_user


@router.get("/me/history", response_model=List[PredictionResponse])
def get_my_prediction_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> list:
    """Return published predictions visible to this user (league favourites filter)."""
    query = db.query(Prediction).filter(
        Prediction.status == PredictionStatus.published
    )

    # If user has favourite leagues, filter to those
    if current_user.favorite_leagues:
        from app.models.match import Match

        query = query.join(Match).filter(
            Match.league_id.in_(current_user.favorite_leagues)
        )

    total = query.count()
    items = (
        query.order_by(Prediction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items


@router.get("/me/alerts", response_model=List[AlertResponse])
def get_my_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> list:
    """Return the current user's alerts."""
    items = (
        db.query(Alert)
        .filter(Alert.user_id == current_user.id)
        .order_by(Alert.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items

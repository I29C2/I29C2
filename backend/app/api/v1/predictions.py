# backend/app/api/v1/predictions.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user, get_db
from app.models.integrity import IntegrityScore
from app.models.match import Match
from app.models.prediction import Prediction, PredictionStatus
from app.models.user import SubscriptionType, User
from app.schemas.prediction import PredictionCreate, PredictionResponse, ValueBetResponse
from app.services.prediction_service import PredictionService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.get("/value-bets", response_model=List[ValueBetResponse])
def get_todays_value_bets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(10, ge=1, le=50),
) -> list:
    """Return today's value bets.

    Free users see at most FREE_DAILY_PICKS_LIMIT results.
    Premium users see all.
    """
    from app.core.config import settings

    svc = PredictionService(db)
    value_bets = svc.get_todays_value_bets()

    # Enforce free tier limit
    if current_user.subscription_type == SubscriptionType.free:
        value_bets = value_bets[: settings.FREE_DAILY_PICKS_LIMIT]
    else:
        value_bets = value_bets[:limit]

    return value_bets


@router.get("/{prediction_id}", response_model=PredictionResponse)
def get_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Prediction:
    pred = db.get(Prediction, prediction_id)
    if not pred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    return pred


@router.post("/analyze", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
def analyze_match(
    body: PredictionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Prediction:
    """Trigger on-demand analysis for a match (premium users only)."""
    if current_user.subscription_type != SubscriptionType.premium and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="On-demand analysis requires a Premium subscription",
        )

    svc = PredictionService(db)
    try:
        prediction = svc.analyze_match(body.match_id, body.market)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("analyze_match_error", match_id=body.match_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed; please try again later",
        )

    return prediction

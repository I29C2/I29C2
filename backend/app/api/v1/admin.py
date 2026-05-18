# backend/app/api/v1/admin.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db
from app.models.match import Match
from app.models.model_registry import ModelRegistry
from app.models.prediction import Prediction, PredictionStatus
from app.models.user import SubscriptionType, User
from app.schemas.prediction import PredictionResponse
from app.schemas.user import UserResponse

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    active_only: bool = Query(False),
) -> list:
    query = db.query(User)
    if active_only:
        query = query.filter(User.is_active == True)  # noqa: E712
    total = query.count()
    items = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items


@router.put("/users/{user_id}/premium", response_model=UserResponse)
def grant_premium(
    user_id: int,
    days: int = Query(30, ge=1, le=3650),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> User:
    """Grant premium subscription to a user."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.subscription_type = SubscriptionType.premium
    user.subscription_expires_at = datetime.now(tz=timezone.utc) + timedelta(days=days)
    db.commit()
    db.refresh(user)
    logger.info("user_granted_premium", user_id=user_id, days=days)
    return user


# ---------------------------------------------------------------------------
# Predictions
# ---------------------------------------------------------------------------


@router.get("/predictions", response_model=List[PredictionResponse])
def list_all_predictions(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
    pred_status: str = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> list:
    query = db.query(Prediction)
    if pred_status:
        try:
            ps = PredictionStatus(pred_status)
            query = query.filter(Prediction.status == ps)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {pred_status}",
            )
    items = (
        query.order_by(Prediction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items


@router.put("/predictions/{prediction_id}/publish", response_model=PredictionResponse)
def publish_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> Prediction:
    pred = db.get(Prediction, prediction_id)
    if not pred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    pred.status = PredictionStatus.published
    db.commit()
    db.refresh(pred)
    return pred


@router.put("/predictions/{prediction_id}/reject", response_model=PredictionResponse)
def reject_prediction(
    prediction_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> Prediction:
    pred = db.get(Prediction, prediction_id)
    if not pred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    pred.status = PredictionStatus.rejected
    db.commit()
    db.refresh(pred)
    return pred


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@router.get("/models", response_model=List[dict])
def list_models(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> list:
    models = db.query(ModelRegistry).order_by(ModelRegistry.created_at.desc()).all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "version": m.version,
            "model_type": m.model_type.value,
            "market": m.market.value,
            "is_active": m.is_active,
            "brier_score": m.brier_score,
            "log_loss": m.log_loss,
            "roi": m.roi,
            "yield_pct": m.yield_pct,
            "training_date": m.training_date,
        }
        for m in models
    ]


# ---------------------------------------------------------------------------
# Jobs / stats
# ---------------------------------------------------------------------------


@router.get("/jobs/status", response_model=dict)
def get_jobs_status(_: User = Depends(get_current_admin_user)) -> dict:
    """Return Celery worker status (placeholder)."""
    try:
        from app.workers.celery_app import celery_app

        inspect = celery_app.control.inspect(timeout=2.0)
        active = inspect.active() or {}
        scheduled = inspect.scheduled() or {}
        return {
            "workers": list(active.keys()),
            "active_tasks": {w: len(t) for w, t in active.items()},
            "scheduled_tasks": {w: len(t) for w, t in scheduled.items()},
        }
    except Exception as exc:
        return {"error": str(exc), "workers": [], "active_tasks": {}, "scheduled_tasks": {}}


@router.get("/stats", response_model=dict)
def platform_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> dict:
    """High-level platform statistics."""
    total_users = db.query(func.count(User.id)).scalar()
    premium_users = (
        db.query(func.count(User.id))
        .filter(User.subscription_type == SubscriptionType.premium)
        .scalar()
    )
    total_predictions = db.query(func.count(Prediction.id)).scalar()
    value_bets = (
        db.query(func.count(Prediction.id))
        .filter(Prediction.is_value_bet == True)  # noqa: E712
        .scalar()
    )
    total_matches = db.query(func.count(Match.id)).scalar()

    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "total_predictions": total_predictions,
        "value_bets_detected": value_bets,
        "total_matches": total_matches,
    }

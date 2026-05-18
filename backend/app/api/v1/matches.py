# backend/app/api/v1/matches.py
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user, get_db
from app.models.match import Match, MatchStatus
from app.models.user import User
from app.schemas.integrity import IntegrityScoreResponse
from app.schemas.match import MatchListResponse, MatchResponse
from app.schemas.prediction import PredictionResponse
from app.services.integrity_service import IntegrityService
from app.services.prediction_service import PredictionService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/matches", tags=["Matches"])


def _get_match_or_404(match_id: int, db: Session) -> Match:
    match = (
        db.query(Match)
        .options(joinedload(Match.league))
        .filter(Match.id == match_id)
        .first()
    )
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    return match


@router.get("/today", response_model=MatchListResponse)
def get_todays_matches(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> MatchListResponse:
    """Return today's matches (UTC) with league info."""
    today_start = datetime.now(tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_end = today_start.replace(hour=23, minute=59, second=59)

    query = (
        db.query(Match)
        .options(joinedload(Match.league))
        .filter(Match.match_date >= today_start, Match.match_date <= today_end)
        .order_by(Match.match_date)
    )

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return MatchListResponse(items=items, total=total, page=page, page_size=page_size)  # type: ignore[arg-type]


@router.get("", response_model=MatchListResponse)
def list_matches(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
    league_id: Optional[int] = Query(None),
    match_date: Optional[date] = Query(None),
    match_status: Optional[MatchStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> MatchListResponse:
    """List matches with optional filters."""
    query = db.query(Match).options(joinedload(Match.league))

    if league_id is not None:
        query = query.filter(Match.league_id == league_id)
    if match_date is not None:
        day_start = datetime(
            match_date.year, match_date.month, match_date.day, tzinfo=timezone.utc
        )
        day_end = day_start.replace(hour=23, minute=59, second=59)
        query = query.filter(Match.match_date >= day_start, Match.match_date <= day_end)
    if match_status is not None:
        query = query.filter(Match.status == match_status)

    query = query.order_by(Match.match_date)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return MatchListResponse(items=items, total=total, page=page, page_size=page_size)  # type: ignore[arg-type]


@router.get("/{match_id}", response_model=MatchResponse)
def get_match(
    match_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Match:
    """Full match detail."""
    return _get_match_or_404(match_id, db)


@router.get("/{match_id}/prediction", response_model=List[PredictionResponse])
def get_match_predictions(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list:
    """Return published predictions for a match.

    Free users are limited to already-stored predictions.
    Premium users also trigger on-demand analysis if none exist.
    """
    match = _get_match_or_404(match_id, db)

    # Return existing published predictions
    from app.models.prediction import Prediction, PredictionStatus

    preds = (
        db.query(Prediction)
        .filter(
            Prediction.match_id == match_id,
            Prediction.status == PredictionStatus.published,
        )
        .all()
    )

    if not preds and current_user.subscription_type.value == "premium":
        # Premium: generate on demand
        svc = PredictionService(db)
        try:
            result = svc.analyze_match(match_id, "1x2")
            if result:
                preds = [result]
        except Exception as exc:
            logger.warning("on_demand_prediction_failed", match_id=match_id, error=str(exc))

    return preds


@router.get("/{match_id}/integrity", response_model=IntegrityScoreResponse)
def get_match_integrity(
    match_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> object:
    """Return (or compute) the integrity score for a match."""
    _get_match_or_404(match_id, db)

    svc = IntegrityService(db)
    score = svc.calculate_integrity_score(match_id)
    return score

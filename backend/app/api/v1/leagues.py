# backend/app/api/v1/leagues.py
from __future__ import annotations

from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user, get_db
from app.models.league import League
from app.models.match import Match
from app.models.user import User
from app.schemas.match import MatchListResponse

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/leagues", tags=["Leagues"])


class LeagueResponse:
    pass  # defined inline via dict below


@router.get("", response_model=List[dict])
def list_leagues(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
    active_only: bool = Query(True),
) -> list:
    """Return all (active) leagues."""
    query = db.query(League)
    if active_only:
        query = query.filter(League.is_active == True)  # noqa: E712
    leagues = query.order_by(League.country, League.name).all()
    return [
        {
            "id": lg.id,
            "name": lg.name,
            "country": lg.country,
            "code": lg.code,
            "competition_type": lg.competition_type.value,
            "is_premium": lg.is_premium,
            "season": lg.season,
            "risk_profile": lg.risk_profile,
        }
        for lg in leagues
    ]


@router.get("/{league_id}/matches", response_model=MatchListResponse)
def get_league_matches(
    league_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> MatchListResponse:
    """Return matches for a specific league."""
    league = db.get(League, league_id)
    if not league:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="League not found")

    query = (
        db.query(Match)
        .options(joinedload(Match.league))
        .filter(Match.league_id == league_id)
        .order_by(Match.match_date.desc())
    )
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return MatchListResponse(items=items, total=total, page=page, page_size=page_size)  # type: ignore[arg-type]

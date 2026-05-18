# backend/app/schemas/match.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class LeagueInfo(BaseModel):
    id: int
    name: str
    country: str
    code: str

    model_config = {"from_attributes": True}


class MatchResponse(BaseModel):
    id: int
    league_id: int
    league: Optional[LeagueInfo] = None
    home_team: str
    away_team: str
    match_date: datetime
    status: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    venue: Optional[str] = None
    round: Optional[str] = None

    home_form: Optional[List[Dict[str, Any]]] = None
    away_form: Optional[List[Dict[str, Any]]] = None
    home_xg: Optional[float] = None
    away_xg: Optional[float] = None
    home_shots_pg: Optional[float] = None
    away_shots_pg: Optional[float] = None
    home_possession: Optional[float] = None
    away_possession: Optional[float] = None
    home_elo: Optional[float] = None
    away_elo: Optional[float] = None
    home_injuries: Optional[List[Dict[str, Any]]] = None
    away_injuries: Optional[List[Dict[str, Any]]] = None
    home_rest_days: Optional[int] = None
    away_rest_days: Optional[int] = None
    h2h_stats: Optional[Dict[str, Any]] = None
    motivation_context: Optional[Dict[str, Any]] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MatchListResponse(BaseModel):
    items: List[MatchResponse]
    total: int
    page: int
    page_size: int

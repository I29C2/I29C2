# backend/app/schemas/prediction.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PredictionCreate(BaseModel):
    match_id: int
    market: str = Field(pattern=r"^(1x2|over_under_25|btts)$")


class PredictionResponse(BaseModel):
    id: int
    match_id: int
    model_id: Optional[int] = None
    market: str
    predicted_outcome: str
    ai_probability: float
    fair_odds: float
    market_odds: float
    edge_percentage: float
    confidence_level: str
    is_value_bet: bool
    value_threshold_used: float
    explanatory_factors: Optional[List[str]] = None
    bankroll_suggestion: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ValueBetResponse(BaseModel):
    prediction: PredictionResponse
    match_home_team: str
    match_away_team: str
    match_date: datetime
    league_name: str
    league_code: str
    integrity_score: Optional[float] = None
    integrity_risk_level: Optional[str] = None

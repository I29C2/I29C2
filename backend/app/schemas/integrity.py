# backend/app/schemas/integrity.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class IntegrityScoreResponse(BaseModel):
    id: int
    match_id: int
    score: float
    risk_level: str
    recommendation: str
    motivation_score: float
    odds_movement_score: float
    financial_instability_score: float
    performance_anomaly_score: float
    market_irregularity_score: float
    contributing_factors: Optional[List[str]] = None
    blocks_value_bet: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

# backend/app/schemas/alert.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AlertCreate(BaseModel):
    alert_type: str
    match_id: Optional[int] = None
    prediction_id: Optional[int] = None
    message: Optional[str] = None  # custom message; auto-generated if omitted


class AlertResponse(BaseModel):
    id: int
    user_id: int
    match_id: Optional[int] = None
    prediction_id: Optional[int] = None
    alert_type: str
    message: str
    is_sent: bool
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}

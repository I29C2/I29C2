# backend/app/models/prediction.py
from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String,
    Enum as SAEnum, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PredictionMarket(str, enum.Enum):
    one_x_two = "1x2"
    over_under_25 = "over_under_25"
    btts = "btts"


class ConfidenceLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    very_high = "very_high"


class PredictionStatus(str, enum.Enum):
    pending = "pending"
    published = "published"
    rejected = "rejected"
    expired = "expired"


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("model_registry.id", ondelete="SET NULL"), nullable=True
    )

    market: Mapped[PredictionMarket] = mapped_column(
        SAEnum(PredictionMarket, name="predictionmarket"), nullable=False
    )

    # Prediction outcome: "home" / "draw" / "away" / "over" / "under" / "yes" / "no"
    predicted_outcome: Mapped[str] = mapped_column(String(20), nullable=False)

    ai_probability: Mapped[float] = mapped_column(Float, nullable=False)
    fair_odds: Mapped[float] = mapped_column(Float, nullable=False)
    market_odds: Mapped[float] = mapped_column(Float, nullable=False)
    edge_percentage: Mapped[float] = mapped_column(Float, nullable=False)

    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        SAEnum(ConfidenceLevel, name="confidencelevel"),
        default=ConfidenceLevel.medium,
        nullable=False,
    )

    is_value_bet: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    value_threshold_used: Mapped[float] = mapped_column(Float, nullable=False, default=3.0)

    # ["Home team has won 4 of last 5 at home", ...]
    explanatory_factors: Mapped[Optional[List]] = mapped_column(JSONB, nullable=True)

    bankroll_suggestion: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    status: Mapped[PredictionStatus] = mapped_column(
        SAEnum(PredictionStatus, name="predictionstatus"),
        default=PredictionStatus.pending,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    match: Mapped["Match"] = relationship("Match", back_populates="predictions")  # noqa: F821
    model: Mapped[Optional["ModelRegistry"]] = relationship(  # noqa: F821
        "ModelRegistry", back_populates="predictions"
    )
    alerts: Mapped[List["Alert"]] = relationship(  # noqa: F821
        "Alert", back_populates="prediction"
    )

    def __repr__(self) -> str:
        return (
            f"<Prediction id={self.id} match_id={self.match_id} "
            f"market={self.market!r} outcome={self.predicted_outcome!r} "
            f"edge={self.edge_percentage:.1f}%>"
        )

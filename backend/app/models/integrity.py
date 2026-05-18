# backend/app/models/integrity.py
from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer,
    Enum as SAEnum, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Recommendation(str, enum.Enum):
    normal = "normal"
    reduced_stake = "reduced_stake"
    caution = "caution"
    no_bet = "no_bet"


class IntegrityScore(Base):
    __tablename__ = "integrity_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("matches.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100
    risk_level: Mapped[RiskLevel] = mapped_column(
        SAEnum(RiskLevel, name="risklevel"), nullable=False
    )
    recommendation: Mapped[Recommendation] = mapped_column(
        SAEnum(Recommendation, name="recommendation"), nullable=False
    )

    # Component scores (0-100 each)
    motivation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    odds_movement_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    financial_instability_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    performance_anomaly_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    market_irregularity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # List of human-readable risk factors
    contributing_factors: Mapped[Optional[List]] = mapped_column(JSONB, nullable=True)

    blocks_value_bet: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    match: Mapped["Match"] = relationship("Match", back_populates="integrity_score")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<IntegrityScore id={self.id} match_id={self.match_id} "
            f"score={self.score:.1f} risk={self.risk_level!r}>"
        )

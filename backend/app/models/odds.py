# backend/app/models/odds.py
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String,
    Enum as SAEnum, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OddsMarket(str, enum.Enum):
    one_x_two = "1x2"
    over_under_25 = "over_under_25"
    btts = "btts"


class Odds(Base):
    __tablename__ = "odds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True
    )

    bookmaker: Mapped[str] = mapped_column(String(100), nullable=False)

    market: Mapped[OddsMarket] = mapped_column(
        SAEnum(OddsMarket, name="oddsmarket"), nullable=False
    )

    # 1X2 odds
    home_odds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    draw_odds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    away_odds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Over/Under 2.5
    over_odds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    under_odds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Both Teams To Score
    yes_odds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    no_odds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Opening line (for movement detection)
    opening_home: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    opening_draw: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    opening_away: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Anomaly flags
    movement_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    volume_spike: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    match: Mapped["Match"] = relationship("Match", back_populates="odds_records")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Odds id={self.id} match_id={self.match_id} "
            f"bookmaker={self.bookmaker!r} market={self.market!r}>"
        )

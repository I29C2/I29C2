# backend/app/models/match.py
from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String,
    Enum as SAEnum, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MatchStatus(str, enum.Enum):
    scheduled = "scheduled"
    live = "live"
    finished = "finished"
    postponed = "postponed"


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    league_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("leagues.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    home_team: Mapped[str] = mapped_column(String(200), nullable=False)
    away_team: Mapped[str] = mapped_column(String(200), nullable=False)
    match_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    status: Mapped[MatchStatus] = mapped_column(
        SAEnum(MatchStatus, name="matchstatus"),
        default=MatchStatus.scheduled,
        nullable=False,
        index=True,
    )

    home_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    venue: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    round: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # matchday / round

    # Form: list of dicts, e.g. [{"result": "W", "goals_for": 2, "goals_against": 1}, ...]
    home_form: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    away_form: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Statistical features
    home_xg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    away_xg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_shots_pg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    away_shots_pg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_possession: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    away_possession: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    home_elo: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    away_elo: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    home_injuries: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    away_injuries: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    home_rest_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_rest_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Head-to-head: {"home_wins": int, "away_wins": int, "draws": int, "avg_goals": float}
    h2h_stats: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Context: {"title_race": bool, "relegation_battle": bool, "cup_distraction": bool, ...}
    motivation_context: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    external_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True, index=True
    )

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
    league: Mapped["League"] = relationship("League", back_populates="matches")  # noqa: F821
    odds_records: Mapped[List["Odds"]] = relationship(  # noqa: F821
        "Odds", back_populates="match", cascade="all, delete-orphan"
    )
    predictions: Mapped[List["Prediction"]] = relationship(  # noqa: F821
        "Prediction", back_populates="match", cascade="all, delete-orphan"
    )
    integrity_score: Mapped[Optional["IntegrityScore"]] = relationship(  # noqa: F821
        "IntegrityScore", back_populates="match", uselist=False, cascade="all, delete-orphan"
    )
    alerts: Mapped[List["Alert"]] = relationship(  # noqa: F821
        "Alert", back_populates="match"
    )

    def __repr__(self) -> str:
        return (
            f"<Match id={self.id} "
            f"{self.home_team!r} vs {self.away_team!r} "
            f"@ {self.match_date.date()}>"
        )

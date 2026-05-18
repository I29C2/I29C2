# backend/app/models/league.py
from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CompetitionType(str, enum.Enum):
    domestic = "domestic"
    european = "european"


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)  # e.g. "PL", "CL"

    competition_type: Mapped[CompetitionType] = mapped_column(
        SAEnum(CompetitionType, name="competitiontype"),
        default=CompetitionType.domestic,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    season: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # e.g. "2024/25"

    # Historical integrity risk profile (0.0 = clean, 1.0 = high risk)
    risk_profile: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    matches: Mapped[List["Match"]] = relationship(  # noqa: F821
        "Match", back_populates="league"
    )

    def __repr__(self) -> str:
        return f"<League id={self.id} code={self.code!r} name={self.name!r}>"

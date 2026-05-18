# backend/app/models/alert.py
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text,
    Enum as SAEnum, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AlertType(str, enum.Enum):
    value_bet = "value_bet"
    daily_summary = "daily_summary"
    risk_warning = "risk_warning"
    custom = "custom"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    match_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("matches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    prediction_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("predictions.id", ondelete="SET NULL"), nullable=True
    )

    alert_type: Mapped[AlertType] = mapped_column(
        SAEnum(AlertType, name="alerttype"), nullable=False, index=True
    )

    message: Mapped[str] = mapped_column(Text, nullable=False)

    is_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="alerts")  # noqa: F821
    match: Mapped[Optional["Match"]] = relationship("Match", back_populates="alerts")  # noqa: F821
    prediction: Mapped[Optional["Prediction"]] = relationship(  # noqa: F821
        "Prediction", back_populates="alerts"
    )

    def __repr__(self) -> str:
        return (
            f"<Alert id={self.id} user_id={self.user_id} "
            f"type={self.alert_type!r} sent={self.is_sent}>"
        )

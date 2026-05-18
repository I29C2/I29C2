# backend/app/models/model_registry.py
from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, DateTime, Float, Integer, String,
    Enum as SAEnum, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ModelType(str, enum.Enum):
    logistic = "logistic"
    xgboost = "xgboost"
    poisson = "poisson"
    ensemble = "ensemble"


class ModelMarket(str, enum.Enum):
    one_x_two = "1x2"
    over_under_25 = "over_under_25"
    btts = "btts"
    all_markets = "all_markets"


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)

    model_type: Mapped[ModelType] = mapped_column(
        SAEnum(ModelType, name="modeltype"), nullable=False
    )
    market: Mapped[ModelMarket] = mapped_column(
        SAEnum(ModelMarket, name="modelmarket"), nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Evaluation metrics
    brier_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    log_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    calibration_error: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    roi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    yield_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    training_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    validation_period: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    model_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    predictions: Mapped[List["Prediction"]] = relationship(  # noqa: F821
        "Prediction", back_populates="model"
    )

    def __repr__(self) -> str:
        return (
            f"<ModelRegistry id={self.id} name={self.name!r} "
            f"version={self.version!r} active={self.is_active}>"
        )

# backend/app/ml/model_manager.py
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import numpy as np
import structlog

from app.ml.models.base_model import BaseModel
from app.ml.models.logistic_model import LogisticRegressionModel
from app.ml.models.poisson_model import PoissonGoalModel
from app.ml.models.xgboost_model import XGBoostModel

logger = structlog.get_logger(__name__)


# Confidence levels mirrored from the ORM enum (avoid circular import)
class _ConfidenceLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ModelManager:
    """Singleton that manages loading and ensembling of ML models.

    Usage::

        manager = ModelManager.get_instance()
        probs = manager.ensemble_predict(features, "1x2")
    """

    _instance: Optional["ModelManager"] = None

    def __init__(self) -> None:
        self._models: Dict[str, BaseModel] = {}
        self._loaded: bool = False

    @classmethod
    def get_instance(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.load_active_models()
        return cls._instance

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_active_models(self) -> Dict[str, BaseModel]:
        """Attempt to load persisted models from disk.  On failure, the
        manager falls back to default (untrained) model instances so that
        the API never crashes.
        """
        model_dir = os.environ.get("MODEL_DIR", "/app/ml_models")
        model_specs = {
            "logistic": LogisticRegressionModel(),
            "xgboost": XGBoostModel(),
            "poisson": PoissonGoalModel(),
        }

        for name, model in model_specs.items():
            path = os.path.join(model_dir, f"{name}_model.joblib")
            if os.path.exists(path):
                try:
                    model.load(path)
                    logger.info("model_loaded", model_name=name, path=path)
                except Exception as exc:
                    logger.warning("model_load_failed", model_name=name, error=str(exc))
            else:
                logger.debug("model_file_not_found", model_name=name, path=path)
            self._models[name] = model

        self._loaded = True
        return self._models

    def get_model(self, model_type: str, market: str = "1x2") -> BaseModel:
        """Return the model for *model_type*.

        Falls back to the logistic or default model if not found.
        """
        model = self._models.get(model_type)
        if model is not None:
            return model
        return self._get_default_model()

    # ------------------------------------------------------------------
    # Ensemble prediction
    # ------------------------------------------------------------------

    def ensemble_predict(
        self, match_features: np.ndarray, market: str
    ) -> Dict[str, Any]:
        """Average predictions from all available models.

        Args:
            match_features: 1-D numpy feature vector.
            market: One of "1x2", "over_under_25", "btts".

        Returns:
            dict with:
            - "probabilities": dict mapping outcome label → probability
            - "confidence": ConfidenceLevel string
            - "predicted_outcome": highest-probability outcome label
        """
        predictions = []

        for name, model in self._models.items():
            try:
                if market == "1x2":
                    pred = model.predict_proba(match_features)
                elif market == "over_under_25":
                    pred = model.predict_over_under(match_features)
                elif market == "btts":
                    pred = model.predict_btts(match_features)
                else:
                    pred = model.predict_proba(match_features)
                predictions.append(pred)
            except Exception as exc:
                logger.warning("model_predict_failed", model=name, error=str(exc))

        if not predictions:
            predictions.append(self._get_default_model().predict_proba(match_features))

        # Average probabilities across models
        keys = list(predictions[0].keys())
        averaged: Dict[str, float] = {}
        for k in keys:
            averaged[k] = float(np.mean([p.get(k, 0.0) for p in predictions]))

        # Re-normalise
        total = sum(averaged.values())
        if total > 0:
            averaged = {k: v / total for k, v in averaged.items()}

        predicted_outcome = max(averaged, key=averaged.get)  # type: ignore[arg-type]
        confidence = self._confidence_from_probabilities(averaged)

        return {
            "probabilities": averaged,
            "confidence": confidence,
            "predicted_outcome": predicted_outcome,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _confidence_from_probabilities(self, probs: Dict[str, float]) -> str:
        """Map max-probability to a confidence level."""
        max_p = max(probs.values())
        if max_p >= 0.70:
            return _ConfidenceLevel.VERY_HIGH
        if max_p >= 0.55:
            return _ConfidenceLevel.HIGH
        if max_p >= 0.42:
            return _ConfidenceLevel.MEDIUM
        return _ConfidenceLevel.LOW

    def _get_default_model(self) -> BaseModel:
        """Return a fallback logistic model (untrained, uses defaults)."""
        return self._models.get("logistic") or LogisticRegressionModel()

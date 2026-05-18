# backend/app/ml/models/base_model.py
from __future__ import annotations

import abc
from typing import Any, Dict

import numpy as np


class BaseModel(abc.ABC):
    """Abstract base class for all BetBot prediction models."""

    @property
    @abc.abstractmethod
    def is_trained(self) -> bool:
        """Return True if the model has been fitted."""

    # ------------------------------------------------------------------
    # Prediction interface
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def predict_proba(self, features: np.ndarray) -> Dict[str, float]:
        """Return 1X2 outcome probabilities.

        Returns:
            dict with keys "home", "draw", "away" summing to ≈1.0
        """

    @abc.abstractmethod
    def predict_over_under(
        self, features: np.ndarray, threshold: float = 2.5
    ) -> Dict[str, float]:
        """Return over/under probabilities.

        Returns:
            dict with keys "over", "under" summing to ≈1.0
        """

    @abc.abstractmethod
    def predict_btts(self, features: np.ndarray) -> Dict[str, float]:
        """Return both-teams-to-score probabilities.

        Returns:
            dict with keys "yes", "no" summing to ≈1.0
        """

    # ------------------------------------------------------------------
    # Training interface
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray) -> "BaseModel":
        """Fit the model on training data.

        Args:
            X: Feature matrix of shape (n_samples, n_features).
            y: Target labels.

        Returns:
            self (for chaining).
        """

    @abc.abstractmethod
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Compute evaluation metrics on held-out data.

        Returns:
            dict with metric names and float values.
        """

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def save(self, path: str) -> None:
        """Serialize the model to *path*."""

    @abc.abstractmethod
    def load(self, path: str) -> "BaseModel":
        """Deserialize the model from *path* and return self."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _default_1x2(self) -> Dict[str, float]:
        """Neutral prior: slight home advantage."""
        return {"home": 0.40, "draw": 0.28, "away": 0.32}

    def _default_ou(self) -> Dict[str, float]:
        return {"over": 0.52, "under": 0.48}

    def _default_btts(self) -> Dict[str, float]:
        return {"yes": 0.50, "no": 0.50}

    def _clip_proba(self, p: float, eps: float = 1e-4) -> float:
        """Clip probability to [eps, 1-eps]."""
        return float(np.clip(p, eps, 1.0 - eps))

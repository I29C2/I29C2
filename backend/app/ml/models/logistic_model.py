# backend/app/ml/models/logistic_model.py
from __future__ import annotations

import os
from typing import Dict, Optional

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from app.ml.models.base_model import BaseModel


class LogisticRegressionModel(BaseModel):
    """Calibrated logistic regression model for football prediction.

    Maintains three separate classifiers:
    - ``_clf_1x2``   → 1X2 (home / draw / away)
    - ``_clf_ou``    → Over/Under 2.5 goals (over / under)
    - ``_clf_btts``  → Both Teams To Score (yes / no)
    """

    def __init__(self) -> None:
        self._clf_1x2: Optional[CalibratedClassifierCV] = None
        self._clf_ou: Optional[CalibratedClassifierCV] = None
        self._clf_btts: Optional[CalibratedClassifierCV] = None
        self._scaler: StandardScaler = StandardScaler()
        self._trained: bool = False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_trained(self) -> bool:
        return self._trained

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict_proba(self, features: np.ndarray) -> Dict[str, float]:
        if not self._trained or self._clf_1x2 is None:
            return self._default_1x2()
        X = self._scaler.transform(features.reshape(1, -1))
        proba = self._clf_1x2.predict_proba(X)[0]
        classes = list(self._clf_1x2.classes_)
        result: Dict[str, float] = {}
        label_map = {0: "home", 1: "draw", 2: "away"}
        for i, cls in enumerate(classes):
            result[label_map.get(cls, str(cls))] = self._clip_proba(proba[i])
        # Ensure all keys present
        for k in ("home", "draw", "away"):
            result.setdefault(k, 1 / 3)
        return result

    def predict_over_under(
        self, features: np.ndarray, threshold: float = 2.5
    ) -> Dict[str, float]:
        if not self._trained or self._clf_ou is None:
            return self._default_ou()
        X = self._scaler.transform(features.reshape(1, -1))
        proba = self._clf_ou.predict_proba(X)[0]
        classes = list(self._clf_ou.classes_)
        over_idx = classes.index(1) if 1 in classes else 0
        over_p = self._clip_proba(proba[over_idx])
        return {"over": over_p, "under": self._clip_proba(1.0 - over_p)}

    def predict_btts(self, features: np.ndarray) -> Dict[str, float]:
        if not self._trained or self._clf_btts is None:
            return self._default_btts()
        X = self._scaler.transform(features.reshape(1, -1))
        proba = self._clf_btts.predict_proba(X)[0]
        classes = list(self._clf_btts.classes_)
        yes_idx = classes.index(1) if 1 in classes else 0
        yes_p = self._clip_proba(proba[yes_idx])
        return {"yes": yes_p, "no": self._clip_proba(1.0 - yes_p)}

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, X: np.ndarray, y: np.ndarray) -> "LogisticRegressionModel":
        """Train three binary/multi-class classifiers.

        *y* is expected to be a 2-D array with columns:
        [outcome_1x2, over_under, btts]
        where:
        - outcome_1x2: 0=home, 1=draw, 2=away
        - over_under:  0=under, 1=over
        - btts:        0=no, 1=yes
        """
        if y.ndim == 1:
            # Assume single-column → 1x2 only
            y_1x2 = y
            y_ou = np.random.randint(0, 2, size=len(y))
            y_btts = np.random.randint(0, 2, size=len(y))
        else:
            y_1x2 = y[:, 0]
            y_ou = y[:, 1]
            y_btts = y[:, 2]

        self._scaler.fit(X)
        X_scaled = self._scaler.transform(X)

        base_lr = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
            multi_class="multinomial",
            solver="lbfgs",
        )
        self._clf_1x2 = CalibratedClassifierCV(base_lr, cv=3, method="isotonic")
        self._clf_1x2.fit(X_scaled, y_1x2)

        base_ou = LogisticRegression(max_iter=500, class_weight="balanced", random_state=42)
        self._clf_ou = CalibratedClassifierCV(base_ou, cv=3, method="isotonic")
        self._clf_ou.fit(X_scaled, y_ou)

        base_btts = LogisticRegression(max_iter=500, class_weight="balanced", random_state=42)
        self._clf_btts = CalibratedClassifierCV(base_btts, cv=3, method="isotonic")
        self._clf_btts.fit(X_scaled, y_btts)

        self._trained = True
        return self

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        from sklearn.metrics import brier_score_loss, log_loss

        if not self._trained:
            return {}
        X_scaled = self._scaler.transform(X)
        y_1x2 = y[:, 0] if y.ndim > 1 else y
        proba = self._clf_1x2.predict_proba(X_scaled)
        # One-vs-rest brier score (average)
        n_classes = proba.shape[1]
        brier = float(
            np.mean(
                [
                    brier_score_loss((y_1x2 == c).astype(int), proba[:, i])
                    for i, c in enumerate(self._clf_1x2.classes_)
                ]
            )
        )
        ll = float(log_loss(y_1x2, proba))
        return {"brier_score": brier, "log_loss": ll}

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(
            {
                "clf_1x2": self._clf_1x2,
                "clf_ou": self._clf_ou,
                "clf_btts": self._clf_btts,
                "scaler": self._scaler,
                "trained": self._trained,
            },
            path,
        )

    def load(self, path: str) -> "LogisticRegressionModel":
        data = joblib.load(path)
        self._clf_1x2 = data["clf_1x2"]
        self._clf_ou = data["clf_ou"]
        self._clf_btts = data["clf_btts"]
        self._scaler = data["scaler"]
        self._trained = data.get("trained", True)
        return self

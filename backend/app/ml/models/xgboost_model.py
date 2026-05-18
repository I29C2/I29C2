# backend/app/ml/models/xgboost_model.py
from __future__ import annotations

import os
from typing import Dict, List, Optional

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from app.ml.models.base_model import BaseModel


class XGBoostModel(BaseModel):
    """XGBoost-backed prediction model with probability calibration."""

    def __init__(self) -> None:
        self._clf_1x2: Optional[CalibratedClassifierCV] = None
        self._clf_ou: Optional[CalibratedClassifierCV] = None
        self._clf_btts: Optional[CalibratedClassifierCV] = None
        self._scaler: StandardScaler = StandardScaler()
        self._trained: bool = False
        self._feature_importances: Optional[np.ndarray] = None

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
        label_map = {0: "home", 1: "draw", 2: "away"}
        result = {label_map.get(c, str(c)): self._clip_proba(p) for c, p in zip(classes, proba)}
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

    def _make_xgb(self, n_classes: int = 3) -> XGBClassifier:
        return XGBClassifier(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="mlogloss" if n_classes > 2 else "logloss",
            random_state=42,
            verbosity=0,
            objective="multi:softprob" if n_classes > 2 else "binary:logistic",
            num_class=n_classes if n_classes > 2 else None,
        )

    def train(self, X: np.ndarray, y: np.ndarray) -> "XGBoostModel":
        if y.ndim == 1:
            y_1x2 = y
            y_ou = np.random.randint(0, 2, size=len(y))
            y_btts = np.random.randint(0, 2, size=len(y))
        else:
            y_1x2 = y[:, 0]
            y_ou = y[:, 1]
            y_btts = y[:, 2]

        self._scaler.fit(X)
        X_scaled = self._scaler.transform(X)

        n_classes = len(np.unique(y_1x2))
        xgb_1x2 = self._make_xgb(n_classes=n_classes)
        self._clf_1x2 = CalibratedClassifierCV(xgb_1x2, cv=3, method="isotonic")
        self._clf_1x2.fit(X_scaled, y_1x2)

        # Store feature importances from the first uncalibrated estimator
        try:
            self._feature_importances = (
                self._clf_1x2.calibrated_classifiers_[0].estimator.feature_importances_
            )
        except Exception:
            self._feature_importances = None

        xgb_ou = self._make_xgb(n_classes=2)
        self._clf_ou = CalibratedClassifierCV(xgb_ou, cv=3, method="isotonic")
        self._clf_ou.fit(X_scaled, y_ou)

        xgb_btts = self._make_xgb(n_classes=2)
        self._clf_btts = CalibratedClassifierCV(xgb_btts, cv=3, method="isotonic")
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

    def get_feature_importances(self) -> Optional[np.ndarray]:
        """Return feature importances from the 1X2 XGBoost model (if trained)."""
        return self._feature_importances

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
                "feature_importances": self._feature_importances,
            },
            path,
        )

    def load(self, path: str) -> "XGBoostModel":
        data = joblib.load(path)
        self._clf_1x2 = data["clf_1x2"]
        self._clf_ou = data["clf_ou"]
        self._clf_btts = data["clf_btts"]
        self._scaler = data["scaler"]
        self._trained = data.get("trained", True)
        self._feature_importances = data.get("feature_importances")
        return self

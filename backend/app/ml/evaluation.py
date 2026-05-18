# backend/app/ml/evaluation.py
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss
from sklearn.metrics import log_loss as sklearn_log_loss


class ModelEvaluator:
    """Offline evaluation metrics for probabilistic football models."""

    @staticmethod
    def brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
        """Mean Brier score across all outcome classes (one-vs-rest).

        Args:
            y_true: Integer class labels, shape (n,).
            y_prob: Probability matrix, shape (n, n_classes).

        Returns:
            Float brier score (lower is better, 0.0 is perfect).
        """
        n_classes = y_prob.shape[1] if y_prob.ndim > 1 else 2
        scores = []
        if y_prob.ndim == 1:
            scores.append(float(brier_score_loss(y_true, y_prob)))
        else:
            classes = np.unique(y_true)
            for i, c in enumerate(range(n_classes)):
                binary = (y_true == c).astype(int)
                if i < y_prob.shape[1]:
                    scores.append(float(brier_score_loss(binary, y_prob[:, i])))
        return float(np.mean(scores)) if scores else 0.0

    @staticmethod
    def log_loss_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
        """Compute log-loss (cross-entropy).

        Args:
            y_true: Integer class labels.
            y_prob: Probability matrix or vector.

        Returns:
            Float log-loss (lower is better).
        """
        return float(sklearn_log_loss(y_true, y_prob))

    @staticmethod
    def calibration_error(
        y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10
    ) -> float:
        """Expected Calibration Error (ECE) for binary predictions.

        For multi-class *y_prob*, uses the probability of the predicted class.

        Args:
            y_true: Integer binary labels (or one class extracted).
            y_prob: Probability vector for the positive class, shape (n,).
            n_bins: Number of bins.

        Returns:
            Float ECE in [0, 1] (lower is better).
        """
        if y_prob.ndim > 1:
            # Use max-probability (confidence) for calibration
            y_conf = y_prob.max(axis=1)
            y_bin = (y_true == y_prob.argmax(axis=1)).astype(int)
        else:
            y_conf = y_prob
            y_bin = y_true

        fraction_positives, mean_predicted = calibration_curve(
            y_bin, y_conf, n_bins=n_bins, strategy="uniform"
        )
        bin_sizes: List[int] = []
        bins = np.linspace(0, 1, n_bins + 1)
        for i in range(n_bins):
            mask = (y_conf >= bins[i]) & (y_conf < bins[i + 1])
            bin_sizes.append(int(mask.sum()))

        ece = 0.0
        n = len(y_bin)
        for i, (frac, pred) in enumerate(zip(fraction_positives, mean_predicted)):
            ece += (bin_sizes[i] / n) * abs(frac - pred)
        return float(ece)

    @staticmethod
    def roi(
        predictions: List[Dict[str, Any]],
        odds: List[float],
        outcomes: List[bool],
    ) -> float:
        """Return on Investment for a set of flat-stake bets.

        Args:
            predictions: Unused (kept for interface symmetry).
            odds: Decimal odds for each bet.
            outcomes: True if the bet won.

        Returns:
            ROI as a fraction (e.g. 0.05 = 5%).
        """
        if not odds:
            return 0.0
        stake = 1.0
        total_staked = stake * len(odds)
        total_return = sum(
            (o - 1.0) * stake if won else -stake
            for o, won in zip(odds, outcomes)
        )
        return float(total_return / total_staked) if total_staked else 0.0

    @staticmethod
    def yield_percentage(roi: float, n_bets: int) -> float:
        """Yield percentage = ROI expressed as percent, per bet.

        Args:
            roi: ROI fraction.
            n_bets: Number of bets (unused but kept for semantic clarity).

        Returns:
            yield as a percentage (e.g. 5.0 for 5%).
        """
        return float(roi * 100.0)

    def generate_report(
        self, model: Any, X_test: np.ndarray, y_test: np.ndarray
    ) -> Dict[str, Any]:
        """Compute full evaluation report for a model on test data.

        Args:
            model: A BaseModel-compatible object.
            X_test: Feature matrix.
            y_test: True labels.

        Returns:
            dict with brier_score, log_loss, calibration_error.
        """
        probas = np.array([list(model.predict_proba(x).values()) for x in X_test])
        y_1x2 = y_test[:, 0] if y_test.ndim > 1 else y_test

        return {
            "brier_score": self.brier_score(y_1x2, probas),
            "log_loss": self.log_loss_score(y_1x2, probas),
            "calibration_error": self.calibration_error(y_1x2, probas),
            "n_samples": len(y_1x2),
        }

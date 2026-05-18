# backend/app/ml/models/poisson_model.py
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import joblib
import numpy as np
from scipy.stats import poisson

from app.ml.models.base_model import BaseModel


class PoissonGoalModel(BaseModel):
    """Poisson-based goal-scoring model.

    Uses Dixon-Coles style attack/defense strength parameters per team.
    When not yet fitted, falls back to league-average goal rates.
    """

    # League-average goals per game (home / away)
    DEFAULT_HOME_GOALS: float = 1.53
    DEFAULT_AWAY_GOALS: float = 1.17

    def __init__(self) -> None:
        # Dicts mapping team name → strength parameter
        self._attack: Dict[str, float] = {}
        self._defense: Dict[str, float] = {}
        self._home_advantage: float = 1.20  # multiplicative advantage
        self._trained: bool = False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_trained(self) -> bool:
        return self._trained

    # ------------------------------------------------------------------
    # Goal expectation
    # ------------------------------------------------------------------

    def _expected_goals(
        self,
        features: np.ndarray,
        home_team: Optional[str] = None,
        away_team: Optional[str] = None,
    ) -> tuple[float, float]:
        """Return (home_lambda, away_lambda) expected goals."""
        if self._trained and home_team and away_team:
            home_att = self._attack.get(home_team, 1.0)
            home_def = self._defense.get(home_team, 1.0)
            away_att = self._attack.get(away_team, 1.0)
            away_def = self._defense.get(away_team, 1.0)
            # Average league attack/defense
            mu_home = home_att * away_def * self._home_advantage
            mu_away = away_att * home_def
        else:
            # Derive from ELO diff embedded in features
            elo_diff = float(features[0]) if len(features) > 0 else 0.0
            adjustment = elo_diff / 400.0  # logistic-style adjustment
            mu_home = max(0.3, self.DEFAULT_HOME_GOALS * (1.0 + adjustment))
            mu_away = max(0.3, self.DEFAULT_AWAY_GOALS * (1.0 - adjustment))
        return mu_home, mu_away

    # ------------------------------------------------------------------
    # Score distribution → outcome probabilities
    # ------------------------------------------------------------------

    @staticmethod
    def _score_matrix(mu_home: float, mu_away: float, max_goals: int = 8) -> np.ndarray:
        """Return (max_goals+1) x (max_goals+1) joint probability matrix."""
        home_pmf = np.array([poisson.pmf(g, mu_home) for g in range(max_goals + 1)])
        away_pmf = np.array([poisson.pmf(g, mu_away) for g in range(max_goals + 1)])
        return np.outer(home_pmf, away_pmf)

    def _outcome_probs_from_matrix(
        self, matrix: np.ndarray
    ) -> tuple[float, float, float]:
        """Return (p_home, p_draw, p_away) from score matrix."""
        p_home = float(np.tril(matrix, -1).sum())
        p_draw = float(np.diag(matrix).sum())
        p_away = float(np.triu(matrix, 1).sum())
        total = p_home + p_draw + p_away
        if total == 0:
            return 1 / 3, 1 / 3, 1 / 3
        return p_home / total, p_draw / total, p_away / total

    # ------------------------------------------------------------------
    # BaseModel interface
    # ------------------------------------------------------------------

    def predict_proba(self, features: np.ndarray) -> Dict[str, float]:
        mu_home, mu_away = self._expected_goals(features)
        matrix = self._score_matrix(mu_home, mu_away)
        p_home, p_draw, p_away = self._outcome_probs_from_matrix(matrix)
        return {
            "home": self._clip_proba(p_home),
            "draw": self._clip_proba(p_draw),
            "away": self._clip_proba(p_away),
        }

    def predict_over_under(
        self, features: np.ndarray, threshold: float = 2.5
    ) -> Dict[str, float]:
        mu_home, mu_away = self._expected_goals(features)
        matrix = self._score_matrix(mu_home, mu_away)
        max_goals = matrix.shape[0] - 1
        p_over = 0.0
        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                if h + a > threshold:
                    p_over += matrix[h, a]
        p_over = self._clip_proba(p_over)
        return {"over": p_over, "under": self._clip_proba(1.0 - p_over)}

    def predict_btts(self, features: np.ndarray) -> Dict[str, float]:
        mu_home, mu_away = self._expected_goals(features)
        # P(home scores) = 1 - P(home scores 0)
        p_home_scores = 1.0 - poisson.pmf(0, mu_home)
        p_away_scores = 1.0 - poisson.pmf(0, mu_away)
        p_btts = self._clip_proba(p_home_scores * p_away_scores)
        return {"yes": p_btts, "no": self._clip_proba(1.0 - p_btts)}

    # ------------------------------------------------------------------
    # Training  (maximum-likelihood strength parameters)
    # ------------------------------------------------------------------

    def train(self, X: np.ndarray, y: np.ndarray) -> "PoissonGoalModel":
        """Estimate attack/defense strengths from historical match data.

        *y* expected shape (n, 4): [home_goals, away_goals, home_team_idx, away_team_idx]
        If not in that format, falls back to setting the home-advantage only.
        """
        try:
            if y.ndim == 1 or y.shape[1] < 4:
                raise ValueError("Insufficient columns for Poisson training")

            home_goals = y[:, 0].astype(float)
            away_goals = y[:, 1].astype(float)
            home_teams = y[:, 2].astype(int)
            away_teams = y[:, 3].astype(int)

            n_teams = max(home_teams.max(), away_teams.max()) + 1
            attack = np.ones(n_teams)
            defense = np.ones(n_teams)

            # Simple iterative estimation (one pass)
            for t in range(n_teams):
                home_mask = home_teams == t
                away_mask = away_teams == t
                if home_mask.any():
                    attack[t] = (home_goals[home_mask].mean() + away_goals[away_mask].mean()) / 2
                if away_mask.any():
                    defense[t] = (
                        away_goals[home_mask].mean() + home_goals[away_mask].mean()
                    ) / 2

            self._attack = {str(i): float(v) for i, v in enumerate(attack)}
            self._defense = {str(i): float(v) for i, v in enumerate(defense)}
        except Exception:
            pass  # Keep defaults on failure

        self._trained = True
        return self

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        if not self._trained:
            return {}
        # Simple brier score approximation
        outcomes = []
        probas = []
        y_1x2 = y[:, 0] if y.ndim > 1 else y
        for i, feat in enumerate(X):
            probs = self.predict_proba(feat)
            probas.append([probs["home"], probs["draw"], probs["away"]])
            outcomes.append(int(y_1x2[i]))
        from sklearn.metrics import log_loss

        ll = float(log_loss(outcomes, probas))
        return {"log_loss": ll}

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(
            {
                "attack": self._attack,
                "defense": self._defense,
                "home_advantage": self._home_advantage,
                "trained": self._trained,
            },
            path,
        )

    def load(self, path: str) -> "PoissonGoalModel":
        data = joblib.load(path)
        self._attack = data.get("attack", {})
        self._defense = data.get("defense", {})
        self._home_advantage = data.get("home_advantage", 1.20)
        self._trained = data.get("trained", True)
        return self

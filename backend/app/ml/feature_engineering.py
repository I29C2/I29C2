# backend/app/ml/feature_engineering.py
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np


class FeatureEngineer:
    """Extract and normalise features from a match record for ML inference."""

    FEATURE_NAMES: List[str] = [
        "home_elo_diff",
        "form_score_diff",
        "xg_diff",
        "xga_diff",
        "shots_diff",
        "possession_diff",
        "rest_days_diff",
        "h2h_advantage",
        "home_advantage",
        "league_risk_profile",
    ]

    # Rough scale factors used for normalisation (mean ≈ 0, std ≈ 1)
    _SCALES: Dict[str, float] = {
        "home_elo_diff": 200.0,
        "form_score_diff": 3.0,
        "xg_diff": 1.5,
        "xga_diff": 1.5,
        "shots_diff": 5.0,
        "possession_diff": 15.0,
        "rest_days_diff": 5.0,
        "h2h_advantage": 1.0,
        "home_advantage": 1.0,
        "league_risk_profile": 1.0,
    }

    def get_feature_names(self) -> List[str]:
        return list(self.FEATURE_NAMES)

    def extract_features(self, match: Any) -> np.ndarray:
        """Extract a 1-D feature vector from a Match ORM object or dict.

        Falls back to neutral (0.0) for any missing attribute so that
        inference never crashes, even without fully-populated match data.
        """
        def _get(obj: Any, *keys: str, default: float = 0.0) -> float:
            for key in keys:
                try:
                    val = obj[key] if isinstance(obj, dict) else getattr(obj, key, None)
                    if val is not None:
                        return float(val)
                except (KeyError, TypeError):
                    pass
            return default

        # ELO difference
        home_elo = _get(match, "home_elo", default=1500.0)
        away_elo = _get(match, "away_elo", default=1500.0)
        home_elo_diff = home_elo - away_elo

        # Form score: W=3, D=1, L=0 over last 5 matches
        home_form = _get(match, "home_form", default=None)
        away_form = _get(match, "away_form", default=None)
        # home_form attribute may be a list of dicts
        home_form_list = (
            match["home_form"]
            if isinstance(match, dict)
            else getattr(match, "home_form", None)
        ) or []
        away_form_list = (
            match["away_form"]
            if isinstance(match, dict)
            else getattr(match, "away_form", None)
        ) or []
        home_pts = sum(
            3 if r.get("result") == "W" else (1 if r.get("result") == "D" else 0)
            for r in (home_form_list or [])
        )
        away_pts = sum(
            3 if r.get("result") == "W" else (1 if r.get("result") == "D" else 0)
            for r in (away_form_list or [])
        )
        form_score_diff = float(home_pts - away_pts)

        # xG
        xg_diff = _get(match, "home_xg", default=1.3) - _get(match, "away_xg", default=1.1)
        # For xGA we invert: lower xGA is better for the team
        home_xga = _get(match, "away_xg", default=1.1)  # xGA home ≈ xG conceded = away xG
        away_xga = _get(match, "home_xg", default=1.3)
        xga_diff = away_xga - home_xga  # positive = home team allows fewer

        shots_diff = _get(match, "home_shots_pg", default=12.0) - _get(
            match, "away_shots_pg", default=11.0
        )
        possession_diff = _get(match, "home_possession", default=50.0) - _get(
            match, "away_possession", default=50.0
        )
        rest_days_diff = _get(match, "home_rest_days", default=7) - _get(
            match, "away_rest_days", default=7
        )

        # H2H: compute advantage from dict
        h2h = (
            match.get("h2h_stats") if isinstance(match, dict) else getattr(match, "h2h_stats", None)
        ) or {}
        h2h_home_wins = float(h2h.get("home_wins", 0))
        h2h_away_wins = float(h2h.get("away_wins", 0))
        h2h_total = h2h_home_wins + h2h_away_wins + float(h2h.get("draws", 0))
        h2h_advantage = (h2h_home_wins - h2h_away_wins) / max(h2h_total, 1.0)

        home_advantage: float = 0.1  # constant home-field advantage prior

        # League risk profile (0–1)
        league = (
            match.get("league") if isinstance(match, dict) else getattr(match, "league", None)
        )
        league_risk = float(getattr(league, "risk_profile", 0.1) if league else 0.1)

        features = np.array(
            [
                home_elo_diff,
                form_score_diff,
                xg_diff,
                xga_diff,
                shots_diff,
                possession_diff,
                rest_days_diff,
                h2h_advantage,
                home_advantage,
                league_risk,
            ],
            dtype=np.float64,
        )
        return features

    def normalize_features(self, features: np.ndarray) -> np.ndarray:
        """Divide each feature by its approximate scale factor."""
        scales = np.array(
            [self._SCALES[name] for name in self.FEATURE_NAMES], dtype=np.float64
        )
        # Avoid division by zero
        scales = np.where(scales == 0, 1.0, scales)
        return features / scales

# backend/app/services/value_bet_service.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple


class ValueBetService:
    """Utility service for value-bet detection and Kelly sizing."""

    # ------------------------------------------------------------------
    # Core value-bet logic
    # ------------------------------------------------------------------

    def calculate_fair_odds(self, probability: float) -> float:
        """Convert an AI probability into fair (no-vig) decimal odds.

        Args:
            probability: Float in (0, 1).

        Returns:
            Fair decimal odds.  Returns 9999.0 if probability ≈ 0.
        """
        if probability <= 0.0:
            return 9999.0
        return round(1.0 / probability, 3)

    def calculate_edge(self, ai_prob: float, market_odds: float) -> float:
        """Calculate the edge percentage of a bet.

        Edge = (AI probability × market odds - 1) × 100

        A positive edge means the bet has positive expected value.

        Args:
            ai_prob: AI-estimated win probability.
            market_odds: Decimal odds offered by the bookmaker.

        Returns:
            Edge as a percentage (e.g. 5.2 means +5.2% EV).
        """
        return round((ai_prob * market_odds - 1.0) * 100.0, 4)

    def detect_value_bet(
        self,
        ai_prob: float,
        market_odds: float,
        threshold: float = 3.0,
    ) -> Tuple[bool, float]:
        """Determine if a bet qualifies as a value bet.

        Args:
            ai_prob: AI win probability.
            market_odds: Decimal market odds.
            threshold: Minimum edge percentage to qualify.

        Returns:
            Tuple of (is_value_bet, edge_percentage).
        """
        edge = self.calculate_edge(ai_prob, market_odds)
        return edge >= threshold, edge

    def filter_by_threshold(
        self,
        predictions: List[Dict[str, Any]],
        threshold: float,
    ) -> List[Dict[str, Any]]:
        """Filter a list of prediction dicts by edge threshold.

        Each dict must have "edge_percentage" key.

        Args:
            predictions: List of prediction result dicts.
            threshold: Minimum edge percentage.

        Returns:
            Filtered list sorted by edge descending.
        """
        filtered = [p for p in predictions if p.get("edge_percentage", 0.0) >= threshold]
        return sorted(filtered, key=lambda p: p.get("edge_percentage", 0.0), reverse=True)

    def kelly_criterion(self, edge: float, odds: float) -> float:
        """Compute the Kelly fraction for optimal bet sizing.

        Full Kelly:  f = (bp - q) / b
        where:
        - b = odds - 1 (net decimal profit per unit)
        - p = AI probability of winning
        - q = 1 - p

        We return the *fractional* Kelly (25% Kelly) to be conservative.

        Args:
            edge: Edge percentage (e.g. 5.2 for 5.2%).
            odds: Decimal odds.

        Returns:
            Suggested fraction of bankroll to stake (0.0–0.25 range).
        """
        if odds <= 1.0:
            return 0.0
        b = odds - 1.0
        p = (edge / 100.0 + 1.0) / odds  # recover implied probability from edge
        q = 1.0 - p
        full_kelly = (b * p - q) / b
        fractional_kelly = max(0.0, full_kelly * 0.25)  # 25% Kelly
        return round(min(fractional_kelly, 0.10), 4)  # cap at 10% of bankroll

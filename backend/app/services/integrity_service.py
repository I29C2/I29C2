# backend/app/services/integrity_service.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.integrity import IntegrityScore, Recommendation, RiskLevel
from app.models.match import Match
from app.models.odds import Odds

logger = structlog.get_logger(__name__)

# Component weights (must sum to 1.0)
_WEIGHTS: Dict[str, float] = {
    "motivation": 0.20,
    "odds_movement": 0.30,
    "financial": 0.15,
    "performance_anomaly": 0.20,
    "market_irregularity": 0.15,
}


class IntegrityService:
    """Compute multi-factor integrity scores for matches."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate_integrity_score(self, match_id: int) -> IntegrityScore:
        """Return (or recompute) an IntegrityScore for a match.

        If a score already exists in the DB it is refreshed in-place.
        """
        match: Optional[Match] = self.db.get(Match, match_id)
        if not match:
            raise ValueError(f"Match {match_id} not found")

        mot_score = self._score_motivation(match)
        odds_score = self._score_odds_movement(match_id)
        fin_score = self._score_financial_instability(match.home_team) + self._score_financial_instability(
            match.away_team
        )
        fin_score = min(fin_score / 2.0, 100.0)  # average of both teams
        perf_score = self._score_performance_anomaly(match)
        mkt_score = self._score_market_irregularity(match_id)

        component_scores: Dict[str, float] = {
            "motivation": mot_score,
            "odds_movement": odds_score,
            "financial": fin_score,
            "performance_anomaly": perf_score,
            "market_irregularity": mkt_score,
        }

        aggregate = self._aggregate_score(component_scores)
        risk_level = self._determine_risk_level(aggregate)
        recommendation = self._determine_recommendation(aggregate, risk_level)
        factors = self._get_contributing_factors(component_scores)
        blocks = self.should_block_value_bet(aggregate, settings.INTEGRITY_RISK_THRESHOLD)

        # Upsert
        existing: Optional[IntegrityScore] = match.integrity_score
        if existing:
            score_obj = existing
        else:
            score_obj = IntegrityScore(match_id=match_id)

        score_obj.score = aggregate
        score_obj.risk_level = risk_level
        score_obj.recommendation = recommendation
        score_obj.motivation_score = mot_score
        score_obj.odds_movement_score = odds_score
        score_obj.financial_instability_score = fin_score
        score_obj.performance_anomaly_score = perf_score
        score_obj.market_irregularity_score = mkt_score
        score_obj.contributing_factors = factors
        score_obj.blocks_value_bet = blocks
        score_obj.updated_at = datetime.now(tz=timezone.utc)

        self.db.add(score_obj)
        self.db.commit()
        self.db.refresh(score_obj)

        logger.info(
            "integrity_score_calculated",
            match_id=match_id,
            score=aggregate,
            risk_level=risk_level.value,
        )
        return score_obj

    # ------------------------------------------------------------------
    # Component scorers (return 0-100, higher = more risky)
    # ------------------------------------------------------------------

    def _score_motivation(self, match: Match) -> float:
        """Low motivation = higher integrity risk (garbage-time matches)."""
        ctx: Dict[str, Any] = match.motivation_context or {}
        risk = 0.0

        if ctx.get("title_race"):
            risk -= 10.0  # high motivation → lower risk
        if ctx.get("relegation_battle"):
            risk -= 10.0
        if ctx.get("cup_distraction"):
            risk += 15.0
        if ctx.get("already_relegated"):
            risk += 25.0
        if ctx.get("already_champions"):
            risk += 20.0
        if ctx.get("nothing_to_play_for"):
            risk += 30.0

        # Round info: last rounds of season are sometimes suspect
        rnd = match.round or ""
        if "38" in rnd or "Final" in rnd or "Last" in rnd.lower():
            risk += 10.0

        return max(0.0, min(100.0, 20.0 + risk))  # baseline 20

    def _score_odds_movement(self, match_id: int) -> float:
        """Large line movements or volume spikes → higher risk."""
        odds_records: List[Odds] = (
            self.db.query(Odds).filter(Odds.match_id == match_id).all()
        )
        if not odds_records:
            return 20.0  # no data → moderate baseline

        flagged = sum(1 for o in odds_records if o.movement_flag or o.volume_spike)
        total = len(odds_records)
        flag_ratio = flagged / total if total else 0.0

        # Check magnitude of movement
        large_movements = 0
        for o in odds_records:
            if o.home_odds and o.opening_home:
                movement = abs(o.home_odds - o.opening_home) / max(o.opening_home, 0.01)
                if movement > 0.10:  # > 10% movement
                    large_movements += 1

        movement_score = min(100.0, flag_ratio * 60.0 + (large_movements / max(total, 1)) * 40.0)
        return max(0.0, movement_score)

    def _score_financial_instability(self, team_name: str) -> float:
        """Return a financial-instability risk score for a team.

        In production this would query an external financial database.
        Here we use a deterministic hash-based pseudo-score as a placeholder
        that is consistent per team name.
        """
        # Deterministic pseudo-score from team name hash
        seed = abs(hash(team_name)) % 100
        # Most teams are financially stable; bias toward low scores
        base_score = seed * 0.3  # 0–30 range
        return float(base_score)

    def _score_performance_anomaly(self, match: Match) -> float:
        """Detect unusual form patterns that may indicate match-fixing."""
        risk = 0.0

        home_form: List[Dict[str, Any]] = match.home_form or []
        away_form: List[Dict[str, Any]] = match.away_form or []

        def _recent_losses(form: List[Dict]) -> int:
            return sum(1 for r in form[-5:] if r.get("result") == "L")

        def _unusual_goals(form: List[Dict]) -> bool:
            """Check for suspiciously high number of goals conceded."""
            total_conceded = sum(r.get("goals_against", 0) for r in form[-5:])
            return total_conceded > 12  # >12 goals conceded in last 5

        if _recent_losses(home_form) >= 5:
            risk += 20.0
        if _recent_losses(away_form) >= 5:
            risk += 20.0
        if home_form and _unusual_goals(home_form):
            risk += 15.0
        if away_form and _unusual_goals(away_form):
            risk += 15.0

        # ELO mismatch vs form disparity
        if match.home_elo and match.away_elo:
            elo_diff = abs(match.home_elo - match.away_elo)
            home_pts = sum(
                3 if r.get("result") == "W" else (1 if r.get("result") == "D" else 0)
                for r in home_form[-5:]
            )
            away_pts = sum(
                3 if r.get("result") == "W" else (1 if r.get("result") == "D" else 0)
                for r in away_form[-5:]
            )
            # Strong ELO favourite with terrible recent form
            if elo_diff > 150 and (home_pts < 3 or away_pts < 3):
                risk += 10.0

        return max(0.0, min(100.0, 10.0 + risk))

    def _score_market_irregularity(self, match_id: int) -> float:
        """Assess overall market irregularity from odds records."""
        odds_records: List[Odds] = (
            self.db.query(Odds).filter(Odds.match_id == match_id).all()
        )
        if not odds_records:
            return 15.0

        # Check for unusually low overround (may indicate liquidity manipulation)
        irregular_count = 0
        for o in odds_records:
            if o.home_odds and o.draw_odds and o.away_odds:
                overround = (1 / o.home_odds + 1 / o.draw_odds + 1 / o.away_odds)
                if overround < 0.95 or overround > 1.15:  # abnormal vig
                    irregular_count += 1

        irregularity = min(100.0, irregular_count * 15.0)
        return max(0.0, irregularity)

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    def _aggregate_score(self, component_scores: Dict[str, float]) -> float:
        """Weighted average of component scores."""
        total = sum(
            _WEIGHTS[name] * score for name, score in component_scores.items()
        )
        return round(min(100.0, max(0.0, total)), 2)

    def _determine_risk_level(self, score: float) -> RiskLevel:
        if score >= 75:
            return RiskLevel.critical
        if score >= 50:
            return RiskLevel.high
        if score >= 30:
            return RiskLevel.medium
        return RiskLevel.low

    def _determine_recommendation(
        self, score: float, risk_level: RiskLevel
    ) -> Recommendation:
        if risk_level == RiskLevel.critical:
            return Recommendation.no_bet
        if risk_level == RiskLevel.high:
            return Recommendation.caution
        if risk_level == RiskLevel.medium:
            return Recommendation.reduced_stake
        return Recommendation.normal

    def _get_contributing_factors(
        self, component_scores: Dict[str, float]
    ) -> List[str]:
        factors: List[str] = []
        if component_scores["motivation"] >= 40:
            factors.append("Low team motivation detected (possible nothing-to-play-for scenario)")
        if component_scores["odds_movement"] >= 40:
            factors.append("Significant odds movement or volume spike observed")
        if component_scores["financial"] >= 40:
            factors.append("Financial instability concerns for one or both clubs")
        if component_scores["performance_anomaly"] >= 40:
            factors.append("Recent performance anomaly inconsistent with team quality")
        if component_scores["market_irregularity"] >= 40:
            factors.append("Unusual market structure or overround detected")
        return factors

    def should_block_value_bet(
        self, integrity_score: float, threshold: float = 70.0
    ) -> bool:
        """Return True if the integrity score is too high to recommend a value bet."""
        return integrity_score >= threshold

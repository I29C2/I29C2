# backend/app/services/prediction_service.py
from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ml.feature_engineering import FeatureEngineer
from app.ml.model_manager import ModelManager
from app.models.integrity import IntegrityScore
from app.models.match import Match, MatchStatus
from app.models.odds import Odds, OddsMarket
from app.models.prediction import (
    ConfidenceLevel,
    Prediction,
    PredictionMarket,
    PredictionStatus,
)
from app.services.integrity_service import IntegrityService
from app.services.value_bet_service import ValueBetService

logger = structlog.get_logger(__name__)


_MARKET_TO_ENUM: Dict[str, PredictionMarket] = {
    "1x2": PredictionMarket.one_x_two,
    "over_under_25": PredictionMarket.over_under_25,
    "btts": PredictionMarket.btts,
}

_MARKET_TO_ODDS_ENUM: Dict[str, OddsMarket] = {
    "1x2": OddsMarket.one_x_two,
    "over_under_25": OddsMarket.over_under_25,
    "btts": OddsMarket.btts,
}


class PredictionService:
    """Orchestrates the full prediction pipeline for a single match."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self._fe = FeatureEngineer()
        self._manager = ModelManager.get_instance()
        self._vbs = ValueBetService()
        self._integrity_svc = IntegrityService(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_match(self, match_id: int, market: str) -> Prediction:
        """Full prediction pipeline for a single match + market.

        1. Load match data
        2. Extract & normalise features
        3. Ensemble ML prediction
        4. Value-bet detection
        5. Integrity check
        6. Persist and return Prediction ORM object
        """
        market = market.lower()
        if market not in _MARKET_TO_ENUM:
            raise ValueError(f"Unsupported market: {market}. Choose from {list(_MARKET_TO_ENUM)}")

        match: Optional[Match] = (
            self.db.query(Match)
            .filter(Match.id == match_id)
            .first()
        )
        if not match:
            raise ValueError(f"Match {match_id} not found")

        # Extract features
        features = self._fe.extract_features(match)
        norm_features = self._fe.normalize_features(features)

        # Ensemble prediction
        ensemble_result = self._manager.ensemble_predict(norm_features, market)
        probabilities: Dict[str, float] = ensemble_result["probabilities"]
        confidence_str: str = ensemble_result["confidence"]
        predicted_outcome: str = ensemble_result["predicted_outcome"]

        ai_probability = probabilities[predicted_outcome]
        fair_odds = self._vbs.calculate_fair_odds(ai_probability)

        # Get the best available market odds
        market_odds = self._get_best_market_odds(match_id, market, predicted_outcome)

        # Value-bet detection
        is_value, edge_pct = self._vbs.detect_value_bet(
            ai_probability,
            market_odds,
            threshold=settings.VALUE_BET_THRESHOLD,
        )

        # Integrity score (compute or retrieve)
        integrity_score_obj: Optional[IntegrityScore] = None
        try:
            integrity_score_obj = self._integrity_svc.calculate_integrity_score(match_id)
        except Exception as exc:
            logger.warning("integrity_score_failed", match_id=match_id, error=str(exc))

        # Block value bet if integrity risk is too high
        if is_value and integrity_score_obj and integrity_score_obj.blocks_value_bet:
            is_value = False
            logger.info(
                "value_bet_blocked_by_integrity",
                match_id=match_id,
                integrity_score=integrity_score_obj.score,
            )

        # Generate explanations
        integrity_score_val = integrity_score_obj.score if integrity_score_obj else 20.0
        explanations = self._generate_explanations(match, probabilities, features)
        bankroll = self._calculate_bankroll_suggestion(
            confidence_str, edge_pct, integrity_score_val
        )

        confidence_enum = ConfidenceLevel(confidence_str)
        prediction = Prediction(
            match_id=match_id,
            market=_MARKET_TO_ENUM[market],
            predicted_outcome=predicted_outcome,
            ai_probability=round(ai_probability, 4),
            fair_odds=round(fair_odds, 3),
            market_odds=round(market_odds, 3),
            edge_percentage=round(edge_pct, 2),
            confidence_level=confidence_enum,
            is_value_bet=is_value,
            value_threshold_used=settings.VALUE_BET_THRESHOLD,
            explanatory_factors=explanations,
            bankroll_suggestion=bankroll,
            status=PredictionStatus.pending,
        )
        self.db.add(prediction)
        self.db.commit()
        self.db.refresh(prediction)

        logger.info(
            "prediction_created",
            prediction_id=prediction.id,
            match_id=match_id,
            market=market,
            outcome=predicted_outcome,
            edge=edge_pct,
            is_value=is_value,
        )
        return prediction

    def get_todays_value_bets(self) -> List[Dict[str, Any]]:
        """Return today's published value bets enriched with match info."""
        from app.schemas.prediction import ValueBetResponse
        today_start = datetime.now(tz=timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_end = today_start.replace(hour=23, minute=59, second=59)

        preds = (
            self.db.query(Prediction)
            .join(Match)
            .filter(
                Prediction.is_value_bet == True,  # noqa: E712
                Prediction.status == PredictionStatus.published,
                Match.match_date >= today_start,
                Match.match_date <= today_end,
            )
            .order_by(Prediction.edge_percentage.desc())
            .all()
        )

        results = []
        for pred in preds:
            match = pred.match
            league = match.league if match else None
            integrity = match.integrity_score if match else None
            results.append(
                {
                    "prediction": pred,
                    "match_home_team": match.home_team if match else "",
                    "match_away_team": match.away_team if match else "",
                    "match_date": match.match_date if match else None,
                    "league_name": league.name if league else "",
                    "league_code": league.code if league else "",
                    "integrity_score": integrity.score if integrity else None,
                    "integrity_risk_level": integrity.risk_level.value if integrity else None,
                }
            )
        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_best_market_odds(
        self, match_id: int, market: str, outcome: str
    ) -> float:
        """Return the best (highest) bookmaker odds for a given outcome."""
        odds_records: List[Odds] = (
            self.db.query(Odds)
            .filter(
                Odds.match_id == match_id,
                Odds.market == _MARKET_TO_ODDS_ENUM.get(market, OddsMarket.one_x_two),
            )
            .all()
        )

        best: float = 0.0
        outcome_field_map: Dict[str, str] = {
            "home": "home_odds",
            "draw": "draw_odds",
            "away": "away_odds",
            "over": "over_odds",
            "under": "under_odds",
            "yes": "yes_odds",
            "no": "no_odds",
        }
        field = outcome_field_map.get(outcome, "home_odds")

        for o in odds_records:
            val = getattr(o, field, None)
            if val and val > best:
                best = val

        # Fallback: generate a plausible odds value
        if best <= 1.0:
            fallback_map = {
                "home": 2.10,
                "draw": 3.40,
                "away": 3.50,
                "over": 1.85,
                "under": 1.95,
                "yes": 1.75,
                "no": 2.05,
            }
            best = fallback_map.get(outcome, 2.0)

        return best

    def _generate_explanations(
        self,
        match: Match,
        probabilities: Dict[str, float],
        features: Any,
    ) -> List[str]:
        """Generate up to 5 human-readable explanatory factors."""
        explanations: List[str] = []

        home_form: List[Dict] = match.home_form or []
        away_form: List[Dict] = match.away_form or []

        # Form analysis
        home_wins = sum(1 for r in home_form[-5:] if r.get("result") == "W")
        away_wins = sum(1 for r in away_form[-5:] if r.get("result") == "W")
        if home_wins >= 3:
            explanations.append(
                f"{match.home_team} in strong home form ({home_wins}W in last 5)"
            )
        if away_wins >= 3:
            explanations.append(
                f"{match.away_team} in strong away form ({away_wins}W in last 5)"
            )

        # xG
        if match.home_xg and match.away_xg:
            if match.home_xg > match.away_xg + 0.4:
                explanations.append(
                    f"{match.home_team} xG advantage ({match.home_xg:.2f} vs {match.away_xg:.2f})"
                )
            elif match.away_xg > match.home_xg + 0.4:
                explanations.append(
                    f"{match.away_team} xG advantage ({match.away_xg:.2f} vs {match.home_xg:.2f})"
                )

        # ELO
        if match.home_elo and match.away_elo:
            elo_diff = match.home_elo - match.away_elo
            if abs(elo_diff) > 100:
                stronger = match.home_team if elo_diff > 0 else match.away_team
                explanations.append(
                    f"{stronger} has significant ELO rating advantage ({abs(elo_diff):.0f} pts)"
                )

        # H2H
        h2h = match.h2h_stats or {}
        hw = h2h.get("home_wins", 0)
        aw = h2h.get("away_wins", 0)
        if hw > aw + 3:
            explanations.append(
                f"Historical H2H heavily favours {match.home_team} ({hw}W vs {aw}W)"
            )

        # Home advantage catch-all
        if not explanations:
            explanations.append("Home advantage factored into probability estimate")

        return explanations[:5]

    def _calculate_bankroll_suggestion(
        self, confidence: str, edge_pct: float, integrity_score: float
    ) -> str:
        """Return a text bankroll management suggestion."""
        # Reduce stake recommendation if integrity risk is elevated
        if integrity_score >= 70:
            return "Avoid – high integrity risk"
        if integrity_score >= 50:
            return "1% of bankroll – caution advised"

        kelly = self._vbs.kelly_criterion(edge_pct, 2.0)
        pct = round(kelly * 100, 1)

        confidence_map = {
            ConfidenceLevel.very_high.value: "3–5%",
            ConfidenceLevel.high.value: "2–3%",
            ConfidenceLevel.medium.value: "1–2%",
            ConfidenceLevel.low.value: "0.5–1%",
        }
        suggestion_range = confidence_map.get(confidence, "1–2%")
        return f"{suggestion_range} of bankroll (Kelly suggests {pct}%)"

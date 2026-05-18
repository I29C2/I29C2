# backend/app/services/data_ingestion_service.py
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Sample data generators (used when no external API key is configured)
# ---------------------------------------------------------------------------

_TEAMS: Dict[str, List[str]] = {
    "PL": [
        "Manchester City", "Arsenal", "Liverpool", "Chelsea",
        "Tottenham", "Manchester United", "Newcastle", "West Ham",
        "Aston Villa", "Brighton",
    ],
    "LL": [
        "Real Madrid", "Barcelona", "Atletico Madrid", "Sevilla",
        "Villarreal", "Real Sociedad", "Athletic Club", "Betis",
        "Valencia", "Getafe",
    ],
    "BL": [
        "Bayern Munich", "Borussia Dortmund", "RB Leipzig", "Bayer Leverkusen",
        "Union Berlin", "Freiburg", "Hoffenheim", "Mainz",
        "Wolfsburg", "Eintracht Frankfurt",
    ],
    "SA": [
        "Napoli", "Inter Milan", "AC Milan", "Juventus",
        "Roma", "Lazio", "Atalanta", "Fiorentina",
        "Torino", "Bologna",
    ],
    "L1": [
        "PSG", "Marseille", "Lyon", "Lille",
        "Monaco", "Nice", "Rennes", "Lens",
        "Montpellier", "Strasbourg",
    ],
}


def _random_form(n: int = 5) -> List[Dict[str, Any]]:
    results = random.choices(["W", "D", "L"], weights=[0.4, 0.25, 0.35], k=n)
    form = []
    for r in results:
        gf = random.randint(0, 3)
        ga = random.randint(0, 3)
        if r == "W":
            ga = max(0, gf - 1)
        elif r == "L":
            gf = max(0, ga - 1)
        form.append({"result": r, "goals_for": gf, "goals_against": ga})
    return form


class DataIngestionService:
    """Fetches and enriches match data.

    Uses live API-Football data when ``API_FOOTBALL_KEY`` is set, otherwise
    generates plausible synthetic data for development and testing.
    """

    def __init__(self) -> None:
        from app.core.config import settings

        self._api_key: Optional[str] = settings.API_FOOTBALL_KEY

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def fetch_todays_matches(self) -> List[Dict[str, Any]]:
        """Return a list of today's match dicts.

        In production, calls the API-Football endpoint.
        Without API key, generates sample data.
        """
        if self._api_key:
            return self._fetch_from_api()
        return self._generate_sample_matches()

    def fetch_odds(self, match_id: int) -> Dict[str, Any]:
        """Return odds for a match (synthetic when no API key)."""
        if self._api_key:
            return self._fetch_odds_from_api(match_id)
        return self._generate_sample_odds(match_id)

    def fetch_team_stats(self, team_name: str) -> Dict[str, Any]:
        """Return team statistics (synthetic when no API key)."""
        if self._api_key:
            return self._fetch_team_stats_from_api(team_name)
        return self._generate_sample_team_stats(team_name)

    def enrich_match(self, match: Any) -> Any:
        """Populate missing xG, ELO, form, and context fields on a match object."""
        import math

        rng = random.Random(
            abs(hash(f"{getattr(match, 'home_team', '')}_{getattr(match, 'away_team', '')}"))
        )

        if not getattr(match, "home_xg", None):
            match.home_xg = round(rng.uniform(0.8, 2.5), 2)
        if not getattr(match, "away_xg", None):
            match.away_xg = round(rng.uniform(0.6, 2.0), 2)
        if not getattr(match, "home_shots_pg", None):
            match.home_shots_pg = round(rng.uniform(8.0, 18.0), 1)
        if not getattr(match, "away_shots_pg", None):
            match.away_shots_pg = round(rng.uniform(7.0, 15.0), 1)
        if not getattr(match, "home_possession", None):
            base = rng.uniform(40.0, 65.0)
            match.home_possession = round(base, 1)
            match.away_possession = round(100.0 - base, 1)
        if not getattr(match, "home_elo", None):
            match.home_elo = round(rng.uniform(1300.0, 1800.0), 1)
            match.away_elo = round(rng.uniform(1300.0, 1800.0), 1)
        if not getattr(match, "home_form", None):
            match.home_form = _random_form()
            match.away_form = _random_form()
        if not getattr(match, "home_rest_days", None):
            match.home_rest_days = rng.randint(3, 14)
            match.away_rest_days = rng.randint(3, 14)
        if not getattr(match, "h2h_stats", None):
            total = rng.randint(5, 20)
            hw = rng.randint(0, total)
            remaining = total - hw
            aw = rng.randint(0, remaining)
            draws = remaining - aw
            match.h2h_stats = {
                "home_wins": hw,
                "away_wins": aw,
                "draws": draws,
                "avg_goals": round(rng.uniform(1.5, 3.5), 2),
            }
        return match

    # ------------------------------------------------------------------
    # Live API calls (stubs – implement with httpx when API key present)
    # ------------------------------------------------------------------

    def _fetch_from_api(self) -> List[Dict[str, Any]]:
        """Call API-Football for today's fixtures."""
        logger.info("api_fetch_not_implemented_using_sample")
        return self._generate_sample_matches()

    def _fetch_odds_from_api(self, match_id: int) -> Dict[str, Any]:
        logger.info("api_odds_fetch_not_implemented")
        return self._generate_sample_odds(match_id)

    def _fetch_team_stats_from_api(self, team_name: str) -> Dict[str, Any]:
        logger.info("api_team_stats_not_implemented")
        return self._generate_sample_team_stats(team_name)

    # ------------------------------------------------------------------
    # Sample data generators
    # ------------------------------------------------------------------

    def _generate_sample_matches(self) -> List[Dict[str, Any]]:
        today = datetime.now(tz=timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        matches = []
        for league_code, teams in _TEAMS.items():
            shuffled = teams[:]
            random.shuffle(shuffled)
            for i in range(0, min(6, len(shuffled)), 2):
                kick_off = today + timedelta(hours=random.choice([13, 15, 17, 19, 20]))
                matches.append(
                    {
                        "external_id": f"{league_code}_{shuffled[i]}_{shuffled[i+1]}_{today.date()}",
                        "league_code": league_code,
                        "home_team": shuffled[i],
                        "away_team": shuffled[i + 1],
                        "match_date": kick_off,
                        "venue": f"{shuffled[i]} Stadium",
                        "round": f"Round {random.randint(1, 38)}",
                    }
                )
        return matches

    def _generate_sample_odds(self, match_id: int) -> Dict[str, Any]:
        rng = random.Random(match_id)
        home_odds = round(rng.uniform(1.5, 4.0), 2)
        draw_odds = round(rng.uniform(2.8, 3.8), 2)
        away_odds = round(rng.uniform(1.8, 5.0), 2)
        return {
            "bookmaker": "Bet365",
            "home_odds": home_odds,
            "draw_odds": draw_odds,
            "away_odds": away_odds,
            "over_odds": round(rng.uniform(1.7, 2.1), 2),
            "under_odds": round(rng.uniform(1.7, 2.1), 2),
            "yes_odds": round(rng.uniform(1.6, 2.0), 2),
            "no_odds": round(rng.uniform(1.8, 2.3), 2),
            "opening_home": home_odds,
            "opening_draw": draw_odds,
            "opening_away": away_odds,
            "movement_flag": rng.random() < 0.05,
            "volume_spike": rng.random() < 0.03,
        }

    def _generate_sample_team_stats(self, team_name: str) -> Dict[str, Any]:
        rng = random.Random(abs(hash(team_name)))
        return {
            "team": team_name,
            "elo": round(rng.uniform(1300.0, 1800.0), 1),
            "form": _random_form(),
            "xg_per_game": round(rng.uniform(0.8, 2.5), 2),
            "xga_per_game": round(rng.uniform(0.8, 2.0), 2),
            "shots_per_game": round(rng.uniform(8.0, 18.0), 1),
            "possession_avg": round(rng.uniform(38.0, 65.0), 1),
        }

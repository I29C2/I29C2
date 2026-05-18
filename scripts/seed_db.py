#!/usr/bin/env python3
# scripts/seed_db.py
"""
BetBot AI – Database Seeder
Creates realistic sample data for development and demonstration purposes.

Usage (inside Docker):
    docker-compose exec backend python /app/scripts/seed_db.py

Usage (local venv):
    python scripts/seed_db.py
"""
from __future__ import annotations

import os
import sys
import random
from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# Ensure the backend/app package is importable when run from project root
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(SCRIPT_DIR, "..", "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Set default env vars so config can load without a .env file
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://betbot:betbot_secret@localhost:5432/betbot",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "seed-script-secret-change-me")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.core.security import get_password_hash
from app.models.user import User, SubscriptionType
from app.models.league import League, CompetitionType
from app.models.match import Match, MatchStatus
from app.models.odds import Odds
from app.models.prediction import Prediction, PredictionMarket, ConfidenceLevel, PredictionStatus
from app.models.integrity import IntegrityScore, RiskLevel, Recommendation

# ---------------------------------------------------------------------------
# DB engine
# ---------------------------------------------------------------------------
engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


# ===========================================================================
# Helpers
# ===========================================================================

def _today_at(hour: int, minute: int = 0) -> datetime:
    """Return a timezone-aware datetime for today at the given UTC time."""
    return datetime.now(timezone.utc).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )


def _days_ago(n: int, hour: int = 15, minute: int = 0) -> datetime:
    base = datetime.now(timezone.utc) - timedelta(days=n)
    return base.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _days_ahead(n: int, hour: int = 15, minute: int = 0) -> datetime:
    base = datetime.now(timezone.utc) + timedelta(days=n)
    return base.replace(hour=hour, minute=minute, second=0, microsecond=0)


FORM_RESULTS = ["W", "W", "D", "L", "W"]


def _random_form(length: int = 5) -> list:
    return [
        {
            "result": random.choice(["W", "D", "L"]),
            "goals_for": random.randint(0, 4),
            "goals_against": random.randint(0, 3),
        }
        for _ in range(length)
    ]


# ===========================================================================
# Seed functions
# ===========================================================================

def seed_leagues(session) -> dict[str, League]:
    """Create leagues and return a code→League map."""
    print("  Seeding leagues...")
    leagues_data = [
        {
            "name": "Premier League",
            "country": "England",
            "code": "PL",
            "competition_type": CompetitionType.domestic,
            "is_active": True,
            "is_premium": False,
            "season": "2024/25",
            "risk_profile": 0.05,
        },
        {
            "name": "La Liga",
            "country": "Spain",
            "code": "LL",
            "competition_type": CompetitionType.domestic,
            "is_active": True,
            "is_premium": False,
            "season": "2024/25",
            "risk_profile": 0.07,
        },
        {
            "name": "Bundesliga",
            "country": "Germany",
            "code": "BL1",
            "competition_type": CompetitionType.domestic,
            "is_active": True,
            "is_premium": False,
            "season": "2024/25",
            "risk_profile": 0.04,
        },
        {
            "name": "Serie A",
            "country": "Italy",
            "code": "SA",
            "competition_type": CompetitionType.domestic,
            "is_active": True,
            "is_premium": False,
            "season": "2024/25",
            "risk_profile": 0.10,
        },
        {
            "name": "Ligue 1",
            "country": "France",
            "code": "L1",
            "competition_type": CompetitionType.domestic,
            "is_active": True,
            "is_premium": False,
            "season": "2024/25",
            "risk_profile": 0.08,
        },
        {
            "name": "UEFA Champions League",
            "country": "Europe",
            "code": "UCL",
            "competition_type": CompetitionType.european,
            "is_active": True,
            "is_premium": True,
            "season": "2024/25",
            "risk_profile": 0.03,
        },
        {
            "name": "UEFA Europa League",
            "country": "Europe",
            "code": "UEL",
            "competition_type": CompetitionType.european,
            "is_active": True,
            "is_premium": True,
            "season": "2024/25",
            "risk_profile": 0.05,
        },
        {
            "name": "Eredivisie",
            "country": "Netherlands",
            "code": "ED",
            "competition_type": CompetitionType.domestic,
            "is_active": True,
            "is_premium": False,
            "season": "2024/25",
            "risk_profile": 0.06,
        },
    ]

    league_map = {}
    for data in leagues_data:
        existing = session.query(League).filter_by(code=data["code"]).first()
        if existing:
            league_map[data["code"]] = existing
            continue
        league = League(**data)
        session.add(league)
        session.flush()
        league_map[data["code"]] = league
        print(f"    + {data['name']} ({data['code']})")

    session.commit()
    print(f"  Done. {len(league_map)} leagues available.")
    return league_map


def seed_users(session) -> dict[str, User]:
    """Create admin and sample users."""
    print("  Seeding users...")
    users_data = [
        {
            "email": "admin@betbot.ai",
            "username": "admin",
            "password": "admin123",
            "is_admin": True,
            "subscription_type": SubscriptionType.premium,
        },
        {
            "email": "user@betbot.ai",
            "username": "bettor",
            "password": "user123",
            "is_admin": False,
            "subscription_type": SubscriptionType.free,
        },
        {
            "email": "pro@betbot.ai",
            "username": "prouser",
            "password": "pro12345",
            "is_admin": False,
            "subscription_type": SubscriptionType.premium,
        },
    ]

    user_map = {}
    for data in users_data:
        existing = session.query(User).filter_by(email=data["email"]).first()
        if existing:
            user_map[data["email"]] = existing
            continue
        user = User(
            email=data["email"],
            username=data["username"],
            hashed_password=get_password_hash(data["password"]),
            is_active=True,
            is_admin=data["is_admin"],
            subscription_type=data["subscription_type"],
            alert_threshold=3.0,
            language="en",
        )
        session.add(user)
        session.flush()
        user_map[data["email"]] = user
        role = "ADMIN" if data["is_admin"] else data["subscription_type"].value.upper()
        print(f"    + {data['email']} [{role}] (password: {data['password']})")

    session.commit()
    print(f"  Done. {len(user_map)} users available.")
    return user_map


def seed_matches(session, league_map: dict[str, League]) -> list[Match]:
    """Create sample matches: today, upcoming, and recently finished."""
    print("  Seeding matches...")
    pl = league_map["PL"]
    ll = league_map["LL"]
    bl = league_map["BL1"]
    ucl = league_map["UCL"]

    matches_data = [
        # ---- Today's matches ----
        {
            "league": pl,
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "match_date": _today_at(12, 30),
            "status": MatchStatus.scheduled,
            "venue": "Emirates Stadium",
            "round": "Matchday 34",
            "home_xg": 1.92, "away_xg": 1.05,
            "home_shots_pg": 14.8, "away_shots_pg": 10.2,
            "home_possession": 58.0, "away_possession": 42.0,
        },
        {
            "league": pl,
            "home_team": "Manchester City",
            "away_team": "Liverpool",
            "match_date": _today_at(15, 0),
            "status": MatchStatus.scheduled,
            "venue": "Etihad Stadium",
            "round": "Matchday 34",
            "home_xg": 2.10, "away_xg": 1.65,
            "home_shots_pg": 16.1, "away_shots_pg": 13.4,
            "home_possession": 62.0, "away_possession": 38.0,
        },
        {
            "league": ll,
            "home_team": "Real Madrid",
            "away_team": "FC Barcelona",
            "match_date": _today_at(20, 0),
            "status": MatchStatus.scheduled,
            "venue": "Santiago Bernabeu",
            "round": "Matchday 33",
            "home_xg": 1.78, "away_xg": 1.95,
            "home_shots_pg": 13.5, "away_shots_pg": 15.2,
            "home_possession": 49.0, "away_possession": 51.0,
        },
        {
            "league": bl,
            "home_team": "Bayern Munich",
            "away_team": "Borussia Dortmund",
            "match_date": _today_at(17, 30),
            "status": MatchStatus.scheduled,
            "venue": "Allianz Arena",
            "round": "Matchday 30",
            "home_xg": 2.45, "away_xg": 0.98,
            "home_shots_pg": 18.3, "away_shots_pg": 9.7,
            "home_possession": 65.0, "away_possession": 35.0,
        },
        {
            "league": ucl,
            "home_team": "Manchester City",
            "away_team": "Real Madrid",
            "match_date": _today_at(20, 0),
            "status": MatchStatus.scheduled,
            "venue": "Etihad Stadium",
            "round": "Semi-Final 1st Leg",
            "home_xg": 1.85, "away_xg": 1.72,
            "home_shots_pg": 14.5, "away_shots_pg": 13.8,
            "home_possession": 55.0, "away_possession": 45.0,
        },
        # ---- Upcoming (tomorrow / this week) ----
        {
            "league": pl,
            "home_team": "Tottenham Hotspur",
            "away_team": "Manchester United",
            "match_date": _days_ahead(1, 15, 0),
            "status": MatchStatus.scheduled,
            "venue": "Tottenham Hotspur Stadium",
            "round": "Matchday 35",
        },
        {
            "league": ll,
            "home_team": "Atletico Madrid",
            "away_team": "Sevilla",
            "match_date": _days_ahead(2, 19, 0),
            "status": MatchStatus.scheduled,
            "venue": "Wanda Metropolitano",
            "round": "Matchday 34",
        },
        {
            "league": bl,
            "home_team": "Bayer Leverkusen",
            "away_team": "RB Leipzig",
            "match_date": _days_ahead(3, 17, 30),
            "status": MatchStatus.scheduled,
            "venue": "BayArena",
            "round": "Matchday 31",
        },
        # ---- Recently finished ----
        {
            "league": pl,
            "home_team": "Newcastle United",
            "away_team": "Aston Villa",
            "match_date": _days_ago(1, 15, 0),
            "status": MatchStatus.finished,
            "home_score": 2,
            "away_score": 1,
            "venue": "St. James' Park",
            "round": "Matchday 33",
        },
        {
            "league": ll,
            "home_team": "FC Barcelona",
            "away_team": "Girona",
            "match_date": _days_ago(2, 20, 0),
            "status": MatchStatus.finished,
            "home_score": 3,
            "away_score": 2,
            "venue": "Olimpic Lluis Companys",
            "round": "Matchday 32",
        },
        {
            "league": ucl,
            "home_team": "Arsenal",
            "away_team": "Bayern Munich",
            "match_date": _days_ago(3, 20, 0),
            "status": MatchStatus.finished,
            "home_score": 1,
            "away_score": 0,
            "venue": "Emirates Stadium",
            "round": "Quarter-Final 2nd Leg",
        },
    ]

    created = []
    for data in matches_data:
        league = data.pop("league")
        # Skip duplicates (same teams same date)
        existing = session.query(Match).filter_by(
            league_id=league.id,
            home_team=data["home_team"],
            away_team=data["away_team"],
            match_date=data["match_date"],
        ).first()
        if existing:
            created.append(existing)
            continue

        match = Match(
            league_id=league.id,
            home_form=_random_form(),
            away_form=_random_form(),
            **data,
        )
        session.add(match)
        session.flush()
        created.append(match)
        print(f"    + {match.home_team} vs {match.away_team} ({match.match_date.strftime('%Y-%m-%d %H:%M')} UTC)")

    session.commit()
    print(f"  Done. {len(created)} matches available.")
    return created


def seed_odds(session, matches: list[Match]) -> None:
    """Create sample bookmaker odds for each match."""
    print("  Seeding odds data...")
    from app.models.odds import OddsMarket
    bookmakers = ["Bet365", "William Hill", "Betway", "Pinnacle", "Betfair"]
    count = 0

    for match in matches:
        if match.status != MatchStatus.scheduled:
            continue  # Only seed odds for upcoming matches

        for bookmaker in bookmakers:
            existing = session.query(Odds).filter_by(
                match_id=match.id, bookmaker=bookmaker
            ).first()
            if existing:
                continue

            # Simulate slightly different odds per bookmaker
            variance = random.uniform(-0.05, 0.05)
            home_odds_val = round(random.uniform(1.70, 3.50) + variance, 2)
            odds = Odds(
                match_id=match.id,
                bookmaker=bookmaker,
                market=OddsMarket.one_x_two,
                home_odds=home_odds_val,
                draw_odds=round(random.uniform(2.90, 3.80) + variance, 2),
                away_odds=round(random.uniform(2.00, 5.00) + variance, 2),
                over_odds=round(random.uniform(1.60, 2.20) + variance, 2),
                under_odds=round(random.uniform(1.70, 2.30) - variance, 2),
                yes_odds=round(random.uniform(1.65, 2.00) + variance, 2),
                no_odds=round(random.uniform(1.85, 2.20) - variance, 2),
                opening_home=home_odds_val,
                movement_flag=False,
                volume_spike=False,
                recorded_at=datetime.now(timezone.utc),
            )
            session.add(odds)
            count += 1

    session.commit()
    print(f"  Done. {count} odds records created.")


def seed_predictions(session, matches: list[Match]) -> None:
    """Create sample AI predictions for scheduled matches."""
    print("  Seeding predictions...")
    count = 0
    scheduled = [m for m in matches if m.status == MatchStatus.scheduled]

    # Try to get a model registry entry; create a dummy one if none exists
    from app.models.model_registry import ModelRegistry, ModelType, ModelMarket
    model = session.query(ModelRegistry).first()
    if not model:
        model = ModelRegistry(
            name="XGBoost Ensemble v1",
            version="1.0.0",
            model_type=ModelType.ensemble,
            market=ModelMarket.all_markets,
            is_active=True,
            brier_score=0.21,
            log_loss=0.58,
            roi=4.2,
            yield_pct=5.1,
            training_date=datetime.now(timezone.utc),
            validation_period="2023-01 to 2024-06",
        )
        session.add(model)
        session.flush()

    markets = [PredictionMarket.one_x_two, PredictionMarket.over_under_25, PredictionMarket.btts]

    for match in scheduled[:6]:    # Predict on first 6 scheduled matches
        for market in markets:
            existing = session.query(Prediction).filter_by(
                match_id=match.id, market=market
            ).first()
            if existing:
                continue

            ai_prob = round(random.uniform(0.35, 0.65), 4)
            market_odds_val = round(1 / (ai_prob * 0.92), 2)    # implied 8% margin
            fair_odds_val = round(1 / ai_prob, 2)
            edge = (ai_prob - 1 / market_odds_val) * 100
            is_value = edge >= settings.VALUE_BET_THRESHOLD

            pred = Prediction(
                match_id=match.id,
                model_id=model.id,
                market=market,
                predicted_outcome="home" if ai_prob > 0.50 else "away",
                ai_probability=ai_prob,
                fair_odds=fair_odds_val,
                market_odds=market_odds_val,
                edge_percentage=round(edge, 2),
                confidence_level=random.choice(list(ConfidenceLevel)),
                is_value_bet=is_value,
                value_threshold_used=settings.VALUE_BET_THRESHOLD,
                status=PredictionStatus.published,
                explanatory_factors=[
                    "Strong home form (4W in last 5)",
                    "Opponent missing key striker",
                ],
            )
            session.add(pred)
            count += 1

    session.commit()
    print(f"  Done. {count} predictions created.")


def seed_integrity_scores(session, matches: list[Match]) -> None:
    """Create sample integrity scores for scheduled matches."""
    print("  Seeding integrity scores...")
    count = 0

    # Mostly clean matches, one high-risk sample
    risk_scenarios = [
        (8.0,  "low",      "normal"),
        (12.0, "low",      "normal"),
        (22.0, "low",      "normal"),
        (38.0, "medium",   "reduced_stake"),
        (45.0, "medium",   "reduced_stake"),
        (62.0, "high",     "caution"),
        (78.0, "critical", "no_bet"),      # 1 suspicious match
    ]

    scheduled = [m for m in matches if m.status == MatchStatus.scheduled]
    for i, match in enumerate(scheduled):
        existing = session.query(IntegrityScore).filter_by(match_id=match.id).first()
        if existing:
            continue

        score_val, risk_str, rec_str = risk_scenarios[i % len(risk_scenarios)]

        integrity = IntegrityScore(
            match_id=match.id,
            score=score_val,
            risk_level=RiskLevel[risk_str],
            recommendation=Recommendation[rec_str],
            motivation_score=round(score_val * random.uniform(0.6, 1.0), 1),
            odds_movement_score=round(score_val * random.uniform(0.8, 1.2), 1),
            financial_instability_score=round(score_val * random.uniform(0.3, 0.8), 1),
            performance_anomaly_score=round(score_val * random.uniform(0.5, 1.0), 1),
            market_irregularity_score=round(score_val * random.uniform(0.7, 1.1), 1),
            contributing_factors=[
                "Suspicious pre-match odds movement" if score_val > 50 else "Stable market",
                "Normal booking patterns",
            ],
            blocks_value_bet=(score_val >= settings.INTEGRITY_RISK_THRESHOLD),
        )
        session.add(integrity)
        count += 1

    session.commit()
    print(f"  Done. {count} integrity scores created.")


# ===========================================================================
# Main entry point
# ===========================================================================

def main() -> None:
    print("\nBetBot AI – Database Seeder")
    print("=" * 50)

    # Ensure all tables exist
    print("\n[1/6] Creating database tables (if not exists)...")
    from app.models import (  # noqa: F401
        user, league, match, odds, prediction, integrity, alert, model_registry
    )
    Base.metadata.create_all(bind=engine)
    print("  Tables ready.")

    session = SessionLocal()
    try:
        print("\n[2/6] Seeding leagues...")
        league_map = seed_leagues(session)

        print("\n[3/6] Seeding users...")
        seed_users(session)

        print("\n[4/6] Seeding matches...")
        matches = seed_matches(session, league_map)

        print("\n[5/6] Seeding odds...")
        seed_odds(session, matches)

        print("\n[6/6] Seeding predictions & integrity scores...")
        seed_predictions(session, matches)
        seed_integrity_scores(session, matches)

    except Exception as exc:
        session.rollback()
        print(f"\nERROR: {exc}")
        raise
    finally:
        session.close()

    print("\n" + "=" * 50)
    print("Seeding complete!")
    print("\nDefault credentials:")
    print("  Admin : admin@betbot.ai  / admin123")
    print("  User  : user@betbot.ai   / user123")
    print("  Pro   : pro@betbot.ai    / pro12345")
    print("\nAPI docs: http://localhost:8000/docs\n")


if __name__ == "__main__":
    main()

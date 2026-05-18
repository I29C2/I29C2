# backend/tests/conftest.py
"""
pytest configuration and shared fixtures for the BetBot AI test suite.
Uses an in-memory SQLite database so tests run without a live Postgres instance.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# ---------------------------------------------------------------------------
# Point the app at SQLite BEFORE importing anything that touches `settings`
# ---------------------------------------------------------------------------
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_betbot.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("POSTGRES_DB", "betbot_test")
os.environ.setdefault("POSTGRES_USER", "betbot_test")
os.environ.setdefault("POSTGRES_PASSWORD", "betbot_test")

from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User, SubscriptionType  # noqa: E402
from app.models.league import League, CompetitionType  # noqa: E402
from app.models.match import Match, MatchStatus  # noqa: E402
from app.core.security import get_password_hash, create_access_token  # noqa: E402
from app.core.config import settings  # noqa: E402

# ---------------------------------------------------------------------------
# SQLite test engine — use check_same_thread=False for pytest-asyncio compat
# ---------------------------------------------------------------------------
SQLALCHEMY_TEST_URL = "sqlite:///./test_betbot.db"

test_engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


# ---------------------------------------------------------------------------
# Session-scoped: create tables once per test run
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Create all ORM tables on the SQLite test DB before any test runs."""
    # Ensure all models are imported so metadata is populated
    from app.models import (  # noqa: F401
        user,
        league,
        match,
        odds,
        prediction,
        integrity,
        alert,
        model_registry,
    )
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    # Clean up test db file
    if os.path.exists("./test_betbot.db"):
        os.remove("./test_betbot.db")


# ---------------------------------------------------------------------------
# Function-scoped DB session — each test gets a fresh transaction
# ---------------------------------------------------------------------------
@pytest.fixture()
def db() -> Generator[Session, None, None]:
    """Yield a test database session that is rolled back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Override the FastAPI dependency so the test client uses the test DB
# ---------------------------------------------------------------------------
@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    """TestClient with the database dependency overridden to use SQLite."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Sample leagues
# ---------------------------------------------------------------------------
@pytest.fixture()
def sample_league(db: Session) -> League:
    """Return a persisted Premier League fixture."""
    league = League(
        name="Premier League",
        country="England",
        code="PL",
        competition_type=CompetitionType.domestic,
        is_active=True,
        is_premium=False,
        season="2024/25",
        risk_profile=0.05,
    )
    db.add(league)
    db.commit()
    db.refresh(league)
    return league


@pytest.fixture()
def sample_leagues(db: Session) -> list[League]:
    """Return a list of persisted sample leagues."""
    leagues_data = [
        League(name="Premier League", country="England", code="PL",
               competition_type=CompetitionType.domestic, is_active=True, season="2024/25"),
        League(name="La Liga", country="Spain", code="LL",
               competition_type=CompetitionType.domestic, is_active=True, season="2024/25"),
        League(name="Bundesliga", country="Germany", code="BL",
               competition_type=CompetitionType.domestic, is_active=True, season="2024/25"),
        League(name="Champions League", country="Europe", code="CL",
               competition_type=CompetitionType.european, is_active=True, is_premium=True,
               season="2024/25"),
    ]
    for lg in leagues_data:
        db.add(lg)
    db.commit()
    for lg in leagues_data:
        db.refresh(lg)
    return leagues_data


# ---------------------------------------------------------------------------
# Sample matches
# ---------------------------------------------------------------------------
@pytest.fixture()
def sample_match(db: Session, sample_league: League) -> Match:
    """Return a persisted match scheduled for today."""
    today = datetime.now(timezone.utc).replace(hour=15, minute=0, second=0, microsecond=0)
    match = Match(
        league_id=sample_league.id,
        home_team="Arsenal",
        away_team="Chelsea",
        match_date=today,
        status=MatchStatus.scheduled,
        venue="Emirates Stadium",
        round="Matchday 32",
        home_form=[
            {"result": "W", "goals_for": 3, "goals_against": 1},
            {"result": "W", "goals_for": 2, "goals_against": 0},
            {"result": "D", "goals_for": 1, "goals_against": 1},
            {"result": "W", "goals_for": 2, "goals_against": 1},
            {"result": "L", "goals_for": 0, "goals_against": 1},
        ],
        away_form=[
            {"result": "D", "goals_for": 2, "goals_against": 2},
            {"result": "W", "goals_for": 1, "goals_against": 0},
            {"result": "L", "goals_for": 0, "goals_against": 2},
            {"result": "W", "goals_for": 3, "goals_against": 1},
            {"result": "D", "goals_for": 1, "goals_against": 1},
        ],
        home_xg=1.85,
        away_xg=1.12,
        home_shots_pg=14.2,
        away_shots_pg=11.8,
        home_possession=58.3,
        away_possession=41.7,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@pytest.fixture()
def sample_matches_today(db: Session, sample_league: League) -> list[Match]:
    """Return multiple matches scheduled for today."""
    today_base = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    fixtures = [
        ("Arsenal", "Chelsea", today_base.replace(hour=12, minute=30)),
        ("Manchester City", "Liverpool", today_base.replace(hour=15, minute=0)),
        ("Tottenham", "Manchester United", today_base.replace(hour=17, minute=30)),
    ]
    matches = []
    for home, away, kick_off in fixtures:
        m = Match(
            league_id=sample_league.id,
            home_team=home,
            away_team=away,
            match_date=kick_off,
            status=MatchStatus.scheduled,
        )
        db.add(m)
        matches.append(m)
    db.commit()
    for m in matches:
        db.refresh(m)
    return matches


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
@pytest.fixture()
def sample_user(db: Session) -> User:
    """Return a plain free-tier test user."""
    user = User(
        email="testuser@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_admin=False,
        subscription_type=SubscriptionType.free,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def sample_admin(db: Session) -> User:
    """Return an admin test user."""
    admin = User(
        email="admin@example.com",
        username="adminuser",
        hashed_password=get_password_hash("adminpassword123"),
        is_active=True,
        is_admin=True,
        subscription_type=SubscriptionType.premium,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


# ---------------------------------------------------------------------------
# Auth headers
# ---------------------------------------------------------------------------
@pytest.fixture()
def auth_headers(sample_user: User) -> dict:
    """Return Authorization headers for the sample user."""
    token = create_access_token(
        data={"sub": str(sample_user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_auth_headers(sample_admin: User) -> dict:
    """Return Authorization headers for the admin user."""
    token = create_access_token(
        data={"sub": str(sample_admin.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"Authorization": f"Bearer {token}"}

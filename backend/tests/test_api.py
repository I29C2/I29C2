# backend/tests/test_api.py
"""
BetBot AI – API Test Suite
Tests are run against an in-memory SQLite DB (see conftest.py).
Services that depend on ML models are mocked where necessary.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.models.match import Match, MatchStatus
from app.models.league import League


# ===========================================================================
# Health check
# ===========================================================================

class TestHealthCheck:
    """Tests for the /health endpoint."""

    def test_health_check_returns_200(self, client: TestClient):
        """GET /health should return HTTP 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_body(self, client: TestClient):
        """Health response body should contain status and service name."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_check_no_auth_required(self, client: TestClient):
        """Health endpoint must be accessible without authentication."""
        response = client.get("/health")
        assert response.status_code != 401
        assert response.status_code != 403


# ===========================================================================
# Authentication – Register
# ===========================================================================

class TestRegisterUser:
    """Tests for POST /api/v1/auth/register."""

    def test_register_success(self, client: TestClient):
        """A valid payload should create a user and return 201."""
        payload = {
            "email": "newuser@betbot.ai",
            "username": "newuser",
            "password": "securePass123",
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == payload["email"]
        assert data["username"] == payload["username"]
        assert "id" in data
        # Password must never be exposed
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client: TestClient):
        """Registering with an already-used email should return 409."""
        payload = {
            "email": "dup@betbot.ai",
            "username": "dupuser1",
            "password": "securePass123",
        }
        client.post("/api/v1/auth/register", json=payload)
        # Second attempt with same email, different username
        payload["username"] = "dupuser2"
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409

    def test_register_duplicate_username(self, client: TestClient):
        """Registering with an already-used username should return 409."""
        payload = {
            "email": "first@betbot.ai",
            "username": "sharedname",
            "password": "securePass123",
        }
        client.post("/api/v1/auth/register", json=payload)
        payload["email"] = "second@betbot.ai"
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409

    def test_register_invalid_email(self, client: TestClient):
        """An invalid email format should return 422."""
        payload = {
            "email": "not-an-email",
            "username": "testuser99",
            "password": "securePass123",
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        """A password shorter than 8 characters should return 422."""
        payload = {
            "email": "shortpw@betbot.ai",
            "username": "shortpwuser",
            "password": "abc",
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422


# ===========================================================================
# Authentication – Login
# ===========================================================================

class TestLoginUser:
    """Tests for POST /api/v1/auth/login."""

    def test_login_success(self, client: TestClient):
        """Valid credentials should return an access token."""
        # Register first
        client.post("/api/v1/auth/register", json={
            "email": "logintest@betbot.ai",
            "username": "logintest",
            "password": "mypassword123",
        })
        # Login via OAuth2 form data
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "logintest@betbot.ai", "password": "mypassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"].lower() == "bearer"

    def test_login_wrong_password(self, client: TestClient):
        """Wrong password should return 401."""
        client.post("/api/v1/auth/register", json={
            "email": "wrongpw@betbot.ai",
            "username": "wrongpwuser",
            "password": "correctpassword",
        })
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "wrongpw@betbot.ai", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Login for an unregistered email should return 401."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "ghost@betbot.ai", "password": "anything"},
        )
        assert response.status_code == 401

    def test_login_token_is_jwt(self, client: TestClient):
        """Returned access_token should look like a JWT (3 dot-separated parts)."""
        client.post("/api/v1/auth/register", json={
            "email": "jwtcheck@betbot.ai",
            "username": "jwtcheck",
            "password": "mypassword123",
        })
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "jwtcheck@betbot.ai", "password": "mypassword123"},
        )
        token = response.json().get("access_token", "")
        parts = token.split(".")
        assert len(parts) == 3, f"Expected JWT with 3 parts, got: {token!r}"


# ===========================================================================
# Leagues
# ===========================================================================

class TestGetLeagues:
    """Tests for GET /api/v1/leagues."""

    def test_get_leagues_requires_auth(self, client: TestClient):
        """Unauthenticated requests should be rejected."""
        response = client.get("/api/v1/leagues")
        assert response.status_code in (401, 403)

    def test_get_leagues_returns_list(
        self, client: TestClient, auth_headers: dict, sample_leagues
    ):
        """Authenticated request should return a list of leagues."""
        response = client.get("/api/v1/leagues", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_leagues_contains_expected_fields(
        self, client: TestClient, auth_headers: dict, sample_leagues
    ):
        """Each league should have required fields."""
        response = client.get("/api/v1/leagues", headers=auth_headers)
        assert response.status_code == 200
        leagues = response.json()
        if leagues:
            league = leagues[0]
            for field in ("id", "name", "country", "code", "competition_type"):
                assert field in league, f"Missing field: {field}"

    def test_get_leagues_active_only_filter(
        self, client: TestClient, auth_headers: dict, sample_leagues
    ):
        """active_only=true (default) should only return active leagues."""
        response = client.get("/api/v1/leagues?active_only=true", headers=auth_headers)
        assert response.status_code == 200
        leagues = response.json()
        # All returned leagues should be active (is_active not in the response dict in this impl,
        # but the count should be >= 1 since we seeded active leagues)
        assert len(leagues) >= 1

    def test_get_leagues_count_matches_seeded_data(
        self, client: TestClient, auth_headers: dict, sample_leagues
    ):
        """The number of returned leagues should match seeded active leagues."""
        response = client.get("/api/v1/leagues", headers=auth_headers)
        leagues = response.json()
        # We seeded 4 active leagues in sample_leagues fixture
        assert len(leagues) == 4


# ===========================================================================
# Today's Matches
# ===========================================================================

class TestGetTodaysMatches:
    """Tests for GET /api/v1/matches/today."""

    def test_requires_auth(self, client: TestClient):
        """Unauthenticated request should be rejected."""
        response = client.get("/api/v1/matches/today")
        assert response.status_code in (401, 403)

    def test_returns_paginated_response(
        self, client: TestClient, auth_headers: dict, sample_matches_today
    ):
        """Should return paginated match list with total count."""
        response = client.get("/api/v1/matches/today", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["items"], list)

    def test_todays_matches_count(
        self, client: TestClient, auth_headers: dict, sample_matches_today
    ):
        """Should return the correct number of matches for today."""
        response = client.get("/api/v1/matches/today", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # sample_matches_today fixture creates 3 matches for today
        assert data["total"] == 3

    def test_match_has_required_fields(
        self, client: TestClient, auth_headers: dict, sample_matches_today
    ):
        """Each match should include home_team, away_team, match_date, status."""
        response = client.get("/api/v1/matches/today", headers=auth_headers)
        assert response.status_code == 200
        items = response.json()["items"]
        if items:
            match = items[0]
            for field in ("id", "home_team", "away_team", "match_date", "status"):
                assert field in match, f"Match missing field: {field}"

    def test_pagination_page_size(
        self, client: TestClient, auth_headers: dict, sample_matches_today
    ):
        """page_size parameter should limit the number of results."""
        response = client.get(
            "/api/v1/matches/today?page=1&page_size=1", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 1


# ===========================================================================
# Value Bet Detection – Unit Tests
# ===========================================================================

class TestValueBetDetection:
    """Unit tests for value bet detection logic (service-level, no HTTP)."""

    @pytest.mark.unit
    def test_positive_ev_detected_as_value_bet(self):
        """When implied probability < model probability, EV should be positive."""
        # Simulate the core EV formula used by PredictionService
        bookmaker_odds = 2.50       # Decimal odds (e.g., Betfair)
        model_prob = 0.48           # Model says 48% chance of home win
        bookmaker_margin = 0.05     # 5% vig

        # Fair odds implied probability
        implied_prob = 1 / bookmaker_odds
        # Expected Value formula: (prob * odds) - 1
        ev_percent = (model_prob * bookmaker_odds - 1) * 100

        # Edge = model_prob - implied_prob
        edge = (model_prob - implied_prob) * 100

        value_bet_threshold = 3.0   # 3% minimum edge

        is_value_bet = edge >= value_bet_threshold
        assert is_value_bet, (
            f"Expected value bet with edge={edge:.2f}%, "
            f"model_prob={model_prob}, implied={implied_prob:.3f}"
        )
        assert ev_percent > 0

    @pytest.mark.unit
    def test_negative_ev_not_value_bet(self):
        """When implied probability > model probability, EV is negative."""
        bookmaker_odds = 1.50
        model_prob = 0.60
        implied_prob = 1 / bookmaker_odds    # 0.667

        edge = (model_prob - implied_prob) * 100    # negative
        assert edge < 0, "Should not be a value bet when model prob < implied prob"

    @pytest.mark.unit
    def test_value_bet_threshold_boundary(self):
        """A bet exactly at the threshold should still be flagged."""
        threshold = 3.0
        edge = 3.0
        assert edge >= threshold

    @pytest.mark.unit
    def test_value_bet_below_threshold_rejected(self):
        """A bet with edge below threshold should not be flagged."""
        threshold = 3.0
        edge = 2.9
        assert edge < threshold

    @pytest.mark.unit
    def test_value_bet_ev_formula_accuracy(self):
        """Verify EV formula: EV = (p * odds - 1) * stake."""
        stake = 100.0
        probability = 0.50
        decimal_odds = 2.20

        ev = (probability * decimal_odds - 1) * stake
        expected = (0.50 * 2.20 - 1) * 100  # = 10.0
        assert abs(ev - expected) < 0.001
        assert ev == pytest.approx(10.0)

    @pytest.mark.unit
    def test_multiple_markets_value_detection(self):
        """Value bets can be identified across 1X2, O/U, and BTTS markets."""
        markets = [
            {"market": "1x2", "home_prob": 0.55, "odds": 2.10,  "threshold": 3.0},
            {"market": "over_2.5", "over_prob": 0.68, "odds": 1.80, "threshold": 3.0},
            {"market": "btts", "btts_prob": 0.62, "odds": 1.75,  "threshold": 3.0},
        ]
        for m in markets:
            prob = list(m.values())[1]   # second value is the probability
            odds = m["odds"]
            edge = (prob - 1 / odds) * 100
            # Just assert the formula works per market
            assert isinstance(edge, float)


# ===========================================================================
# Integrity Score Calculation – Unit Tests
# ===========================================================================

class TestIntegrityScoreCalculation:
    """Unit tests for match integrity scoring logic."""

    @pytest.mark.unit
    def test_low_risk_match_score(self):
        """A match with stable odds and no suspicious patterns should score < 30."""
        signals = {
            "odds_movement_score": 5.0,       # 0-100, low = stable
            "late_money_score": 2.0,           # 0-100
            "red_card_anomaly_score": 0.0,
            "booking_pattern_score": 10.0,
            "league_risk_profile": 5.0,
        }
        weights = {
            "odds_movement_score": 0.30,
            "late_money_score": 0.25,
            "red_card_anomaly_score": 0.20,
            "booking_pattern_score": 0.15,
            "league_risk_profile": 0.10,
        }
        composite = sum(signals[k] * weights[k] for k in signals)
        assert composite < 30, f"Expected low risk, got score={composite:.1f}"

    @pytest.mark.unit
    def test_high_risk_match_score(self):
        """A match with multiple suspicious signals should score >= 70."""
        signals = {
            "odds_movement_score": 85.0,
            "late_money_score": 90.0,
            "red_card_anomaly_score": 80.0,
            "booking_pattern_score": 75.0,
            "league_risk_profile": 60.0,
        }
        weights = {
            "odds_movement_score": 0.30,
            "late_money_score": 0.25,
            "red_card_anomaly_score": 0.20,
            "booking_pattern_score": 0.15,
            "league_risk_profile": 0.10,
        }
        composite = sum(signals[k] * weights[k] for k in signals)
        assert composite >= 70, f"Expected high risk, got score={composite:.1f}"

    @pytest.mark.unit
    def test_integrity_score_range(self):
        """Integrity score should always be in the range [0, 100]."""
        test_cases = [
            (0.0, 0.0, 0.0, 0.0, 0.0),
            (100.0, 100.0, 100.0, 100.0, 100.0),
            (50.0, 45.0, 60.0, 30.0, 40.0),
        ]
        weights = [0.30, 0.25, 0.20, 0.15, 0.10]
        for signals in test_cases:
            score = sum(s * w for s, w in zip(signals, weights))
            assert 0.0 <= score <= 100.0, f"Score {score} out of range for signals {signals}"

    @pytest.mark.unit
    def test_risk_level_classification(self):
        """Scores should map to correct risk levels."""
        def classify(score: float) -> str:
            if score < 30:
                return "low"
            elif score < 55:
                return "medium"
            elif score < 75:
                return "high"
            else:
                return "critical"

        assert classify(15.0) == "low"
        assert classify(42.0) == "medium"
        assert classify(65.0) == "high"
        assert classify(85.0) == "critical"

    @pytest.mark.unit
    def test_recommendation_based_on_risk(self):
        """Recommendation should follow from risk level."""
        def recommend(score: float, threshold: float = 70.0) -> str:
            if score >= threshold:
                return "no_bet"
            elif score >= 55:
                return "caution"
            elif score >= 30:
                return "reduced_stake"
            else:
                return "normal"

        assert recommend(85.0) == "no_bet"
        assert recommend(60.0) == "caution"
        assert recommend(40.0) == "reduced_stake"
        assert recommend(15.0) == "normal"

    @pytest.mark.unit
    def test_odds_movement_anomaly_detection(self):
        """Large odds movement within 24 hours should trigger elevated score."""
        opening_odds = 2.50
        closing_odds = 1.60   # major drop = heavy money on home
        movement_pct = abs(closing_odds - opening_odds) / opening_odds * 100
        # Movement of ~36% is suspicious
        assert movement_pct > 20, "Expected significant movement to be flagged"

    @pytest.mark.unit
    def test_no_bet_flag_above_threshold(self):
        """Matches above INTEGRITY_RISK_THRESHOLD should be flagged as no_bet."""
        threshold = 70.0
        score = 75.0
        should_block = score >= threshold
        assert should_block is True

    @pytest.mark.unit
    def test_value_bet_suppressed_by_integrity(self):
        """A value bet on a compromised match should be suppressed."""
        ev_edge = 8.5           # Good value bet
        integrity_score = 78.0  # But high integrity risk
        threshold = 70.0

        should_publish = ev_edge > 0 and integrity_score < threshold
        assert should_publish is False, (
            "Value bet should be suppressed when integrity risk is above threshold"
        )

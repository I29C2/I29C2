# backend/alembic/versions/001_initial.py
"""Initial schema – create all tables.

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Enum types
    # ------------------------------------------------------------------
    subscription_type = postgresql.ENUM(
        "free", "premium", name="subscriptiontype", create_type=False
    )
    subscription_type.create(op.get_bind(), checkfirst=True)

    competition_type = postgresql.ENUM(
        "domestic", "european", name="competitiontype", create_type=False
    )
    competition_type.create(op.get_bind(), checkfirst=True)

    match_status = postgresql.ENUM(
        "scheduled", "live", "finished", "postponed",
        name="matchstatus", create_type=False,
    )
    match_status.create(op.get_bind(), checkfirst=True)

    odds_market = postgresql.ENUM(
        "1x2", "over_under_25", "btts", name="oddsmarket", create_type=False
    )
    odds_market.create(op.get_bind(), checkfirst=True)

    prediction_market = postgresql.ENUM(
        "1x2", "over_under_25", "btts", name="predictionmarket", create_type=False
    )
    prediction_market.create(op.get_bind(), checkfirst=True)

    confidence_level = postgresql.ENUM(
        "low", "medium", "high", "very_high",
        name="confidencelevel", create_type=False,
    )
    confidence_level.create(op.get_bind(), checkfirst=True)

    prediction_status = postgresql.ENUM(
        "pending", "published", "rejected", "expired",
        name="predictionstatus", create_type=False,
    )
    prediction_status.create(op.get_bind(), checkfirst=True)

    risk_level = postgresql.ENUM(
        "low", "medium", "high", "critical", name="risklevel", create_type=False
    )
    risk_level.create(op.get_bind(), checkfirst=True)

    recommendation = postgresql.ENUM(
        "normal", "reduced_stake", "caution", "no_bet",
        name="recommendation", create_type=False,
    )
    recommendation.create(op.get_bind(), checkfirst=True)

    alert_type = postgresql.ENUM(
        "value_bet", "daily_summary", "risk_warning", "custom",
        name="alerttype", create_type=False,
    )
    alert_type.create(op.get_bind(), checkfirst=True)

    model_type = postgresql.ENUM(
        "logistic", "xgboost", "poisson", "ensemble",
        name="modeltype", create_type=False,
    )
    model_type.create(op.get_bind(), checkfirst=True)

    model_market = postgresql.ENUM(
        "1x2", "over_under_25", "btts", "all_markets",
        name="modelmarket", create_type=False,
    )
    model_market.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------------

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "subscription_type",
            sa.Enum("free", "premium", name="subscriptiontype"),
            nullable=False,
            server_default="free",
        ),
        sa.Column("subscription_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("telegram_id", sa.String(64), nullable=True),
        sa.Column("favorite_leagues", postgresql.JSONB(), nullable=True),
        sa.Column("preferred_markets", postgresql.JSONB(), nullable=True),
        sa.Column("alert_threshold", sa.Float(), nullable=False, server_default="3.0"),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "leagues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("code", sa.String(10), nullable=False),
        sa.Column(
            "competition_type",
            sa.Enum("domestic", "european", name="competitiontype"),
            nullable=False,
            server_default="domestic",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_premium", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("season", sa.String(20), nullable=True),
        sa.Column("risk_profile", sa.Float(), nullable=False, server_default="0.1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_leagues_id", "leagues", ["id"])
    op.create_index("ix_leagues_code", "leagues", ["code"], unique=True)

    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "league_id",
            sa.Integer(),
            sa.ForeignKey("leagues.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("home_team", sa.String(200), nullable=False),
        sa.Column("away_team", sa.String(200), nullable=False),
        sa.Column("match_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("scheduled", "live", "finished", "postponed", name="matchstatus"),
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("venue", sa.String(200), nullable=True),
        sa.Column("round", sa.String(50), nullable=True),
        sa.Column("home_form", postgresql.JSONB(), nullable=True),
        sa.Column("away_form", postgresql.JSONB(), nullable=True),
        sa.Column("home_xg", sa.Float(), nullable=True),
        sa.Column("away_xg", sa.Float(), nullable=True),
        sa.Column("home_shots_pg", sa.Float(), nullable=True),
        sa.Column("away_shots_pg", sa.Float(), nullable=True),
        sa.Column("home_possession", sa.Float(), nullable=True),
        sa.Column("away_possession", sa.Float(), nullable=True),
        sa.Column("home_elo", sa.Float(), nullable=True),
        sa.Column("away_elo", sa.Float(), nullable=True),
        sa.Column("home_injuries", postgresql.JSONB(), nullable=True),
        sa.Column("away_injuries", postgresql.JSONB(), nullable=True),
        sa.Column("home_rest_days", sa.Integer(), nullable=True),
        sa.Column("away_rest_days", sa.Integer(), nullable=True),
        sa.Column("h2h_stats", postgresql.JSONB(), nullable=True),
        sa.Column("motivation_context", postgresql.JSONB(), nullable=True),
        sa.Column("external_id", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_matches_id", "matches", ["id"])
    op.create_index("ix_matches_league_id", "matches", ["league_id"])
    op.create_index("ix_matches_match_date", "matches", ["match_date"])
    op.create_index("ix_matches_status", "matches", ["status"])
    op.create_index("ix_matches_external_id", "matches", ["external_id"], unique=True)

    op.create_table(
        "model_registry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column(
            "model_type",
            sa.Enum("logistic", "xgboost", "poisson", "ensemble", name="modeltype"),
            nullable=False,
        ),
        sa.Column(
            "market",
            sa.Enum("1x2", "over_under_25", "btts", "all_markets", name="modelmarket"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("brier_score", sa.Float(), nullable=True),
        sa.Column("log_loss", sa.Float(), nullable=True),
        sa.Column("calibration_error", sa.Float(), nullable=True),
        sa.Column("roi", sa.Float(), nullable=True),
        sa.Column("yield_pct", sa.Float(), nullable=True),
        sa.Column("training_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("validation_period", sa.String(100), nullable=True),
        sa.Column("model_path", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_model_registry_id", "model_registry", ["id"])
    op.create_index("ix_model_registry_is_active", "model_registry", ["is_active"])

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "match_id",
            sa.Integer(),
            sa.ForeignKey("matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "model_id",
            sa.Integer(),
            sa.ForeignKey("model_registry.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "market",
            sa.Enum("1x2", "over_under_25", "btts", name="predictionmarket"),
            nullable=False,
        ),
        sa.Column("predicted_outcome", sa.String(20), nullable=False),
        sa.Column("ai_probability", sa.Float(), nullable=False),
        sa.Column("fair_odds", sa.Float(), nullable=False),
        sa.Column("market_odds", sa.Float(), nullable=False),
        sa.Column("edge_percentage", sa.Float(), nullable=False),
        sa.Column(
            "confidence_level",
            sa.Enum("low", "medium", "high", "very_high", name="confidencelevel"),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("is_value_bet", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("value_threshold_used", sa.Float(), nullable=False, server_default="3.0"),
        sa.Column("explanatory_factors", postgresql.JSONB(), nullable=True),
        sa.Column("bankroll_suggestion", sa.String(200), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "published", "rejected", "expired", name="predictionstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_predictions_id", "predictions", ["id"])
    op.create_index("ix_predictions_match_id", "predictions", ["match_id"])
    op.create_index("ix_predictions_is_value_bet", "predictions", ["is_value_bet"])
    op.create_index("ix_predictions_status", "predictions", ["status"])

    op.create_table(
        "odds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "match_id",
            sa.Integer(),
            sa.ForeignKey("matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("bookmaker", sa.String(100), nullable=False),
        sa.Column(
            "market",
            sa.Enum("1x2", "over_under_25", "btts", name="oddsmarket"),
            nullable=False,
        ),
        sa.Column("home_odds", sa.Float(), nullable=True),
        sa.Column("draw_odds", sa.Float(), nullable=True),
        sa.Column("away_odds", sa.Float(), nullable=True),
        sa.Column("over_odds", sa.Float(), nullable=True),
        sa.Column("under_odds", sa.Float(), nullable=True),
        sa.Column("yes_odds", sa.Float(), nullable=True),
        sa.Column("no_odds", sa.Float(), nullable=True),
        sa.Column("opening_home", sa.Float(), nullable=True),
        sa.Column("opening_draw", sa.Float(), nullable=True),
        sa.Column("opening_away", sa.Float(), nullable=True),
        sa.Column("movement_flag", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("volume_spike", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_odds_id", "odds", ["id"])
    op.create_index("ix_odds_match_id", "odds", ["match_id"])

    op.create_table(
        "integrity_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "match_id",
            sa.Integer(),
            sa.ForeignKey("matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column(
            "risk_level",
            sa.Enum("low", "medium", "high", "critical", name="risklevel"),
            nullable=False,
        ),
        sa.Column(
            "recommendation",
            sa.Enum("normal", "reduced_stake", "caution", "no_bet", name="recommendation"),
            nullable=False,
        ),
        sa.Column(
            "motivation_score", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "odds_movement_score", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "financial_instability_score", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "performance_anomaly_score", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "market_irregularity_score", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column("contributing_factors", postgresql.JSONB(), nullable=True),
        sa.Column(
            "blocks_value_bet", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_integrity_scores_id", "integrity_scores", ["id"])
    op.create_index(
        "ix_integrity_scores_match_id", "integrity_scores", ["match_id"], unique=True
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "match_id",
            sa.Integer(),
            sa.ForeignKey("matches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "prediction_id",
            sa.Integer(),
            sa.ForeignKey("predictions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "alert_type",
            sa.Enum(
                "value_bet", "daily_summary", "risk_warning", "custom",
                name="alerttype",
            ),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_alerts_id", "alerts", ["id"])
    op.create_index("ix_alerts_user_id", "alerts", ["user_id"])
    op.create_index("ix_alerts_match_id", "alerts", ["match_id"])
    op.create_index("ix_alerts_alert_type", "alerts", ["alert_type"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("integrity_scores")
    op.drop_table("odds")
    op.drop_table("predictions")
    op.drop_table("model_registry")
    op.drop_table("matches")
    op.drop_table("leagues")
    op.drop_table("users")

    # Drop enum types
    for enum_name in [
        "alerttype",
        "recommendation",
        "risklevel",
        "predictionstatus",
        "confidencelevel",
        "predictionmarket",
        "oddsmarket",
        "matchstatus",
        "competitiontype",
        "subscriptiontype",
        "modeltype",
        "modelmarket",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")

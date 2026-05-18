# backend/app/workers/tasks/data_ingestion.py
from __future__ import annotations

from datetime import datetime, timezone

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


def _get_db_session():
    """Create a new DB session for use inside a Celery task."""
    from app.core.database import SessionLocal
    return SessionLocal()


@celery_app.task(name="app.workers.tasks.data_ingestion.ingest_todays_matches", bind=True)
def ingest_todays_matches(self) -> dict:
    """Fetch today's fixtures and persist any new ones to the database."""
    from app.models.league import League
    from app.models.match import Match, MatchStatus
    from app.services.data_ingestion_service import DataIngestionService

    db = _get_db_session()
    try:
        svc = DataIngestionService()
        raw_matches = svc.fetch_todays_matches()
        created = 0
        updated = 0

        for raw in raw_matches:
            external_id = raw.get("external_id")
            league_code = raw.get("league_code", "PL")

            # Resolve league
            league = db.query(League).filter(League.code == league_code).first()
            if not league:
                league = League(
                    name=league_code,
                    country="Unknown",
                    code=league_code,
                    season="2024/25",
                )
                db.add(league)
                db.flush()

            existing = (
                db.query(Match).filter(Match.external_id == external_id).first()
                if external_id
                else None
            )

            if existing:
                existing.match_date = raw.get("match_date", existing.match_date)
                svc.enrich_match(existing)
                updated += 1
            else:
                match = Match(
                    league_id=league.id,
                    home_team=raw["home_team"],
                    away_team=raw["away_team"],
                    match_date=raw["match_date"],
                    venue=raw.get("venue"),
                    round=raw.get("round"),
                    status=MatchStatus.scheduled,
                    external_id=external_id,
                )
                svc.enrich_match(match)
                db.add(match)
                created += 1

        db.commit()
        result = {"created": created, "updated": updated, "total": len(raw_matches)}
        logger.info("ingest_todays_matches_complete", **result)
        return result

    except Exception as exc:
        db.rollback()
        logger.error("ingest_todays_matches_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60, max_retries=3)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.data_ingestion.update_odds", bind=True)
def update_odds(self) -> dict:
    """Refresh odds for all of today's scheduled/live matches."""
    from datetime import timedelta

    from app.models.match import Match, MatchStatus
    from app.models.odds import Odds, OddsMarket
    from app.services.data_ingestion_service import DataIngestionService

    db = _get_db_session()
    try:
        today_start = datetime.now(tz=timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_end = today_start.replace(hour=23, minute=59, second=59)

        matches = (
            db.query(Match)
            .filter(
                Match.match_date >= today_start,
                Match.match_date <= today_end,
                Match.status.in_([MatchStatus.scheduled, MatchStatus.live]),
            )
            .all()
        )

        svc = DataIngestionService()
        updated = 0

        for match in matches:
            try:
                raw_odds = svc.fetch_odds(match.id)
                # Upsert odds record for each market
                for market in OddsMarket:
                    existing = (
                        db.query(Odds)
                        .filter(
                            Odds.match_id == match.id,
                            Odds.bookmaker == raw_odds.get("bookmaker", "Bet365"),
                            Odds.market == market,
                        )
                        .first()
                    )
                    now = datetime.now(tz=timezone.utc)
                    if existing:
                        for field in (
                            "home_odds", "draw_odds", "away_odds",
                            "over_odds", "under_odds", "yes_odds", "no_odds",
                            "movement_flag", "volume_spike",
                        ):
                            val = raw_odds.get(field)
                            if val is not None:
                                setattr(existing, field, val)
                        existing.recorded_at = now
                    else:
                        odds_obj = Odds(
                            match_id=match.id,
                            bookmaker=raw_odds.get("bookmaker", "Bet365"),
                            market=market,
                            recorded_at=now,
                            **{
                                k: raw_odds.get(k)
                                for k in (
                                    "home_odds", "draw_odds", "away_odds",
                                    "over_odds", "under_odds", "yes_odds", "no_odds",
                                    "opening_home", "opening_draw", "opening_away",
                                    "movement_flag", "volume_spike",
                                )
                            },
                        )
                        db.add(odds_obj)
                updated += 1
            except Exception as exc:
                logger.warning("odds_update_failed", match_id=match.id, error=str(exc))

        db.commit()
        result = {"matches_updated": updated}
        logger.info("update_odds_complete", **result)
        return result

    except Exception as exc:
        db.rollback()
        logger.error("update_odds_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=30, max_retries=5)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.data_ingestion.refresh_team_stats", bind=True)
def refresh_team_stats(self) -> dict:
    """Refresh team statistics (ELO, form, xG) for all active matches."""
    from app.models.match import Match, MatchStatus
    from app.services.data_ingestion_service import DataIngestionService

    db = _get_db_session()
    try:
        matches = (
            db.query(Match)
            .filter(Match.status == MatchStatus.scheduled)
            .all()
        )
        svc = DataIngestionService()
        enriched = 0

        for match in matches:
            try:
                svc.enrich_match(match)
                enriched += 1
            except Exception as exc:
                logger.warning("enrich_match_failed", match_id=match.id, error=str(exc))

        db.commit()
        result = {"matches_enriched": enriched}
        logger.info("refresh_team_stats_complete", **result)
        return result

    except Exception as exc:
        db.rollback()
        logger.error("refresh_team_stats_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=120, max_retries=2)
    finally:
        db.close()

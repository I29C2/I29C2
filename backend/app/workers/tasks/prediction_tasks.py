# backend/app/workers/tasks/prediction_tasks.py
from __future__ import annotations

from datetime import datetime, timezone

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


def _get_db():
    from app.core.database import SessionLocal
    return SessionLocal()


@celery_app.task(
    name="app.workers.tasks.prediction_tasks.generate_predictions_for_today",
    bind=True,
)
def generate_predictions_for_today(self) -> dict:
    """Generate predictions for all of today's scheduled matches."""
    from app.models.match import Match, MatchStatus
    from app.models.prediction import Prediction, PredictionStatus
    from app.services.prediction_service import PredictionService

    db = _get_db()
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
                Match.status == MatchStatus.scheduled,
            )
            .all()
        )

        svc = PredictionService(db)
        created = 0
        errors = 0
        markets = ["1x2", "over_under_25", "btts"]

        for match in matches:
            for market in markets:
                # Skip if prediction already exists
                from app.models.prediction import PredictionMarket

                market_enum_map = {
                    "1x2": PredictionMarket.one_x_two,
                    "over_under_25": PredictionMarket.over_under_25,
                    "btts": PredictionMarket.btts,
                }
                existing = (
                    db.query(Prediction)
                    .filter(
                        Prediction.match_id == match.id,
                        Prediction.market == market_enum_map[market],
                        Prediction.status != PredictionStatus.rejected,
                    )
                    .first()
                )
                if existing:
                    continue

                try:
                    pred = svc.analyze_match(match.id, market)
                    # Auto-publish if it's a value bet with high confidence
                    if pred.is_value_bet and pred.confidence_level.value in ("high", "very_high"):
                        pred.status = PredictionStatus.published
                        db.commit()
                    created += 1
                except Exception as exc:
                    logger.warning(
                        "prediction_generation_failed",
                        match_id=match.id,
                        market=market,
                        error=str(exc),
                    )
                    errors += 1

        result = {"created": created, "errors": errors, "matches": len(matches)}
        logger.info("generate_predictions_complete", **result)
        return result

    except Exception as exc:
        db.rollback()
        logger.error("generate_predictions_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300, max_retries=2)
    finally:
        db.close()


@celery_app.task(
    name="app.workers.tasks.prediction_tasks.recalculate_integrity_scores",
    bind=True,
)
def recalculate_integrity_scores(self) -> dict:
    """Recalculate integrity scores for today's matches."""
    from app.models.match import Match, MatchStatus
    from app.services.integrity_service import IntegrityService

    db = _get_db()
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
                Match.status == MatchStatus.scheduled,
            )
            .all()
        )

        svc = IntegrityService(db)
        processed = 0
        errors = 0

        for match in matches:
            try:
                svc.calculate_integrity_score(match.id)
                processed += 1
            except Exception as exc:
                logger.warning(
                    "integrity_recalc_failed", match_id=match.id, error=str(exc)
                )
                errors += 1

        result = {"processed": processed, "errors": errors}
        logger.info("recalculate_integrity_complete", **result)
        return result

    except Exception as exc:
        db.rollback()
        logger.error("recalculate_integrity_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=120, max_retries=2)
    finally:
        db.close()


@celery_app.task(
    name="app.workers.tasks.prediction_tasks.evaluate_completed_predictions",
    bind=True,
)
def evaluate_completed_predictions(self) -> dict:
    """Mark predictions as expired if their match has finished."""
    from app.models.match import Match, MatchStatus
    from app.models.prediction import Prediction, PredictionStatus

    db = _get_db()
    try:
        # Find finished matches
        finished_matches = (
            db.query(Match).filter(Match.status == MatchStatus.finished).all()
        )
        match_ids = [m.id for m in finished_matches]

        if not match_ids:
            return {"expired": 0}

        # Expire any pending predictions for finished matches
        pending_preds = (
            db.query(Prediction)
            .filter(
                Prediction.match_id.in_(match_ids),
                Prediction.status == PredictionStatus.pending,
            )
            .all()
        )

        for pred in pending_preds:
            pred.status = PredictionStatus.expired

        db.commit()
        result = {"expired": len(pending_preds), "finished_matches": len(finished_matches)}
        logger.info("evaluate_completed_predictions_done", **result)
        return result

    except Exception as exc:
        db.rollback()
        logger.error("evaluate_completed_predictions_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60, max_retries=3)
    finally:
        db.close()

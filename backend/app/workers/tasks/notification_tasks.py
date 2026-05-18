# backend/app/workers/tasks/notification_tasks.py
from __future__ import annotations

from datetime import datetime, timezone

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


def _get_db():
    from app.core.database import SessionLocal
    return SessionLocal()


# ---------------------------------------------------------------------------
# Helper: Telegram notification
# ---------------------------------------------------------------------------

def _send_telegram(telegram_id: str, message: str) -> bool:
    """Send a Telegram message.  Returns True on success."""
    from app.core.config import settings

    if not settings.TELEGRAM_BOT_TOKEN or not telegram_id:
        return False
    try:
        import httpx

        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        resp = httpx.post(
            url,
            json={"chat_id": telegram_id, "text": message, "parse_mode": "HTML"},
            timeout=10.0,
        )
        return resp.status_code == 200
    except Exception as exc:
        logger.warning("telegram_send_failed", telegram_id=telegram_id, error=str(exc))
        return False


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@celery_app.task(
    name="app.workers.tasks.notification_tasks.send_daily_value_bets_digest",
    bind=True,
)
def send_daily_value_bets_digest(self) -> dict:
    """Send a morning digest of today's value bets to premium subscribers."""
    from app.models.alert import Alert, AlertType
    from app.models.match import Match
    from app.models.prediction import Prediction, PredictionStatus
    from app.models.user import SubscriptionType, User

    db = _get_db()
    try:
        today_start = datetime.now(tz=timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_end = today_start.replace(hour=23, minute=59, second=59)

        value_bets = (
            db.query(Prediction)
            .join(Match)
            .filter(
                Prediction.is_value_bet == True,  # noqa: E712
                Prediction.status == PredictionStatus.published,
                Match.match_date >= today_start,
                Match.match_date <= today_end,
            )
            .order_by(Prediction.edge_percentage.desc())
            .limit(5)
            .all()
        )

        if not value_bets:
            return {"sent": 0, "skipped_no_bets": True}

        # Build digest text
        lines = [f"<b>BetBot AI – Daily Value Bets ({today_start.strftime('%d %b %Y')})</b>\n"]
        for pred in value_bets:
            match = pred.match
            lines.append(
                f"• {match.home_team} vs {match.away_team} | "
                f"{pred.market.value} → {pred.predicted_outcome.upper()} | "
                f"Odds: {pred.market_odds:.2f} | Edge: +{pred.edge_percentage:.1f}%"
            )
        message = "\n".join(lines)

        # Find users who subscribed to daily_summary alerts
        subscribed_users = (
            db.query(User)
            .join(Alert)
            .filter(
                Alert.alert_type == AlertType.daily_summary,
                User.is_active == True,  # noqa: E712
                User.subscription_type == SubscriptionType.premium,
            )
            .distinct()
            .all()
        )

        sent = 0
        for user in subscribed_users:
            if user.telegram_id:
                if _send_telegram(user.telegram_id, message):
                    sent += 1
            # Mark all pending daily_summary alerts for this user as sent
            pending_alerts = (
                db.query(Alert)
                .filter(
                    Alert.user_id == user.id,
                    Alert.alert_type == AlertType.daily_summary,
                    Alert.is_sent == False,  # noqa: E712
                )
                .all()
            )
            for alert in pending_alerts:
                alert.is_sent = True
                alert.sent_at = datetime.now(tz=timezone.utc)

        db.commit()
        result = {"sent": sent, "value_bets": len(value_bets)}
        logger.info("daily_digest_sent", **result)
        return result

    except Exception as exc:
        db.rollback()
        logger.error("daily_digest_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300, max_retries=2)
    finally:
        db.close()


@celery_app.task(
    name="app.workers.tasks.notification_tasks.send_high_risk_alerts",
    bind=True,
)
def send_high_risk_alerts(self) -> dict:
    """Alert users when a match they follow develops a high integrity risk."""
    from app.models.alert import Alert, AlertType
    from app.models.integrity import IntegrityScore, RiskLevel
    from app.models.match import Match, MatchStatus
    from app.models.user import User

    db = _get_db()
    try:
        today_start = datetime.now(tz=timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_end = today_start.replace(hour=23, minute=59, second=59)

        risky_scores = (
            db.query(IntegrityScore)
            .join(Match)
            .filter(
                IntegrityScore.risk_level.in_([RiskLevel.high, RiskLevel.critical]),
                Match.match_date >= today_start,
                Match.match_date <= today_end,
                Match.status == MatchStatus.scheduled,
            )
            .all()
        )

        sent = 0
        for score in risky_scores:
            match = score.match
            msg = (
                f"<b>Risk Warning</b>\n"
                f"{match.home_team} vs {match.away_team}\n"
                f"Integrity Risk: {score.risk_level.value.upper()} ({score.score:.0f}/100)\n"
                f"Recommendation: {score.recommendation.value.replace('_', ' ').title()}"
            )

            # Find users subscribed to risk_warning alerts
            risk_subscribers = (
                db.query(User)
                .join(Alert)
                .filter(
                    Alert.alert_type == AlertType.risk_warning,
                    Alert.is_sent == False,  # noqa: E712
                    User.is_active == True,  # noqa: E712
                )
                .distinct()
                .all()
            )

            for user in risk_subscribers:
                if user.telegram_id:
                    if _send_telegram(user.telegram_id, msg):
                        sent += 1

        result = {"sent": sent, "risky_matches": len(risky_scores)}
        logger.info("high_risk_alerts_sent", **result)
        return result

    except Exception as exc:
        db.rollback()
        logger.error("high_risk_alerts_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60, max_retries=3)
    finally:
        db.close()


@celery_app.task(
    name="app.workers.tasks.notification_tasks.process_pending_alerts",
    bind=True,
)
def process_pending_alerts(self) -> dict:
    """Process and dispatch all unsent alerts."""
    from app.models.alert import Alert, AlertType
    from app.models.user import User

    db = _get_db()
    try:
        pending = (
            db.query(Alert)
            .join(User)
            .filter(Alert.is_sent == False, User.is_active == True)  # noqa: E712
            .order_by(Alert.created_at)
            .limit(100)
            .all()
        )

        sent = 0
        failed = 0
        now = datetime.now(tz=timezone.utc)

        for alert in pending:
            user = alert.user
            if not user:
                continue

            dispatched = False
            if user.telegram_id:
                dispatched = _send_telegram(user.telegram_id, alert.message)

            if dispatched:
                alert.is_sent = True
                alert.sent_at = now
                sent += 1
            else:
                failed += 1

        db.commit()
        result = {"processed": len(pending), "sent": sent, "failed": failed}
        logger.info("process_pending_alerts_done", **result)
        return result

    except Exception as exc:
        db.rollback()
        logger.error("process_pending_alerts_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=30, max_retries=5)
    finally:
        db.close()

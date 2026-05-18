# backend/app/workers/celery_app.py
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "betbot",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks.data_ingestion",
        "app.workers.tasks.prediction_tasks",
        "app.workers.tasks.notification_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Beat schedule
    beat_schedule={
        # Data ingestion
        "ingest-todays-matches-every-2h": {
            "task": "app.workers.tasks.data_ingestion.ingest_todays_matches",
            "schedule": crontab(minute=0, hour="*/2"),
        },
        "update-odds-every-30min": {
            "task": "app.workers.tasks.data_ingestion.update_odds",
            "schedule": crontab(minute="*/30"),
        },
        "refresh-team-stats-daily": {
            "task": "app.workers.tasks.data_ingestion.refresh_team_stats",
            "schedule": crontab(hour=3, minute=0),
        },
        # Predictions
        "generate-predictions-daily": {
            "task": "app.workers.tasks.prediction_tasks.generate_predictions_for_today",
            "schedule": crontab(hour=7, minute=0),
        },
        "recalculate-integrity-daily": {
            "task": "app.workers.tasks.prediction_tasks.recalculate_integrity_scores",
            "schedule": crontab(hour=6, minute=30),
        },
        "evaluate-completed-predictions": {
            "task": "app.workers.tasks.prediction_tasks.evaluate_completed_predictions",
            "schedule": crontab(hour=23, minute=30),
        },
        # Notifications
        "send-daily-digest": {
            "task": "app.workers.tasks.notification_tasks.send_daily_value_bets_digest",
            "schedule": crontab(hour=8, minute=0),
        },
        "send-high-risk-alerts": {
            "task": "app.workers.tasks.notification_tasks.send_high_risk_alerts",
            "schedule": crontab(minute="*/15"),
        },
        "process-pending-alerts": {
            "task": "app.workers.tasks.notification_tasks.process_pending_alerts",
            "schedule": crontab(minute="*/5"),
        },
    },
)

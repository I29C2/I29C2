"""Configurare Celery. Toate joburile lungi (scraping, parsare, extracție) trec pe aici.

Scheduler-ul (beat) e definit declarativ mai jos — frecvența per sursă va veni din
config/DB în iterații viitoare, nu hardcodată în cod (vezi Ghidul Tehnic §2.3).
"""

from celery import Celery

from app.config import settings

celery = Celery(
    "funding",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.scraping.tasks",
        "app.documents.tasks",
        "app.ai.tasks",
    ],
)

celery.conf.update(
    task_track_started=True,
    task_time_limit=60 * 30,  # 30 min hard limit per task (Docling poate fi lent)
    worker_max_tasks_per_child=20,  # eliberează RAM după Docling
)

# TODO: mută în config per-sursă. Placeholder pentru o singură sursă zilnică.
celery.conf.beat_schedule = {
    "scrape-all-daily": {
        "task": "app.scraping.tasks.scrape_all_sources",
        "schedule": 60 * 60 * 24,  # zilnic; ajustabil
    },
}

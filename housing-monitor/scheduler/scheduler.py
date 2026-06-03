"""Periodic scheduling using APScheduler."""
from __future__ import annotations

import logging
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class MonitorScheduler:
    def __init__(self, interval_minutes: int, job: Callable[[], None]):
        self.interval_minutes = interval_minutes
        self.job = job
        self._scheduler = BackgroundScheduler()

    def start(self, run_on_start: bool = True) -> None:
        self._scheduler.add_job(
            self._safe_job,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id="scan",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info("Scheduler started (every %d min)", self.interval_minutes)
        if run_on_start:
            self._safe_job()

    def _safe_job(self) -> None:
        try:
            self.job()
        except Exception:  # a single failed scan must not kill the scheduler
            logger.exception("Scan job raised an exception")

    def shutdown(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

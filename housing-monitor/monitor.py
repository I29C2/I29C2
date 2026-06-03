"""Core monitoring orchestration: scrape -> dedup/store -> filter -> notify."""
from __future__ import annotations

import logging
from typing import List

from core.config import Config
from filters import FilterEngine
from notifications import TelegramNotifier
from scrapers import get_scraper
from storage import Database

logger = logging.getLogger(__name__)


class Monitor:
    def __init__(self, config: Config, db: Database, notifier: TelegramNotifier):
        self.config = config
        self.db = db
        self.notifier = notifier
        self.filter_engine = FilterEngine(config.filters)
        self._scrapers = self._build_scrapers()

    def _build_scrapers(self) -> list:
        scrapers = []
        for src in self.config.sources:
            try:
                cls = get_scraper(src["type"])
            except KeyError as exc:
                logger.error("Skipping source '%s': %s", src.get("name"), exc)
                continue
            scrapers.append(cls(src.get("name", src["type"]), src["url"], self.config.http))
        return scrapers

    def run_once(self) -> dict:
        """Run a full scan cycle across all sources. Returns a summary dict."""
        summary = {"scraped": 0, "new": 0, "matched": 0, "notified": 0}

        for scraper in self._scrapers:
            listings = scraper.extract_listings()
            summary["scraped"] += len(listings)
            self.db.record_scan(scraper.source_name, len(listings))

            for listing in listings:
                row_id, is_new = self.db.upsert(listing)
                if not is_new:
                    continue  # duplicate -> stored, ignored
                summary["new"] += 1

                result = self.filter_engine.evaluate(listing)
                if not result.matched:
                    logger.debug(
                        "Listing %s filtered out: %s", listing.listing_url, result.reasons
                    )
                    continue
                summary["matched"] += 1

                if self.notifier.send(listing):
                    self.db.mark_notified(row_id, status="sent")
                    summary["notified"] += 1
                else:
                    self.db.mark_notified(row_id, status="failed")

        logger.info(
            "Scan complete: %d scraped, %d new, %d matched, %d notified",
            summary["scraped"], summary["new"], summary["matched"], summary["notified"],
        )
        return summary

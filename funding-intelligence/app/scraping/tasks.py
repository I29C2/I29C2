"""Taskuri Celery pentru scraping. API-ul nu blochează niciodată pe astea.

Flux per sursă:
  healthcheck → (dacă ok) fetch → snapshot HTML → upsert apel → change detection
  → scrie funding_call_version → emit `call.new` / `call.changed`
  → (când apare ghid nou) declanșează app.documents.tasks.parse_document

TODO de completat:
- persistența (upsert FundingCall, scriere FundingCallVersion)
- emiterea evenimentelor (la MVP: un simplu log + flag; Slack/email amânate)
- alertă pe healthcheck eșuat
"""

import logging

from app.celery_app import celery
from app.scraping.registry import all_scrapers, get_scraper

logger = logging.getLogger(__name__)


@celery.task
def scrape_all_sources() -> None:
    """Declanșat de beat. Pune câte un task per sursă."""
    for scraper in all_scrapers():
        scrape_source.delay(scraper.source_id)


@celery.task
def scrape_source(source_id: str) -> None:
    scraper = get_scraper(source_id)

    health = scraper.healthcheck()
    if not health.ok:
        # NU scriem date goale. Alertă (Ghid Tehnic §2.3).
        logger.error("Scraper %s nesănătos: %s", source_id, health.message)
        # TODO: emite alertă operațională.
        return

    calls = scraper.fetch()
    logger.info("Scraper %s: %d apeluri", source_id, len(calls))
    # TODO: snapshot, upsert, change detection, versiuni, evenimente.

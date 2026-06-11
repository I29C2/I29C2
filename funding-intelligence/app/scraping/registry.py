"""Registru de scrapere. Adaugi o sursă nouă = o înregistrezi aici."""

from app.scraping.base import BaseScraper
from app.scraping.sources.example_source import ExampleScraper

# Cheie = source_id. La MVP pornim cu o singură sursă, făcută bine.
SCRAPERS: dict[str, BaseScraper] = {
    ExampleScraper.source_id: ExampleScraper(),
}


def get_scraper(source_id: str) -> BaseScraper:
    return SCRAPERS[source_id]


def all_scrapers() -> list[BaseScraper]:
    return list(SCRAPERS.values())

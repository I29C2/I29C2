"""Interfața comună a scraperelor + tipurile de date brute.

Un modul per sursă (scraping/sources/*.py), toate implementând BaseScraper.
La MVP: httpx + BeautifulSoup. Playwright doar dacă o sursă chiar cere JS.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Protocol, runtime_checkable


@dataclass
class RawCallData:
    """Date brute normalizate dintr-o sursă, înainte de mapare la schema canonică."""

    source_id: str
    external_id: str            # id-ul apelului la sursă (pentru deduplicare)
    title: str
    url_official: str
    program: str | None = None
    axis: str | None = None
    status: str | None = None
    budget_total: float | None = None
    deadline_submission: date | None = None
    raw_fields: dict = field(default_factory=dict)  # tot ce mai prinde scraperul


@dataclass
class ScraperHealth:
    """Rezultatul healthcheck-ului (Ghid Tehnic §2.3): 0 rezultate / selectori lipsă = alertă."""

    source_id: str
    ok: bool
    results_count: int
    message: str = ""


@runtime_checkable
class BaseScraper(Protocol):
    source_id: str

    def fetch(self) -> list[RawCallData]:
        """Întoarce apelurile curente de la sursă. Snapshot HTML se arhivează separat."""
        ...

    def healthcheck(self) -> ScraperHealth:
        """Verifică dacă structura paginii încă conține selectorii așteptați."""
        ...

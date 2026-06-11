"""Sursă-șablon. Copiezi fișierul ăsta pentru fiecare sursă reală.

RISCUL REAL al fazei de scraping (Ghid Tehnic): nu fetch-ul, ci NORMALIZAREA
anti-zgomot la change detection. Vezi change_detection.py.

De respectat:
- rate-limit per domeniu (settings.scraper_rate_limit_seconds)
- User-Agent identificabil
- robots.txt verificat per sursă în checklist-ul legal (track Securitate)
- snapshot HTML arhivat la fiecare rulare (debugging pe snapshot, nu pe live)
"""

import httpx

from app.config import settings
from app.scraping.base import BaseScraper, RawCallData, ScraperHealth

USER_AGENT = "TeamILabsFundingBot/0.1 (+contact@example.com)"


class ExampleScraper(BaseScraper):
    source_id = "example"
    base_url = "https://example.gov.ro/apeluri"

    def _client(self) -> httpx.Client:
        return httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )

    def fetch(self) -> list[RawCallData]:
        # TODO: GET + BeautifulSoup, mapează la RawCallData.
        # TODO: arhivează HTML-ul brut (snapshot) înainte de parsare.
        # TODO: respectă settings.scraper_rate_limit_seconds între requesturi.
        raise NotImplementedError("Implementare per sursă reală")

    def healthcheck(self) -> ScraperHealth:
        # TODO: GET pagina, verifică prezența selectorilor-cheie.
        # 0 rezultate / selectori lipsă → ok=False (alertă, NU scriere de date goale).
        return ScraperHealth(
            source_id=self.source_id,
            ok=False,
            results_count=0,
            message="Neimplementat — șablon",
        )

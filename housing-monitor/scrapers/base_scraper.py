"""Base scraper with HTTP fetching, retries and a clean extension interface."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from models import Listing

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Interface every provider scraper must implement.

    Subclasses implement :meth:`parse`. The base class provides
    :meth:`fetch` (HTTP with retry/backoff) and :meth:`extract_listings`
    which ties fetch + parse together.
    """

    #: human readable source name; overridden via config `name`
    source_name: str = "Generic"

    def __init__(self, name: str, url: str, http_config: dict | None = None):
        self.source_name = name
        self.url = url
        http = http_config or {}
        self.timeout = int(http.get("timeout_seconds", 30))
        self.retries = int(http.get("retries", 3))
        self.backoff = float(http.get("backoff_seconds", 2))
        self.user_agent = http.get(
            "user_agent",
            "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        )
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            }
        )

    def fetch(self) -> str:
        """Download the page HTML with retry + exponential backoff."""

        @retry(
            stop=stop_after_attempt(self.retries),
            wait=wait_exponential(multiplier=self.backoff, min=self.backoff, max=60),
            retry=retry_if_exception_type(requests.RequestException),
            reraise=True,
        )
        def _do_fetch() -> str:
            logger.debug("Fetching %s", self.url)
            resp = self._session.get(self.url, timeout=self.timeout)
            resp.raise_for_status()
            return resp.text

        return _do_fetch()

    @abstractmethod
    def parse(self, html: str) -> List[Listing]:
        """Parse HTML into a list of normalized :class:`Listing` objects."""
        raise NotImplementedError

    def extract_listings(self) -> List[Listing]:
        """Fetch then parse. Returns [] on hard failure (already logged)."""
        try:
            html = self.fetch()
        except requests.RequestException as exc:
            logger.error("Failed to fetch %s after retries: %s", self.source_name, exc)
            return []
        try:
            listings = self.parse(html)
        except Exception:  # parsing must never crash the scheduler
            logger.exception("Failed to parse listings for %s", self.source_name)
            return []
        logger.info("%s: extracted %d listing(s)", self.source_name, len(listings))
        return listings

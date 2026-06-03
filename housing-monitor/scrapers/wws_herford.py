"""Scraper for WWS Herford (https://www.wws-herford.de/wohnen/wohnungsangebote).

Strategy
--------
1. Fetch the overview/listings page → collect (detail_url, title) pairs.
   The title comes from the card text on the overview page (correct).
2. For each detail URL, fetch the detail page.
3. Extract labelled fields from the full page text using strict, named patterns:
      Zimmer          → integer 1-9
      Wohnfläche      → decimal, plausible area (5-500 m²)
      Verfügbar ab    → strict DD.MM.YYYY or "sofort"
      Kaltmiete       → decimal, plausible rent (50-9999 €)
   These patterns are immune to UUID strings, postal codes and button text.
"""
from __future__ import annotations

import logging
import re
import time
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from models import Listing, parse_number
from .base_scraper import BaseScraper
from .registry import register

logger = logging.getLogger(__name__)

# --- strict field patterns on flat page text ---------------------------------
# Each pattern anchors on the German label and captures only the value token
# immediately after it — preventing UUID / postal-code false positives.

_F_ROOMS = re.compile(
    r"Zimmer\s*:?\s*(\d(?:[.,]\d)?)\b",   # 1-9 rooms, no 5-digit postal codes
    re.I,
)
_F_AREA = re.compile(
    r"Wohnfl[äa]che\s*:?\s*(\d{2,3}(?:[.,]\d{1,2})?)\s*m",  # 10-999 m²
    re.I,
)
_F_AVAIL = re.compile(
    r"Verf[üu]gbar(?:\s+ab)?\s*:?\s*(\d{1,2}[.]\d{1,2}[.]\d{4}|sofort|ab\s+sofort)",
    re.I,
)
_F_KALT = re.compile(
    r"Kaltmiete\s*:?\s*(\d{2,4}(?:[.,]\d{1,2})?)\s*[€E]",  # 10-9999 €
    re.I,
)
_F_WARM = re.compile(
    r"(?:Warmmiete|Gesamtmiete)\s*:?\s*(\d{2,4}(?:[.,]\d{1,2})?)\s*[€E]",
    re.I,
)
_F_EXTRA = re.compile(
    r"Nebenkosten\s*:?\s*(\d{2,4}(?:[.,]\d{1,2})?)\s*[€E]",
    re.I,
)
_WBS_RE = re.compile(r"\bWBS\b|Wohnberechtigungsschein", re.I)

# Candidate selectors for overview page links
_LINK_SELECTORS = [
    "a[href*='/detail/']",
    "a[href*='wohnungsangebote/']",
    "[class*='wohnung'] a",
    "[class*='angebot'] a",
    "article a",
]


@register("wws_herford")
class WWSHerfordScraper(BaseScraper):
    source_name = "WWS Herford"

    _DETAIL_DELAY = 1.5  # polite delay between detail requests (seconds)

    # -----------------------------------------------------------------
    def extract_listings(self) -> List[Listing]:
        """Fetch overview → collect links → fetch each detail page."""
        try:
            overview_html = self.fetch()
        except Exception as exc:
            logger.error("Failed to fetch overview %s: %s", self.source_name, exc)
            return []

        links = self._collect_detail_links(overview_html)
        if not links:
            logger.warning("%s: no detail links found on overview page", self.source_name)
            return []

        logger.info("%s: found %d detail link(s)", self.source_name, len(links))
        listings: List[Listing] = []
        for url, title in links:
            listing = self._fetch_and_parse_detail(url, title)
            if listing:
                listings.append(listing)
            time.sleep(self._DETAIL_DELAY)

        logger.info("%s: extracted %d listing(s)", self.source_name, len(listings))
        return listings

    def parse(self, html: str) -> List[Listing]:
        """Parse a detail page directly (used in unit tests)."""
        return [self._parse_detail(self.url, "", html)]

    # -----------------------------------------------------------------
    def _collect_detail_links(self, html: str) -> List[tuple[str, str]]:
        """Return [(abs_url, title_text), ...] from the overview page."""
        soup = BeautifulSoup(html, "lxml")
        seen: set[str] = set()
        results: list[tuple[str, str]] = []

        for selector in _LINK_SELECTORS:
            for a in soup.select(selector):
                href = a.get("href", "")
                if not href:
                    continue
                url = urljoin(self.url, href)
                if url == self.url or url in seen:
                    continue
                seen.add(url)
                # Title: text of the anchor or its closest heading sibling/parent
                title = self._extract_title_near(a)
                results.append((url, title))
            if results:
                break

        return results

    @staticmethod
    def _extract_title_near(anchor) -> str:
        """Find the best title text near a listing anchor on the overview page."""
        # Look for a heading inside the anchor itself
        for tag in ("h1", "h2", "h3", "h4"):
            el = anchor.find(tag)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)

        # Walk up to find a heading sibling
        parent = anchor.parent
        for _ in range(4):
            if parent is None:
                break
            for tag in ("h1", "h2", "h3", "h4"):
                el = parent.find(tag)
                if el and el.get_text(strip=True):
                    return el.get_text(strip=True)
            parent = parent.parent

        # Last resort: anchor text itself (may be "Mehr erfahren" etc.)
        txt = anchor.get_text(strip=True)
        return txt if txt else "Wohnungsangebot"

    # -----------------------------------------------------------------
    def _fetch_and_parse_detail(self, url: str, title: str) -> Optional[Listing]:
        try:
            resp = self._session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            html = resp.text
        except Exception as exc:
            logger.warning("Could not fetch detail %s: %s", url, exc)
            return None
        try:
            return self._parse_detail(url, title, html)
        except Exception:
            logger.exception("Failed to parse detail page %s", url)
            return None

    def _parse_detail(self, url: str, hint_title: str, html: str) -> Listing:
        soup = BeautifulSoup(html, "lxml")

        # Flat text — used for strict regex matching.
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))

        # --- title: prefer hint from overview (h1 on detail = address) ---
        title = hint_title.strip()
        if not title:
            # Try h2/h3 which sometimes holds the listing name
            for tag in ("h2", "h3", "h1"):
                el = soup.find(tag)
                if el and el.get_text(strip=True):
                    title = el.get_text(strip=True)
                    break

        rooms     = self._match_num(_F_ROOMS,  text)
        area      = self._match_num(_F_AREA,   text)
        rent_cold = self._match_num(_F_KALT,   text)
        rent_warm = self._match_num(_F_WARM,   text)
        extra     = self._match_num(_F_EXTRA,  text)
        avail     = self._match_str(_F_AVAIL,  text)

        return Listing(
            source=self.source_name,
            listing_url=url,
            title=title or "Wohnungsangebot",
            rooms=rooms,
            area=area,
            rent_cold=rent_cold,
            extra_costs=extra,
            rent_warm=rent_warm,
            available_date=avail,
            wbs_required=bool(_WBS_RE.search(text)),
            raw_text=text,
        )

    # -----------------------------------------------------------------
    @staticmethod
    def _match_num(pattern: re.Pattern, text: str) -> Optional[float]:
        m = pattern.search(text)
        return parse_number(m.group(1)) if m else None

    @staticmethod
    def _match_str(pattern: re.Pattern, text: str) -> Optional[str]:
        m = pattern.search(text)
        return m.group(1).strip() if m else None

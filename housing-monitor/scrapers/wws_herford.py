"""Scraper for WWS Herford (https://www.wws-herford.de/wohnen/wohnungsangebote).

NOTE ON SELECTORS
-----------------
The live site blocks unauthenticated inspection, so the exact CSS class
names could not be confirmed at build time. This scraper therefore uses a
*heuristic* approach: it finds candidate listing blocks (containers that
link to a detail page and contain rent/room/area patterns) and extracts
fields via labelled regex. If WWS publishes a stable markup you can pin
exact selectors by overriding ``LISTING_SELECTOR`` / field selectors.

The heuristic is intentionally defensive so a markup change degrades
gracefully (fewer fields) rather than crashing.
"""
from __future__ import annotations

import logging
import re
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from models import Listing, parse_number
from .base_scraper import BaseScraper
from .registry import register

logger = logging.getLogger(__name__)

# Candidate container selectors, tried in order. First that yields blocks wins.
_CANDIDATE_SELECTORS = [
    "[class*='wohnung']",
    "[class*='angebot']",
    "[class*='immobilie']",
    "[class*='listing']",
    "article",
    "li[class*='item']",
    ".teaser",
]

_ROOMS_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:Zimmer|Zi\.?|Zimmern)", re.I)
_AREA_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:m²|m2|qm|Wohnfläche)", re.I)
_RENT_WARM_RE = re.compile(r"(?:Warmmiete|warm|Gesamtmiete)\D{0,15}(\d+(?:[.,]\d+)?)", re.I)
_RENT_COLD_RE = re.compile(r"(?:Kaltmiete|kalt|Nettomiete|Grundmiete)\D{0,15}(\d+(?:[.,]\d+)?)", re.I)
_EXTRA_RE = re.compile(r"(?:Nebenkosten|Betriebskosten|NK)\D{0,15}(\d+(?:[.,]\d+)?)", re.I)
_GENERIC_RENT_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:€|EUR)", re.I)
_DATE_RE = re.compile(r"(\d{1,2}[./]\d{1,2}[./]\d{2,4}|sofort|ab sofort)", re.I)
_ADDR_RE = re.compile(r"\d{5}\s+\w+|[A-ZÄÖÜ][\wäöüß.\-]+(?:straße|str\.?|weg|platz|allee|ring)\s*\d*", re.I)
_WBS_RE = re.compile(r"\bWBS\b|Wohnberechtigungsschein", re.I)
_ID_RE = re.compile(r"(?:Objekt(?:nummer|-?nr)\.?|ID)[\s:#]{0,5}([A-Za-z0-9][A-Za-z0-9\-]*)", re.I)


@register("wws_herford")
class WWSHerfordScraper(BaseScraper):
    source_name = "WWS Herford"

    def parse(self, html: str) -> List[Listing]:
        soup = BeautifulSoup(html, "lxml")
        blocks = self._find_listing_blocks(soup)
        listings: List[Listing] = []
        seen_urls: set[str] = set()

        for block in blocks:
            listing = self._parse_block(block)
            if listing is None:
                continue
            # Within a single page, avoid emitting the same URL twice.
            if listing.listing_url in seen_urls:
                continue
            seen_urls.add(listing.listing_url)
            listings.append(listing)

        return listings

    # --- helpers -----------------------------------------------------------
    def _find_listing_blocks(self, soup: BeautifulSoup):
        for selector in _CANDIDATE_SELECTORS:
            blocks = soup.select(selector)
            # Keep only blocks that look like a listing (a link + numbers).
            candidates = [
                b for b in blocks
                if b.find("a", href=True) and (_ROOMS_RE.search(b.get_text(" ")) or _GENERIC_RENT_RE.search(b.get_text(" ")))
            ]
            if candidates:
                logger.debug("Using selector '%s' -> %d blocks", selector, len(candidates))
                return candidates
        logger.warning("%s: no listing blocks matched any known selector", self.source_name)
        return []

    def _parse_block(self, block) -> Optional[Listing]:
        text = block.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text)

        link = block.find("a", href=True)
        if not link:
            return None
        listing_url = urljoin(self.url, link["href"])

        title = self._first_text(block, ["h1", "h2", "h3", "h4", "[class*='title']"]) \
            or link.get_text(strip=True) or "Wohnungsangebot"

        rooms = self._search_num(_ROOMS_RE, text)
        area = self._search_num(_AREA_RE, text)
        rent_warm = self._search_num(_RENT_WARM_RE, text)
        rent_cold = self._search_num(_RENT_COLD_RE, text)
        extra = self._search_num(_EXTRA_RE, text)

        # Fallback: if no labelled rent found, take first generic €-amount.
        if rent_warm is None and rent_cold is None:
            generic = _GENERIC_RENT_RE.search(text)
            if generic:
                rent_cold = parse_number(generic.group(1))

        addr_match = _ADDR_RE.search(text)
        address = addr_match.group(0).strip() if addr_match else ""

        date_match = _DATE_RE.search(text)
        available = date_match.group(1) if date_match else None

        id_match = _ID_RE.search(text)
        listing_id = id_match.group(1) if id_match else None

        return Listing(
            source=self.source_name,
            listing_url=listing_url,
            title=title.strip(),
            address=address,
            rooms=rooms,
            area=area,
            rent_cold=rent_cold,
            extra_costs=extra,
            rent_warm=rent_warm,
            available_date=available,
            listing_id=listing_id,
            wbs_required=bool(_WBS_RE.search(text)),
            raw_text=text,
        )

    @staticmethod
    def _first_text(block, selectors) -> str:
        for sel in selectors:
            el = block.select_one(sel)
            if el and el.get_text(strip=True):
                return el.get_text(strip=True)
        return ""

    @staticmethod
    def _search_num(pattern: re.Pattern, text: str) -> Optional[float]:
        m = pattern.search(text)
        return parse_number(m.group(1)) if m else None

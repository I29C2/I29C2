"""Scraper for WWS Herford (https://www.wws-herford.de/wohnen/wohnungsangebote).

Strategy
--------
1. Fetch the overview/listings page and collect all detail-page URLs + titles.
2. For each detail URL, fetch the detail page where fields are presented as
   labelled pairs (label on one line, value on the next):

       Zimmer          → 2
       Wohnfläche      → 45,00 m²
       Verfügbar ab    → 01.07.2026
       Kaltmiete       → 365,00 €

   This is far more reliable than trying to parse the overview cards.
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

# --- detail-page label patterns (German, matched case-insensitively) ---------
_LBL_ROOMS   = re.compile(r"^zimmer$", re.I)
_LBL_AREA    = re.compile(r"wohnfl[äa]che", re.I)
_LBL_AVAIL   = re.compile(r"verf[üu]gbar", re.I)
_LBL_KALT    = re.compile(r"kaltmiete", re.I)
_LBL_WARM    = re.compile(r"warmmiete|gesamtmiete", re.I)
_LBL_EXTRA   = re.compile(r"nebenkosten|betriebskosten", re.I)
_LBL_ADDR    = re.compile(r"adresse|lage|anschrift", re.I)

_NUM_RE      = re.compile(r"\d+(?:[.,]\d+)?")
_DATE_RE     = re.compile(r"\d{1,2}[./]\d{1,2}[./]\d{2,4}|sofort|ab sofort", re.I)
_WBS_RE      = re.compile(r"\bWBS\b|Wohnberechtigungsschein", re.I)

# Candidate selectors for finding listing cards on the overview page.
_CARD_SELECTORS = [
    "a[href*='/detail/']",
    "a[href*='wohnungsangebote']",
    "[class*='wohnung'] a",
    "[class*='angebot'] a",
    "[class*='listing'] a",
    "article a",
]


@register("wws_herford")
class WWSHerfordScraper(BaseScraper):
    source_name = "WWS Herford"

    # Polite delay between detail-page requests (seconds).
    _DETAIL_DELAY = 1.5

    def extract_listings(self) -> List[Listing]:
        """Override: fetch overview then each detail page."""
        try:
            html = self.fetch()
        except Exception as exc:
            logger.error("Failed to fetch overview %s: %s", self.source_name, exc)
            return []

        links = self._collect_detail_links(html)
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
        """Fallback: parse a detail page directly (used in tests)."""
        return [self._parse_detail_page(self.url, "", html)]

    # --- overview parsing ---------------------------------------------------
    def _collect_detail_links(self, html: str) -> List[tuple[str, str]]:
        """Return [(absolute_url, title), ...] from the overview page."""
        soup = BeautifulSoup(html, "lxml")
        seen: set[str] = set()
        results: List[tuple[str, str]] = []

        for selector in _CARD_SELECTORS:
            anchors = soup.select(selector)
            for a in anchors:
                href = a.get("href", "")
                if not href:
                    continue
                url = urljoin(self.url, href)
                # Only keep detail URLs (not the overview itself).
                if url == self.url or url in seen:
                    continue
                seen.add(url)
                title = a.get_text(" ", strip=True) or a.get("title", "") or ""
                results.append((url, title))
            if results:
                break

        return results

    # --- detail page --------------------------------------------------------
    def _fetch_and_parse_detail(self, url: str, hint_title: str) -> Optional[Listing]:
        try:
            html = self._session.get(url, timeout=self.timeout).text
        except Exception as exc:
            logger.warning("Could not fetch detail %s: %s", url, exc)
            return None
        try:
            return self._parse_detail_page(url, hint_title, html)
        except Exception:
            logger.exception("Failed to parse detail page %s", url)
            return None

    def _parse_detail_page(self, url: str, hint_title: str, html: str) -> Listing:
        soup = BeautifulSoup(html, "lxml")
        full_text = soup.get_text(" ", strip=True)
        full_text = re.sub(r"\s+", " ", full_text)

        # --- title: prefer <h1> / <h2>, fall back to hint ---
        title = ""
        for tag in ("h1", "h2"):
            el = soup.find(tag)
            if el and el.get_text(strip=True):
                title = el.get_text(strip=True)
                break
        if not title:
            title = hint_title

        # --- labelled field extraction ---
        fields = self._extract_labeled_fields(soup)

        rooms      = fields.get("rooms")
        area       = fields.get("area")
        rent_cold  = fields.get("rent_cold")
        rent_warm  = fields.get("rent_warm")
        extra      = fields.get("extra_costs")
        avail      = fields.get("available_date")
        address    = fields.get("address", "")

        return Listing(
            source=self.source_name,
            listing_url=url,
            title=title.strip(),
            address=address,
            rooms=rooms,
            area=area,
            rent_cold=rent_cold,
            extra_costs=extra,
            rent_warm=rent_warm,
            available_date=avail,
            wbs_required=bool(_WBS_RE.search(full_text)),
            raw_text=full_text,
        )

    def _extract_labeled_fields(self, soup: BeautifulSoup) -> dict:
        """Walk all text nodes; when a node matches a field label, the next
        sibling/node is the value."""
        fields: dict = {}

        # Strategy A: look for <dt>/<dd> definition lists.
        for dt in soup.find_all("dt"):
            label = dt.get_text(strip=True)
            dd = dt.find_next_sibling("dd")
            value = dd.get_text(" ", strip=True) if dd else ""
            self._assign_field(fields, label, value)

        # Strategy B: pairs of consecutive leaf elements sharing a parent.
        if not fields:
            for parent in soup.find_all(True):
                children = [c for c in parent.children
                            if hasattr(c, "get_text") and c.get_text(strip=True)]
                for i in range(len(children) - 1):
                    label = children[i].get_text(strip=True)
                    value = children[i + 1].get_text(strip=True)
                    self._assign_field(fields, label, value)

        # Strategy C: flat text scan for "Label Value" patterns.
        if not fields:
            text = soup.get_text(" ", strip=True)
            for label_re, key, parser in [
                (_LBL_ROOMS, "rooms",         self._parse_num),
                (_LBL_AREA,  "area",          self._parse_num),
                (_LBL_KALT,  "rent_cold",     self._parse_num),
                (_LBL_WARM,  "rent_warm",     self._parse_num),
                (_LBL_EXTRA, "extra_costs",   self._parse_num),
                (_LBL_AVAIL, "available_date", self._parse_date),
            ]:
                m = re.search(
                    label_re.pattern + r"\s*:?\s*(\d[\d.,\s/]+\S*)", text, re.I
                )
                if m and key not in fields:
                    fields[key] = parser(m.group(1))

        return fields

    def _assign_field(self, fields: dict, label: str, value: str) -> None:
        if not value:
            return
        if _LBL_ROOMS.search(label)  and "rooms"          not in fields:
            fields["rooms"]          = self._parse_num(value)
        elif _LBL_AREA.search(label) and "area"           not in fields:
            fields["area"]           = self._parse_num(value)
        elif _LBL_KALT.search(label) and "rent_cold"      not in fields:
            fields["rent_cold"]      = self._parse_num(value)
        elif _LBL_WARM.search(label) and "rent_warm"      not in fields:
            fields["rent_warm"]      = self._parse_num(value)
        elif _LBL_EXTRA.search(label) and "extra_costs"   not in fields:
            fields["extra_costs"]    = self._parse_num(value)
        elif _LBL_AVAIL.search(label) and "available_date" not in fields:
            fields["available_date"] = self._parse_date(value)
        elif _LBL_ADDR.search(label)  and "address"       not in fields:
            fields["address"]        = value.strip()

    @staticmethod
    def _parse_num(text: str) -> Optional[float]:
        return parse_number(text)

    @staticmethod
    def _parse_date(text: str) -> Optional[str]:
        m = _DATE_RE.search(text)
        return m.group(0) if m else text.strip()

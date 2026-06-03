"""Listing data model and normalization helpers."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Optional


@dataclass
class Listing:
    """A normalized housing listing as produced by any scraper.

    All scrapers must return objects of this type so that downstream
    components (filter engine, storage, notifier) are source-agnostic.
    """

    source: str
    listing_url: str
    title: str = ""
    address: str = ""
    rooms: Optional[float] = None
    area: Optional[float] = None          # living area in sqm
    rent_cold: Optional[float] = None     # Kaltmiete
    extra_costs: Optional[float] = None   # Nebenkosten
    rent_warm: Optional[float] = None     # Warmmiete
    available_date: Optional[str] = None  # ISO date string or free text
    listing_id: Optional[str] = None      # provider-side id, if any
    wbs_required: bool = False
    raw_text: str = ""                    # full text used for keyword matching
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    @property
    def effective_rent(self) -> Optional[float]:
        """Rent used for filtering: warm rent when known, else cold rent."""
        if self.rent_warm is not None:
            return self.rent_warm
        return self.rent_cold

    @property
    def fingerprint(self) -> str:
        """Stable identifier used for duplicate detection.

        Priority: listing_url -> listing_id -> (title + address).
        """
        basis = (
            self.listing_url.strip()
            or (self.listing_id or "").strip()
            or f"{self.title.strip().lower()}|{self.address.strip().lower()}"
        )
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()

    @property
    def available_as_date(self) -> Optional[date]:
        """Best-effort parse of available_date into a date object.

        Returns None if it cannot be parsed or means 'immediately'.
        """
        return parse_german_date(self.available_date)

    def to_dict(self) -> dict:
        return asdict(self)


# --- normalization helpers -------------------------------------------------

_NUM_RE = re.compile(r"(\d+(?:[.,]\d+)?)")


def parse_number(value) -> Optional[float]:
    """Parse a German-formatted number from arbitrary text.

    Handles '1.234,56', '589 €', '3 Zimmer', '72 m²', etc.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value)
    # Remove thousands separators (dots) when followed by 3 digits, then
    # convert decimal comma to dot.
    cleaned = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", text)
    cleaned = cleaned.replace(",", ".")
    match = _NUM_RE.search(cleaned)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


_DATE_FORMATS = ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d", "%d/%m/%Y")

_IMMEDIATE_TOKENS = ("sofort", "ab sofort", "immediately", "now", "verfügbar")


def parse_german_date(value: Optional[str]) -> Optional[date]:
    """Parse common German date strings. 'sofort'/empty -> None (means now)."""
    if not value:
        return None
    text = value.strip().lower()
    if any(tok in text for tok in _IMMEDIATE_TOKENS) and not _NUM_RE.search(text):
        return None
    m = re.search(r"\d{1,2}[./]\d{1,2}[./]\d{2,4}|\d{4}-\d{2}-\d{2}", value)
    candidate = m.group(0) if m else value.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(candidate, fmt).date()
        except ValueError:
            continue
    return None

"""Rule-based filtering of listings."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional

from models import Listing


@dataclass
class FilterResult:
    """Outcome of evaluating one listing against the rules."""

    listing: Listing
    matched: bool
    reasons: List[str] = field(default_factory=list)  # why it was rejected


class FilterEngine:
    """Evaluates listings against user-defined rules.

    A listing matches only if it passes every configured rule. Rules whose
    config value is ``None`` (or missing) are skipped. Unknown values (e.g.
    a listing with no detected rent) do not fail numeric rules — we prefer a
    false positive notification over silently dropping a possible match.
    """

    def __init__(self, filters: dict | None = None):
        self.f = filters or {}

    def evaluate(self, listing: Listing) -> FilterResult:
        reasons: List[str] = []

        self._check_range(reasons, listing.rooms, "min_rooms", "max_rooms", "rooms")
        self._check_range(reasons, listing.area, "min_area", "max_area", "area")
        self._check_range(reasons, listing.effective_rent, "min_rent", "max_rent", "rent")

        if self._truthy("exclude_wbs") and listing.wbs_required:
            reasons.append("WBS required")

        self._check_availability(reasons, listing)
        self._check_keywords(reasons, listing)

        return FilterResult(listing=listing, matched=not reasons, reasons=reasons)

    def filter(self, listings: List[Listing]) -> List[Listing]:
        return [r.listing for r in self.evaluate_all(listings) if r.matched]

    def evaluate_all(self, listings: List[Listing]) -> List[FilterResult]:
        return [self.evaluate(l) for l in listings]

    # --- individual rules --------------------------------------------------
    def _check_range(self, reasons, value, min_key, max_key, label) -> None:
        if value is None:
            return  # unknown -> don't reject
        lo = self.f.get(min_key)
        hi = self.f.get(max_key)
        if lo is not None and value < lo:
            reasons.append(f"{label} {value} < min {lo}")
        if hi is not None and value > hi:
            reasons.append(f"{label} {value} > max {hi}")

    def _check_availability(self, reasons, listing: Listing) -> None:
        months = self.f.get("available_within_months")
        if not months:
            return
        avail = listing.available_as_date
        if avail is None:
            return  # 'sofort' / unknown -> acceptable
        cutoff = date.today() + timedelta(days=int(months) * 31)
        if avail > cutoff:
            reasons.append(f"available {avail.isoformat()} after cutoff {cutoff.isoformat()}")

    def _check_keywords(self, reasons, listing: Listing) -> None:
        haystack = f"{listing.title} {listing.raw_text}".lower()

        excludes = [k.lower() for k in (self.f.get("keywords_exclude") or [])]
        for kw in excludes:
            if kw and kw in haystack:
                reasons.append(f"excluded keyword '{kw}'")

        includes = [k.lower() for k in (self.f.get("keywords_include") or [])]
        if includes and not any(kw in haystack for kw in includes if kw):
            reasons.append("no required keyword present")

    def _truthy(self, key: str) -> bool:
        return bool(self.f.get(key))

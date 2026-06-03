"""Notifier interface and shared message formatting."""
from __future__ import annotations

from abc import ABC, abstractmethod

from models import Listing


class BaseNotifier(ABC):
    """Base class for notification channels (Telegram, Email, Discord, ...)."""

    @abstractmethod
    def send(self, listing: Listing) -> bool:
        """Send a notification for a listing. Returns True on success."""
        raise NotImplementedError

    @staticmethod
    def format_listing(listing: Listing) -> str:
        """Human-readable alert message (Markdown-friendly, channel-agnostic)."""
        def fmt(value, suffix=""):
            return f"{value}{suffix}" if value is not None and value != "" else "—"

        return (
            "🏠 *Neue Wohnung gefunden!*\n\n"
            f"*Titel:* {fmt(listing.title)}\n"
            f"*Zimmer:* {fmt(listing.rooms)}\n"
            f"*Wohnfläche:* {fmt(listing.area, ' m²')}\n"
            f"*Kaltmiete:* {fmt(listing.rent_cold, ' €')}\n"
            f"*Verfügbar ab:* {fmt(listing.available_date)}\n"
            f"*Quelle:* {fmt(listing.source)}\n"
            f"*Link:* {fmt(listing.listing_url)}\n"
            f"*Erkannt:* {listing.detected_at}"
        )

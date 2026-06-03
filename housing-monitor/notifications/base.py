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
        """Human-readable message body (Markdown-friendly, channel-agnostic)."""
        def fmt(value, suffix=""):
            return f"{value}{suffix}" if value is not None and value != "" else "—"

        rent = listing.effective_rent
        return (
            "🏠 *New Apartment Found*\n\n"
            f"*Title:* {fmt(listing.title)}\n"
            f"*Rooms:* {fmt(listing.rooms)}\n"
            f"*Area:* {fmt(listing.area, ' m²')}\n"
            f"*Rent:* {fmt(rent, ' €')}\n"
            f"*Available:* {fmt(listing.available_date)}\n"
            f"*Source:* {fmt(listing.source)}\n"
            f"*Link:* {fmt(listing.listing_url)}\n"
            f"*Detected:* {listing.detected_at}"
        )

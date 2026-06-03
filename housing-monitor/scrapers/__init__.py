from .base_scraper import BaseScraper
from .registry import get_scraper, register, available_scrapers

# Import concrete scrapers so they self-register.
from . import wws_herford  # noqa: F401

__all__ = ["BaseScraper", "get_scraper", "register", "available_scrapers"]

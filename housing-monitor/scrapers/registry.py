"""Scraper registry so new providers can be added without touching core code."""
from __future__ import annotations

from typing import Callable, Type

from .base_scraper import BaseScraper

_REGISTRY: dict[str, Type[BaseScraper]] = {}


def register(type_name: str) -> Callable[[Type[BaseScraper]], Type[BaseScraper]]:
    """Class decorator registering a scraper under a config `type` name."""

    def _wrap(cls: Type[BaseScraper]) -> Type[BaseScraper]:
        _REGISTRY[type_name] = cls
        return cls

    return _wrap


def get_scraper(type_name: str) -> Type[BaseScraper]:
    if type_name not in _REGISTRY:
        raise KeyError(
            f"Unknown scraper type '{type_name}'. Available: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[type_name]


def available_scrapers() -> list[str]:
    return sorted(_REGISTRY)

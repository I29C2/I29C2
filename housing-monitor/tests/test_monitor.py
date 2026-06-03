"""Integration test for the full scrape->store->filter->notify cycle."""
from core.config import Config
from models import Listing
from monitor import Monitor
from storage import Database


class FakeNotifier:
    def __init__(self):
        self.sent = []

    def send(self, listing):
        self.sent.append(listing)
        return True


class FakeConfig(Config):
    """Config built directly from a dict (bypasses file loading)."""


def build_config(filters):
    return FakeConfig(raw={
        "scheduler": {"interval_minutes": 15},
        "storage": {"database_path": ":memory:"},
        "http": {},
        "sources": [{"name": "Fake", "type": "fake", "enabled": True, "url": "http://x"}],
        "filters": filters,
    })


def register_fake_scraper(listings):
    from scrapers.base_scraper import BaseScraper
    from scrapers.registry import register, _REGISTRY

    @register("fake")
    class FakeScraper(BaseScraper):
        def parse(self, html):
            return listings

        def extract_listings(self):
            return listings

    return FakeScraper


def test_full_cycle_notifies_matches():
    listings = [
        Listing(source="Fake", listing_url="http://x/1", title="3Z", rooms=3, area=72, rent_warm=589),
        Listing(source="Fake", listing_url="http://x/2", title="too big", rooms=9, area=200, rent_warm=2000),
    ]
    register_fake_scraper(listings)
    cfg = build_config({"min_rooms": 2, "max_rooms": 4, "max_rent": 650, "min_area": 50})
    db = Database(":memory:")
    notifier = FakeNotifier()
    mon = Monitor(cfg, db, notifier)

    summary = mon.run_once()
    assert summary["scraped"] == 2
    assert summary["new"] == 2
    assert summary["matched"] == 1
    assert summary["notified"] == 1
    assert len(notifier.sent) == 1
    db.close()


def test_duplicates_not_renotified():
    listings = [Listing(source="Fake", listing_url="http://x/1", rooms=3, area=72, rent_warm=500)]
    register_fake_scraper(listings)
    cfg = build_config({"min_rooms": 2})
    db = Database(":memory:")
    notifier = FakeNotifier()
    mon = Monitor(cfg, db, notifier)

    first = mon.run_once()
    assert first["notified"] == 1
    second = mon.run_once()
    assert second["new"] == 0
    assert second["notified"] == 0
    assert len(notifier.sent) == 1
    db.close()


def test_unknown_scraper_type_skipped():
    cfg = FakeConfig(raw={
        "scheduler": {"interval_minutes": 15},
        "storage": {"database_path": ":memory:"},
        "sources": [{"name": "Bad", "type": "does_not_exist", "enabled": True, "url": "http://x"}],
        "filters": {},
    })
    db = Database(":memory:")
    mon = Monitor(cfg, db, FakeNotifier())
    assert mon._scrapers == []
    summary = mon.run_once()
    assert summary["scraped"] == 0
    db.close()

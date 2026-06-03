import pytest

from models import Listing
from storage import Database


@pytest.fixture
def db():
    d = Database(":memory:")
    yield d
    d.close()


def make(url="http://x/1", **kw):
    return Listing(source="WWS", listing_url=url, title="T", **kw)


def test_insert_and_duplicate_detection(db):
    l = make()
    assert not db.exists(l)
    row_id, is_new = db.upsert(l)
    assert is_new and row_id > 0
    assert db.exists(l)

    row_id2, is_new2 = db.upsert(make())
    assert row_id2 == row_id and is_new2 is False


def test_distinct_listings(db):
    db.upsert(make(url="http://x/1"))
    _, is_new = db.upsert(make(url="http://x/2"))
    assert is_new
    assert db.stats()["total_listings"] == 2


def test_mark_notified_and_stats(db):
    row_id, _ = db.upsert(make())
    db.mark_notified(row_id, status="sent")
    s = db.stats()
    assert s["notified_listings"] == 1
    assert s["notifications_sent"] == 1


def test_record_scan_and_latest(db):
    db.upsert(make(url="http://x/1", rent_warm=500))
    db.upsert(make(url="http://x/2", rent_warm=600))
    db.record_scan("WWS", 2)
    rows = db.latest(5)
    assert len(rows) == 2
    assert db.stats()["last_scan"] is not None


def test_failed_notification_status(db):
    row_id, _ = db.upsert(make())
    db.mark_notified(row_id, status="failed")
    s = db.stats()
    assert s["notified_listings"] == 1
    assert s["notifications_sent"] == 0


def test_matched_returns_notified_only(db):
    r1, _ = db.upsert(make(url="http://x/1"))
    r2, _ = db.upsert(make(url="http://x/2"))
    db.mark_notified(r1, "sent")
    matched = db.matched(10)
    assert len(matched) == 1
    assert matched[0]["listing_url"] == "http://x/1"

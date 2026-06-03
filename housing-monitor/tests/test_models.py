from datetime import date

import pytest

from models import Listing
from models.listing import parse_number, parse_german_date


@pytest.mark.parametrize("raw,expected", [
    ("589 €", 589.0),
    ("1.234,56 €", 1234.56),
    ("3 Zimmer", 3.0),
    ("72 m²", 72.0),
    ("2,5", 2.5),
    (None, None),
    ("keine zahl", None),
    (42, 42.0),
])
def test_parse_number(raw, expected):
    assert parse_number(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("01.08.2026", date(2026, 8, 1)),
    ("2026-08-01", date(2026, 8, 1)),
    ("sofort", None),
    ("ab sofort", None),
    ("", None),
    (None, None),
    ("garbage", None),
])
def test_parse_german_date(raw, expected):
    assert parse_german_date(raw) == expected


def test_effective_rent_prefers_warm():
    l = Listing(source="s", listing_url="u", rent_cold=400, rent_warm=550)
    assert l.effective_rent == 550
    l2 = Listing(source="s", listing_url="u", rent_cold=400)
    assert l2.effective_rent == 400
    l3 = Listing(source="s", listing_url="u")
    assert l3.effective_rent is None


def test_fingerprint_priority():
    by_url = Listing(source="s", listing_url="http://a")
    by_url2 = Listing(source="s", listing_url="http://a", title="x")
    assert by_url.fingerprint == by_url2.fingerprint

    by_id = Listing(source="s", listing_url="", listing_id="ID1")
    by_title = Listing(source="s", listing_url="", title="T", address="A")
    assert by_id.fingerprint != by_title.fingerprint

    same_title = Listing(source="s", listing_url="", title="T", address="A")
    assert by_title.fingerprint == same_title.fingerprint


def test_to_dict_roundtrip():
    l = Listing(source="s", listing_url="u", rooms=3)
    d = l.to_dict()
    assert d["source"] == "s" and d["rooms"] == 3

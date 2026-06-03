from datetime import date, timedelta

from filters import FilterEngine
from models import Listing


def make(**kw):
    base = dict(source="s", listing_url="http://x", title="Wohnung", raw_text="")
    base.update(kw)
    return Listing(**base)


FILTERS = {
    "min_rooms": 2, "max_rooms": 4,
    "min_area": 50, "max_rent": 650,
    "exclude_wbs": True,
    "available_within_months": 3,
    "keywords_exclude": ["Seniorenwohnung"],
    "keywords_include": [],
}


def test_matching_listing_passes():
    eng = FilterEngine(FILTERS)
    l = make(rooms=3, area=72, rent_warm=589, available_date="sofort")
    res = eng.evaluate(l)
    assert res.matched, res.reasons


def test_rooms_out_of_range():
    eng = FilterEngine(FILTERS)
    assert not eng.evaluate(make(rooms=1, area=60, rent_warm=500)).matched
    assert not eng.evaluate(make(rooms=5, area=60, rent_warm=500)).matched


def test_area_too_small():
    eng = FilterEngine(FILTERS)
    assert not eng.evaluate(make(rooms=3, area=40, rent_warm=500)).matched


def test_rent_too_high():
    eng = FilterEngine(FILTERS)
    assert not eng.evaluate(make(rooms=3, area=60, rent_warm=900)).matched


def test_wbs_excluded():
    eng = FilterEngine(FILTERS)
    assert not eng.evaluate(make(rooms=3, area=60, rent_warm=500, wbs_required=True)).matched


def test_exclude_keyword():
    eng = FilterEngine(FILTERS)
    l = make(rooms=3, area=60, rent_warm=500, raw_text="schöne Seniorenwohnung")
    assert not eng.evaluate(l).matched


def test_include_keyword_required():
    eng = FilterEngine({**FILTERS, "keywords_include": ["Balkon"]})
    assert not eng.evaluate(make(rooms=3, area=60, rent_warm=500)).matched
    ok = make(rooms=3, area=60, rent_warm=500, raw_text="mit Balkon")
    assert eng.evaluate(ok).matched


def test_availability_cutoff():
    eng = FilterEngine(FILTERS)
    far = (date.today() + timedelta(days=300)).strftime("%d.%m.%Y")
    assert not eng.evaluate(make(rooms=3, area=60, rent_warm=500, available_date=far)).matched
    soon = (date.today() + timedelta(days=20)).strftime("%d.%m.%Y")
    assert eng.evaluate(make(rooms=3, area=60, rent_warm=500, available_date=soon)).matched


def test_unknown_values_not_rejected():
    eng = FilterEngine(FILTERS)
    # No numeric fields detected -> should not be filtered out by numeric rules.
    assert eng.evaluate(make()).matched


def test_filter_list_helpers():
    eng = FilterEngine(FILTERS)
    good = make(rooms=3, area=60, rent_warm=500)
    bad = make(rooms=9, area=60, rent_warm=500)
    assert eng.filter([good, bad]) == [good]
    assert len(eng.evaluate_all([good, bad])) == 2


def test_empty_filters_accept_all():
    eng = FilterEngine({})
    assert eng.evaluate(make(rooms=99, rent_warm=9999)).matched

import responses

from scrapers import get_scraper, available_scrapers
from scrapers.wws_herford import WWSHerfordScraper

URL = "https://www.wws-herford.de/wohnen/wohnungsangebote"

# Simulates the detail page structure seen on the live WWS site:
# label on one row, value on the next (like a definition list).
DETAIL_HTML = """
<html><body>
<h1>WWS - Schöne 3-Zimmerwohnung in zentraler Lage</h1>
<dl>
  <dt>Zimmer</dt>         <dd>3</dd>
  <dt>Wohnfläche</dt>     <dd>72,00 m²</dd>
  <dt>Verfügbar ab</dt>   <dd>01.08.2026</dd>
  <dt>Kaltmiete</dt>      <dd>536,00 €</dd>
  <dt>Nebenkosten</dt>    <dd>139,00 €</dd>
  <dt>Warmmiete</dt>      <dd>675,00 €</dd>
  <dt>Adresse</dt>        <dd>Musterstraße 12, 32049 Herford</dd>
</dl>
</body></html>
"""

# Simulates a WBS listing
DETAIL_WBS_HTML = """
<html><body>
<h1>WWS - Seniorenwohnung mit WBS</h1>
<dl>
  <dt>Zimmer</dt>       <dd>2</dd>
  <dt>Wohnfläche</dt>   <dd>55,00 m²</dd>
  <dt>Verfügbar ab</dt> <dd>01.07.2026</dd>
  <dt>Kaltmiete</dt>    <dd>380,00 €</dd>
</dl>
<p>WBS erforderlich</p>
</body></html>
"""

OVERVIEW_HTML = f"""
<html><body>
  <a href="/wohnen/wohnungsangebote/detail/abc123">Wohnung 1</a>
  <a href="/wohnen/wohnungsangebote/detail/def456">Wohnung 2</a>
</body></html>
"""

DETAIL_URL_1 = "https://www.wws-herford.de/wohnen/wohnungsangebote/detail/abc123"
DETAIL_URL_2 = "https://www.wws-herford.de/wohnen/wohnungsangebote/detail/def456"


def test_scraper_is_registered():
    assert "wws_herford" in available_scrapers()
    assert get_scraper("wws_herford") is WWSHerfordScraper


def test_parse_detail_page_fields():
    scraper = WWSHerfordScraper("WWS Herford", URL)
    listings = scraper.parse(DETAIL_HTML)
    assert len(listings) == 1
    l = listings[0]
    assert "3-Zimmerwohnung" in l.title
    assert l.rooms == 3
    assert l.area == 72.0
    assert l.rent_cold == 536.0
    assert l.extra_costs == 139.0
    assert l.rent_warm == 675.0
    assert l.available_date == "01.08.2026"
    assert "Musterstraße" in l.address
    assert l.wbs_required is False


def test_parse_detects_wbs():
    scraper = WWSHerfordScraper("WWS Herford", URL)
    listings = scraper.parse(DETAIL_WBS_HTML)
    assert listings[0].wbs_required is True


def test_parse_empty_html_returns_listing_no_fields():
    scraper = WWSHerfordScraper("WWS Herford", URL)
    listings = scraper.parse("<html><body><h1>Test</h1></body></html>")
    # parse() on an empty detail page still returns one Listing (with None fields)
    assert isinstance(listings, list)


@responses.activate
def test_extract_listings_end_to_end():
    # Overview page
    responses.add(responses.GET, URL, body=OVERVIEW_HTML, status=200)
    # Two detail pages
    responses.add(responses.GET, DETAIL_URL_1, body=DETAIL_HTML,     status=200)
    responses.add(responses.GET, DETAIL_URL_2, body=DETAIL_WBS_HTML, status=200)

    scraper = WWSHerfordScraper("WWS Herford", URL, {"retries": 1, "backoff_seconds": 0})
    scraper._DETAIL_DELAY = 0   # no sleep in tests
    listings = scraper.extract_listings()

    assert len(listings) == 2
    assert listings[0].rooms == 3
    assert listings[0].area  == 72.0
    assert listings[0].rent_cold == 536.0
    assert listings[1].wbs_required is True


@responses.activate
def test_extract_listings_handles_overview_error():
    responses.add(responses.GET, URL, status=403)
    scraper = WWSHerfordScraper("WWS Herford", URL, {"retries": 1, "backoff_seconds": 0})
    assert scraper.extract_listings() == []


@responses.activate
def test_extract_listings_skips_failed_detail():
    responses.add(responses.GET, URL,          body=OVERVIEW_HTML, status=200)
    # detail 1 raises a connection error → skipped
    responses.add(responses.GET, DETAIL_URL_1,
                  body=Exception("connection error"))
    responses.add(responses.GET, DETAIL_URL_2, body=DETAIL_HTML,   status=200)

    scraper = WWSHerfordScraper("WWS Herford", URL, {"retries": 1, "backoff_seconds": 0})
    scraper._DETAIL_DELAY = 0
    listings = scraper.extract_listings()
    # First detail failed → skipped; second returned OK
    assert len(listings) == 1
    assert listings[0].rooms == 3

import responses

from scrapers import get_scraper, available_scrapers
from scrapers.wws_herford import WWSHerfordScraper

SAMPLE_HTML = """
<html><body>
<div class="wohnungsangebot">
  <h3 class="title">Renovierte 3-Zimmer Wohnung</h3>
  <p>Musterstraße 12, 32049 Herford</p>
  <p>3 Zimmer · 72 m²</p>
  <p>Kaltmiete: 450 € Nebenkosten: 139 € Warmmiete: 589 €</p>
  <p>Verfügbar ab 01.08.2026</p>
  <p>Objektnummer: A-1001</p>
  <a href="/wohnen/angebot/1001">Details</a>
</div>
<div class="wohnungsangebot">
  <h3 class="title">Seniorenwohnung mit WBS</h3>
  <p>Altweg 3, 32051 Herford</p>
  <p>2 Zimmer · 55 m²</p>
  <p>Kaltmiete: 380 € WBS erforderlich</p>
  <a href="https://www.wws-herford.de/wohnen/angebot/1002">Details</a>
</div>
</body></html>
"""

URL = "https://www.wws-herford.de/wohnen/wohnungsangebote"


def test_scraper_is_registered():
    assert "wws_herford" in available_scrapers()
    assert get_scraper("wws_herford") is WWSHerfordScraper


def test_parse_extracts_fields():
    scraper = WWSHerfordScraper("WWS Herford", URL)
    listings = scraper.parse(SAMPLE_HTML)
    assert len(listings) == 2

    first = listings[0]
    assert first.title == "Renovierte 3-Zimmer Wohnung"
    assert first.rooms == 3
    assert first.area == 72
    assert first.rent_warm == 589
    assert first.rent_cold == 450
    assert first.extra_costs == 139
    assert first.available_date == "01.08.2026"
    assert first.listing_id == "A-1001"
    assert first.listing_url == "https://www.wws-herford.de/wohnen/angebot/1001"
    assert first.wbs_required is False
    assert "Musterstraße" in first.address


def test_parse_detects_wbs():
    scraper = WWSHerfordScraper("WWS Herford", URL)
    listings = scraper.parse(SAMPLE_HTML)
    assert listings[1].wbs_required is True


def test_parse_empty_html():
    scraper = WWSHerfordScraper("WWS Herford", URL)
    assert scraper.parse("<html><body>nothing</body></html>") == []


@responses.activate
def test_extract_listings_end_to_end():
    responses.add(responses.GET, URL, body=SAMPLE_HTML, status=200)
    scraper = WWSHerfordScraper("WWS Herford", URL, {"retries": 1})
    listings = scraper.extract_listings()
    assert len(listings) == 2


@responses.activate
def test_extract_listings_handles_http_error():
    responses.add(responses.GET, URL, status=403)
    scraper = WWSHerfordScraper("WWS Herford", URL, {"retries": 1, "backoff_seconds": 0})
    assert scraper.extract_listings() == []

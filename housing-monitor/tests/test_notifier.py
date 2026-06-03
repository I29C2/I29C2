import responses

from models import Listing
from notifications import TelegramNotifier
from notifications.base import BaseNotifier

TOKEN = "123:abc"
CHAT = "999"
SEND_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"


def make_listing():
    return Listing(
        source="WWS Herford", listing_url="http://x/1",
        title="3-Zimmer", rooms=3, area=72, rent_warm=589,
        available_date="01.08.2026",
    )


def test_format_listing_contains_fields():
    msg = BaseNotifier.format_listing(make_listing())
    assert "3-Zimmer" in msg
    assert "72 m²" in msg
    assert "589 €" in msg
    assert "WWS Herford" in msg


def test_not_configured():
    n = TelegramNotifier("", "")
    assert n.configured is False
    assert n.send(make_listing()) is False


@responses.activate
def test_send_success():
    responses.add(responses.POST, SEND_URL, json={"ok": True}, status=200)
    n = TelegramNotifier(TOKEN, CHAT)
    assert n.configured
    assert n.send(make_listing()) is True


@responses.activate
def test_send_failure():
    responses.add(responses.POST, SEND_URL, status=500)
    n = TelegramNotifier(TOKEN, CHAT)
    assert n.send(make_listing()) is False


def test_format_handles_missing_fields():
    msg = BaseNotifier.format_listing(Listing(source="s", listing_url="u"))
    assert "—" in msg

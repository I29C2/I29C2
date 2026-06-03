import responses

from models import Listing
from notifications import TelegramNotifier
from notifications.base import BaseNotifier
from notifications.telegram_notifier import BotHandlers, CommandListener, CB_ALL, CB_EDIT

TOKEN = "123:abc"
CHAT  = "999"
SEND_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
ACK_URL  = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"


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
    assert "WWS Herford" in msg
    assert "Kaltmiete" in msg
    assert "Verfügbar" in msg


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


@responses.activate
def test_send_menu():
    responses.add(responses.POST, SEND_URL, json={"ok": True}, status=200)
    n = TelegramNotifier(TOKEN, CHAT)
    assert n.send_menu() is True
    body = responses.calls[0].request.body
    import json
    payload = json.loads(body)
    assert "reply_markup" in payload
    assert "inline_keyboard" in payload["reply_markup"]


def _make_listener(handlers=None):
    n = TelegramNotifier(TOKEN, CHAT)
    h = handlers or BotHandlers()
    return CommandListener(n, h)


def test_edit_criteria_happy_path():
    saved = {}
    h = BotHandlers()
    h.save_criteria = lambda r, a: saved.update({"rooms": r, "area": a})
    l = _make_listener(h)

    # Step 1: click Edit button
    l._handle_callback({
        "id": "cq1",
        "data": CB_EDIT,
        "message": {"chat": {"id": CHAT}},
    })
    from notifications.telegram_notifier import _STATE_ASK_ROOMS
    assert l._state.get(CHAT) == _STATE_ASK_ROOMS

    # Step 2: send rooms
    l._handle_message({"chat": {"id": CHAT}, "text": "3"})
    from notifications.telegram_notifier import _STATE_ASK_AREA
    assert l._state.get(CHAT) == _STATE_ASK_AREA
    assert l._edit_rooms.get(CHAT) == 3.0

    # Step 3: send area (no network calls needed — notifier.send_text patched below)
    sent = []
    l.notifier.send_text = lambda t, c=None, reply_markup=None: sent.append(t) or True
    l._handle_message({"chat": {"id": CHAT}, "text": "65"})

    assert saved == {"rooms": 3.0, "area": 65.0}
    assert l._state.get(CHAT) == "idle"
    assert any("actualizate" in m for m in sent)


def test_edit_criteria_invalid_input():
    l = _make_listener()
    l._start_edit(CHAT)
    sent = []
    l.notifier.send_text = lambda t, c=None, reply_markup=None: sent.append(t) or True
    l._handle_message({"chat": {"id": CHAT}, "text": "nu_e_numar"})
    assert any("valid" in m for m in sent)
    from notifications.telegram_notifier import _STATE_ASK_ROOMS
    assert l._state.get(CHAT) == _STATE_ASK_ROOMS

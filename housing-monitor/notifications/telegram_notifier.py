"""Telegram notifier with inline keyboard menu and edit-criteria conversation flow."""
from __future__ import annotations

import json
import logging
import threading
import time
from typing import Callable, Optional

import requests

from models import Listing
from .base import BaseNotifier

logger = logging.getLogger(__name__)

_API = "https://api.telegram.org/bot{token}/{method}"

# Callback data constants for inline buttons
CB_ALL      = "menu:all"
CB_MATCHES  = "menu:matches"
CB_EDIT     = "menu:edit"
CB_MENU     = "menu:main"

_MAIN_KEYBOARD = {
    "inline_keyboard": [
        [
            {"text": "📋 Toate ofertele",  "callback_data": CB_ALL},
            {"text": "🔔 Oferte potrivite", "callback_data": CB_MATCHES},
        ],
        [
            {"text": "✏️ Editare criterii", "callback_data": CB_EDIT},
        ],
    ]
}


class TelegramNotifier(BaseNotifier):
    def __init__(self, bot_token: str, chat_id: str, timeout: int = 30):
        self.bot_token = (bot_token or "").strip()
        self.chat_id   = (chat_id or "").strip()
        self.timeout   = timeout

    @property
    def configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def _call(self, method: str, payload: dict, timeout: Optional[int] = None) -> dict:
        url = _API.format(token=self.bot_token, method=method)
        resp = requests.post(url, json=payload, timeout=timeout or self.timeout)
        resp.raise_for_status()
        return resp.json()

    def send_text(self, text: str, chat_id: Optional[str] = None,
                  reply_markup: Optional[dict] = None) -> bool:
        if not self.configured:
            logger.warning("Telegram not configured; skipping notification")
            return False
        payload: dict = {
            "chat_id":    chat_id or self.chat_id,
            "text":       text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            self._call("sendMessage", payload)
            return True
        except requests.RequestException as exc:
            logger.error("Failed to send Telegram message: %s", exc)
            return False

    def answer_callback(self, callback_query_id: str, text: str = "") -> None:
        try:
            self._call("answerCallbackQuery",
                       {"callback_query_id": callback_query_id, "text": text})
        except requests.RequestException:
            pass

    def send(self, listing: Listing) -> bool:
        return self.send_text(self.format_listing(listing))

    def send_menu(self, chat_id: Optional[str] = None) -> bool:
        return self.send_text(
            "🏠 *Housing Monitor* — ce vrei să faci?",
            chat_id=chat_id,
            reply_markup=_MAIN_KEYBOARD,
        )

    def start_command_listener(self, handlers: "BotHandlers") -> "CommandListener":
        listener = CommandListener(self, handlers)
        listener.start()
        return listener


class BotHandlers:
    """Dependency-injection bag passed to CommandListener.

    Callers set each attribute to a callable returning str.
    """
    def __init__(self):
        self.all_listings:  Callable[[], str] = lambda: "—"
        self.matched:       Callable[[], str] = lambda: "—"
        self.stats:         Callable[[], str] = lambda: "—"
        self.status:        Callable[[], str] = lambda: "—"
        self.test:          Callable[[], str] = lambda: "🔔 Test OK"
        # Called with (min_rooms, min_area) when user finishes editing.
        self.save_criteria: Callable[[float, float], None] = lambda r, a: None


# States for the edit-criteria conversation
_STATE_IDLE     = "idle"
_STATE_ASK_ROOMS = "ask_rooms"
_STATE_ASK_AREA  = "ask_area"


class CommandListener:
    """Background thread polling getUpdates; handles commands and inline buttons."""

    def __init__(self, notifier: TelegramNotifier, handlers: BotHandlers):
        self.notifier = notifier
        self.h        = handlers
        self._offset  = 0
        self._stop    = threading.Event()
        self._thread  = threading.Thread(target=self._run, name="tg-cmd", daemon=True)
        # Per-chat conversation state for criteria editing
        self._state:      dict[str, str]   = {}
        self._edit_rooms: dict[str, float] = {}

    def start(self) -> None:
        if not self.notifier.configured:
            logger.info("Telegram not configured; command listener disabled")
            return
        self._thread.start()
        logger.info("Telegram command listener started")

    def stop(self) -> None:
        self._stop.set()

    # --- polling loop -------------------------------------------------------
    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                resp = self.notifier._call(
                    "getUpdates",
                    {"offset": self._offset, "timeout": 25},
                    timeout=30,
                )
                for update in resp.get("result", []):
                    self._offset = update["update_id"] + 1
                    try:
                        self._dispatch(update)
                    except Exception:
                        logger.exception("Error dispatching update %s", update.get("update_id"))
            except requests.RequestException as exc:
                logger.debug("getUpdates failed: %s", exc)
                time.sleep(5)

    def _dispatch(self, update: dict) -> None:
        if "callback_query" in update:
            self._handle_callback(update["callback_query"])
            return
        msg = update.get("message") or update.get("edited_message")
        if msg:
            self._handle_message(msg)

    # --- text messages / commands -------------------------------------------
    def _handle_message(self, msg: dict) -> None:
        text    = (msg.get("text") or "").strip()
        chat_id = str(msg["chat"]["id"])
        state   = self._state.get(chat_id, _STATE_IDLE)

        # --- edit-criteria conversation flow ---
        if state == _STATE_ASK_ROOMS:
            self._collect_rooms(chat_id, text)
            return
        if state == _STATE_ASK_AREA:
            self._collect_area(chat_id, text)
            return

        # --- commands ---
        if not text.startswith("/"):
            return
        command = text.lstrip("/").split("@")[0].split()[0].lower()
        dispatch = {
            "start":   lambda: self.notifier.send_menu(chat_id),
            "menu":    lambda: self.notifier.send_menu(chat_id),
            "status":  lambda: self.notifier.send_text(self.h.status(),  chat_id),
            "stats":   lambda: self.notifier.send_text(self.h.stats(),   chat_id),
            "test":    lambda: self.notifier.send_text(self.h.test(),    chat_id),
            "oferte":  lambda: self.notifier.send_text(self.h.all_listings(), chat_id),
            "potrivite": lambda: self.notifier.send_text(self.h.matched(), chat_id),
        }
        fn = dispatch.get(command)
        if fn:
            fn()

    # --- inline button callbacks -------------------------------------------
    def _handle_callback(self, cq: dict) -> None:
        data    = cq.get("data", "")
        chat_id = str(cq["message"]["chat"]["id"])
        cq_id   = cq["id"]

        self.notifier.answer_callback(cq_id)

        if data == CB_ALL:
            self.notifier.send_text(self.h.all_listings(), chat_id)
        elif data == CB_MATCHES:
            self.notifier.send_text(self.h.matched(), chat_id)
        elif data == CB_EDIT:
            self._start_edit(chat_id)
        elif data == CB_MENU:
            self.notifier.send_menu(chat_id)

    # --- criteria edit flow -------------------------------------------------
    def _start_edit(self, chat_id: str) -> None:
        self._state[chat_id] = _STATE_ASK_ROOMS
        self.notifier.send_text(
            "✏️ *Editare criterii*\n\nCâte camere *minim*? (trimite un număr, ex: `3`)",
            chat_id,
        )

    def _collect_rooms(self, chat_id: str, text: str) -> None:
        try:
            rooms = float(text.replace(",", "."))
            if rooms <= 0:
                raise ValueError
        except ValueError:
            self.notifier.send_text("❌ Introdu un număr valid, ex: `3`", chat_id)
            return
        self._edit_rooms[chat_id] = rooms
        self._state[chat_id] = _STATE_ASK_AREA
        self.notifier.send_text(
            f"✅ Camere minim: *{rooms}*\n\nSuprafață *minimă* (m²)? (ex: `65`)",
            chat_id,
        )

    def _collect_area(self, chat_id: str, text: str) -> None:
        try:
            area = float(text.replace(",", "."))
            if area <= 0:
                raise ValueError
        except ValueError:
            self.notifier.send_text("❌ Introdu un număr valid, ex: `65`", chat_id)
            return
        rooms = self._edit_rooms.pop(chat_id, 1)
        self._state[chat_id] = _STATE_IDLE
        try:
            self.h.save_criteria(rooms, area)
            self.notifier.send_text(
                f"✅ *Criterii actualizate!*\n\n"
                f"Camere minim: *{rooms}*\n"
                f"Suprafață minim: *{area} m²*\n\n"
                f"Filtrele intră în vigoare la următoarea scanare.",
                chat_id,
                reply_markup=_MAIN_KEYBOARD,
            )
        except Exception as exc:
            logger.exception("Failed to save criteria")
            self.notifier.send_text(f"⚠️ Eroare la salvare: {exc}", chat_id)

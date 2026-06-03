"""Telegram notifier + lightweight command poller (raw Bot API, no async)."""
from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

import requests

from models import Listing
from .base import BaseNotifier

logger = logging.getLogger(__name__)

_API = "https://api.telegram.org/bot{token}/{method}"


class TelegramNotifier(BaseNotifier):
    def __init__(self, bot_token: str, chat_id: str, timeout: int = 30):
        self.bot_token = (bot_token or "").strip()
        self.chat_id = (chat_id or "").strip()
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def _call(self, method: str, payload: dict, timeout: Optional[int] = None) -> dict:
        url = _API.format(token=self.bot_token, method=method)
        resp = requests.post(url, json=payload, timeout=timeout or self.timeout)
        resp.raise_for_status()
        return resp.json()

    def send_text(self, text: str, chat_id: Optional[str] = None) -> bool:
        if not self.configured:
            logger.warning("Telegram not configured; skipping notification")
            return False
        try:
            self._call(
                "sendMessage",
                {
                    "chat_id": chat_id or self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False,
                },
            )
            return True
        except requests.RequestException as exc:
            logger.error("Failed to send Telegram message: %s", exc)
            return False

    def send(self, listing: Listing) -> bool:
        return self.send_text(self.format_listing(listing))

    # --- command polling ---------------------------------------------------
    def start_command_listener(self, handlers: dict[str, Callable[[], str]]) -> "CommandListener":
        listener = CommandListener(self, handlers)
        listener.start()
        return listener


class CommandListener:
    """Background thread polling getUpdates for /status /stats /test /latest."""

    def __init__(self, notifier: TelegramNotifier, handlers: dict[str, Callable[[], str]]):
        self.notifier = notifier
        self.handlers = handlers
        self._offset = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="tg-cmd", daemon=True)

    def start(self) -> None:
        if not self.notifier.configured:
            logger.info("Telegram not configured; command listener disabled")
            return
        self._thread.start()
        logger.info("Telegram command listener started")

    def stop(self) -> None:
        self._stop.set()

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
                    self._handle(update)
            except requests.RequestException as exc:
                logger.debug("getUpdates failed: %s", exc)
                time.sleep(5)

    def _handle(self, update: dict) -> None:
        msg = update.get("message") or update.get("edited_message")
        if not msg:
            return
        text = (msg.get("text") or "").strip().lower()
        chat_id = str(msg["chat"]["id"])
        command = text.lstrip("/").split("@")[0].split()[0] if text else ""
        handler = self.handlers.get(command)
        if handler:
            try:
                reply = handler()
            except Exception as exc:  # never crash the listener
                logger.exception("Command handler '%s' failed", command)
                reply = f"⚠️ Error: {exc}"
            self.notifier.send_text(reply, chat_id=chat_id)

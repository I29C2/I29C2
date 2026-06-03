"""Housing Monitor Germany - application entry point."""
from __future__ import annotations

import logging
import signal
import sys
import threading
from datetime import datetime

from core.config import Config, ConfigError
from core.logging_config import setup_logging
from monitor import Monitor
from notifications import TelegramNotifier
from scheduler import MonitorScheduler
from storage import Database

logger = logging.getLogger("housing_monitor")


def build_command_handlers(monitor: Monitor, db: Database, started_at: datetime):
    """Telegram command handlers: /status /stats /test /latest."""

    def status() -> str:
        uptime = datetime.now() - started_at
        s = db.stats()
        return (
            "✅ *Housing Monitor running*\n"
            f"Uptime: {str(uptime).split('.')[0]}\n"
            f"Last scan: {s['last_scan'] or 'n/a'}\n"
            f"Sources: {len(monitor.config.sources)}\n"
            f"Interval: {monitor.config.interval_minutes} min"
        )

    def stats() -> str:
        s = db.stats()
        return (
            "📊 *Statistics*\n"
            f"Total listings: {s['total_listings']}\n"
            f"Notified: {s['notified_listings']}\n"
            f"Notifications sent: {s['notifications_sent']}\n"
            f"Last scan: {s['last_scan'] or 'n/a'}"
        )

    def test() -> str:
        return "🔔 Test notification — your bot is configured correctly."

    def latest() -> str:
        rows = db.latest(5)
        if not rows:
            return "No listings stored yet."
        lines = ["🆕 *Latest listings*"]
        for r in rows:
            lines.append(f"• {r['title']} — {r['rent_warm'] or r['rent_cold'] or '?'} € — {r['listing_url']}")
        return "\n".join(lines)

    return {"status": status, "stats": stats, "test": test, "latest": latest}


def main() -> int:
    try:
        config = Config.load("config.yaml")
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    log_cfg = config.logging
    setup_logging(
        level=log_cfg.get("level", "INFO"),
        file=log_cfg.get("file", "logs/app.log"),
        max_bytes=int(log_cfg.get("max_bytes", 5_242_880)),
        backup_count=int(log_cfg.get("backup_count", 5)),
    )

    logger.info("Starting Housing Monitor Germany")

    db = Database(config.database_path)
    tg = config.telegram
    notifier = TelegramNotifier(tg.get("bot_token", ""), tg.get("chat_id", ""))
    if not notifier.configured:
        logger.warning("Telegram is not configured — notifications will be skipped")

    monitor = Monitor(config, db, notifier)
    started_at = datetime.now()

    # Optional Telegram command listener
    listener = None
    if tg.get("enable_bot_commands", True) and notifier.configured:
        handlers = build_command_handlers(monitor, db, started_at)
        listener = notifier.start_command_listener(handlers)

    scheduler = MonitorScheduler(config.interval_minutes, monitor.run_once)

    stop_event = threading.Event()

    def _shutdown(signum, _frame):
        logger.info("Received signal %s, shutting down", signum)
        stop_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    scheduler.start(run_on_start=config.run_on_start)
    try:
        stop_event.wait()
    finally:
        scheduler.shutdown()
        if listener:
            listener.stop()
        db.close()
        logger.info("Shutdown complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

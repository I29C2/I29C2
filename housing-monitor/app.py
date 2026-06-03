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
from notifications.telegram_notifier import BotHandlers
from scheduler import MonitorScheduler
from storage import Database

logger = logging.getLogger("housing_monitor")

_PAGE = 10   # listings per Telegram message


def _fmt_listing_short(row) -> str:
    rooms_str = f"{row['rooms']} Zimmer" if row["rooms"] else "?"
    area_str  = f"{int(row['area'])} m²" if row["area"] else "?"
    kalt_str  = f"{int(row['rent_cold'])} € Kaltmiete" if row["rent_cold"] else "?"
    avail_str = row["available_date"] or "?"
    title     = row["title"] or "Wohnungsangebot"
    return (
        f"🏠 *{title}*\n"
        f"  🚪 {rooms_str}  |  📐 {area_str}  |  💶 {kalt_str}\n"
        f"  📅 Verfügbar: {avail_str}\n"
        f"  🔗 {row['listing_url']}"
    )


def build_bot_handlers(monitor: Monitor, db: Database,
                       config: Config, started_at: datetime) -> BotHandlers:
    h = BotHandlers()

    def all_listings() -> str:
        rows = db.latest(limit=_PAGE)
        if not rows:
            return "📭 Nicio ofertă stocată încă."
        lines = [f"📋 *Ultimele {len(rows)} oferte detectate:*\n"]
        lines += [_fmt_listing_short(r) for r in rows]
        return "\n".join(lines)

    def matched() -> str:
        rows = db.matched(limit=_PAGE)
        if not rows:
            return "🔕 Nicio ofertă potrivită criteriilor încă."
        lines = [f"🔔 *Ultimele {len(rows)} oferte potrivite:*\n"]
        lines += [_fmt_listing_short(r) for r in rows]
        return "\n".join(lines)

    def stats() -> str:
        s = db.stats()
        w = config.window
        return (
            "📊 *Statistici*\n"
            f"Total oferte detectate: {s['total_listings']}\n"
            f"Oferte potrivite: {s['notified_listings']}\n"
            f"Notificări trimise: {s['notifications_sent']}\n"
            f"Ultima scanare: {s['last_scan'] or 'n/a'}"
        )

    def status() -> str:
        uptime = datetime.now() - started_at
        s = db.stats()
        w = config.window
        in_win = "✅ Da" if config.within_window() else "⏸️ În afara ferestrei"
        return (
            "🟢 *Housing Monitor activ*\n"
            f"Uptime: {str(uptime).split('.')[0]}\n"
            f"Interval: {config.interval_minutes} min\n"
            f"Fereastră activă: {w.get('start_hour',8)}:00–{w.get('end_hour',20)}:00, L–V\n"
            f"Scanează acum: {in_win}\n"
            f"Ultima scanare: {s['last_scan'] or 'n/a'}\n"
            f"Surse: {len(monitor.config.sources)}"
        )

    def test() -> str:
        return "🔔 Test OK — botul funcționează corect."

    def scan() -> str:
        logger.info("Manual scan triggered via Telegram")
        summary = monitor.run_once()
        if summary["new"] == 0:
            return (
                "🔍 *Scanare finalizată*\n\n"
                "Nu au fost găsite oferte noi față de ultima scanare."
            )
        matched_str = (
            f"✅ {summary['matched']} ofert{'ă' if summary['matched'] == 1 else 'e'} "
            f"potrivit{'ă' if summary['matched'] == 1 else 'e'} — "
            f"{'notificare trimisă' if summary['notified'] > 0 else 'nicio notificare'}."
            if summary["matched"] > 0
            else "❌ Nicio ofertă nu corespunde criteriilor."
        )
        return (
            f"🔍 *Scanare finalizată*\n\n"
            f"Detectate: {summary['scraped']} oferte\n"
            f"Noi: {summary['new']}\n"
            f"{matched_str}"
        )

    def save_criteria(min_rooms: float, min_area: float) -> None:
        config.save_filters(min_rooms, min_area)
        # Update the running filter engine immediately.
        monitor.filter_engine.f["min_rooms"] = min_rooms
        monitor.filter_engine.f["min_area"]  = min_area
        logger.info("Criteria updated: min_rooms=%s, min_area=%s", min_rooms, min_area)

    h.all_listings  = all_listings
    h.matched       = matched
    h.stats         = stats
    h.status        = status
    h.test          = test
    h.scan          = scan
    h.save_criteria = save_criteria
    return h


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

    db       = Database(config.database_path)
    tg       = config.telegram
    notifier = TelegramNotifier(tg.get("bot_token", ""), tg.get("chat_id", ""))
    if not notifier.configured:
        logger.warning("Telegram is not configured — notifications will be skipped")

    monitor    = Monitor(config, db, notifier)
    started_at = datetime.now()
    listener   = None

    if tg.get("enable_bot_commands", True) and notifier.configured:
        handlers = build_bot_handlers(monitor, db, config, started_at)
        listener = notifier.start_command_listener(handlers)

    scheduler = MonitorScheduler(
        interval_minutes=config.interval_minutes,
        job=monitor.run_once,
        within_window=config.within_window,
    )

    stop_event = threading.Event()

    def _shutdown(signum, _frame):
        logger.info("Received signal %s, shutting down", signum)
        stop_event.set()

    signal.signal(signal.SIGINT,  _shutdown)
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

# telegram_bot/bot/main.py
from __future__ import annotations

import structlog
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from bot.config import config
from bot.handlers.start import start_command, back_main_callback
from bot.handlers.picks import (
    picks_today_callback,
    picks_page_callback,
    picks_filter_callback,
)
from bot.handlers.analysis import (
    analyze_callback,
    analyze_league_callback,
    analyze_match_callback,
    analyze_market_callback,
)
from bot.handlers.competitions import competitions_callback, comp_league_callback
from bot.handlers.settings import (
    settings_callback,
    settings_threshold_menu_callback,
    settings_threshold_callback,
    settings_notifications_callback,
    settings_leagues_callback,
)
from bot.handlers.premium import premium_callback, premium_plan_callback

logger = structlog.get_logger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(
        "Unhandled exception in update handler",
        error=str(context.error),
        update=str(update),
    )
    # Attempt to notify user if possible
    if isinstance(update, Update) and update.callback_query:
        try:
            await update.callback_query.answer(
                "⚠️ An error occurred. Please try again.", show_alert=True
            )
        except Exception:
            pass
    elif isinstance(update, Update) and update.message:
        try:
            await update.message.reply_text(
                "⚠️ An unexpected error occurred. Please try again."
            )
        except Exception:
            pass


async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle no-op callbacks (e.g. region headers in competitions)."""
    if update.callback_query:
        await update.callback_query.answer()


def build_application() -> Application:
    """Build and configure the Telegram bot application."""
    app = (
        ApplicationBuilder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .build()
    )

    # ── Commands ──────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start_command))

    # ── Main menu / navigation ────────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(back_main_callback, pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(noop_callback, pattern="^noop$"))

    # ── Today's Picks ─────────────────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(picks_today_callback, pattern="^picks_today$"))
    app.add_handler(CallbackQueryHandler(picks_page_callback, pattern=r"^picks_page_\d+$"))
    app.add_handler(CallbackQueryHandler(picks_filter_callback, pattern="^picks_filter"))

    # ── Match Analysis ────────────────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(analyze_callback, pattern="^analyze$"))
    app.add_handler(
        CallbackQueryHandler(analyze_league_callback, pattern=r"^analyze_league_.+$")
    )
    app.add_handler(
        CallbackQueryHandler(analyze_match_callback, pattern=r"^analyze_match_.+$")
    )
    app.add_handler(
        CallbackQueryHandler(
            analyze_market_callback, pattern=r"^market_(1x2|over_under|btts)$"
        )
    )

    # ── Competitions ──────────────────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(competitions_callback, pattern="^competitions$"))
    app.add_handler(
        CallbackQueryHandler(comp_league_callback, pattern=r"^comp_league_.+$")
    )

    # ── Settings ──────────────────────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings$"))
    app.add_handler(
        CallbackQueryHandler(
            settings_threshold_menu_callback, pattern="^settings_threshold_menu$"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            settings_threshold_callback, pattern=r"^settings_threshold_\d+$"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            settings_notifications_callback, pattern="^settings_notifications$"
        )
    )
    app.add_handler(
        CallbackQueryHandler(settings_leagues_callback, pattern="^settings_leagues$")
    )

    # ── Premium ───────────────────────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(premium_callback, pattern="^premium$"))
    app.add_handler(
        CallbackQueryHandler(
            premium_plan_callback,
            pattern=r"^premium_(monthly|quarterly|annual)$",
        )
    )

    # ── Error handler ─────────────────────────────────────────────────────────
    app.add_error_handler(error_handler)

    return app


def main() -> None:
    """Entry point — start the bot."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ]
    )

    logger.info("Starting BetBot AI Telegram bot...")
    app = build_application()
    logger.info("Bot started, polling for updates...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

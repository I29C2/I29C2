# telegram_bot/bot/handlers/start.py
import structlog
import httpx
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import config
from bot.keyboards.menus import main_menu_keyboard

logger = structlog.get_logger(__name__)

WELCOME_MESSAGE = (
    "👋 Welcome to *BetBot AI* — Your AI-Powered Sports Betting Analyst!\n\n"
    "🤖 *What I do:*\n"
    "• Analyze football matches with advanced AI models\n"
    "• Find value bets with edge calculations\n"
    "• Detect integrity risks in matches\n"
    "• Provide confidence-rated predictions\n\n"
    "⚠️ *Disclaimer:* This bot is for informational purposes only. "
    "Please gamble responsibly. 18\\+\n\n"
    "Use the menu below to get started:"
)


async def _register_user(telegram_id: int, username: str | None, first_name: str) -> None:
    """Register or update user via backend API."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{config.BACKEND_API_URL}/api/v1/users/telegram/register",
                json={
                    "telegram_id": telegram_id,
                    "username": username or "",
                    "first_name": first_name,
                },
            )
    except Exception as exc:
        logger.warning("Failed to register user via API", error=str(exc))


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user = update.effective_user
    if user is None:
        return

    logger.info("User started bot", user_id=user.id, username=user.username)

    # Register user asynchronously, errors are non-fatal
    await _register_user(user.id, user.username, user.first_name)

    await update.message.reply_text(  # type: ignore[union-attr]
        WELCOME_MESSAGE,
        parse_mode="MarkdownV2",
        reply_markup=main_menu_keyboard(),
    )


async def back_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'back_main' callback — return to main menu."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    user = update.effective_user
    first_name = user.first_name if user else "there"

    await query.edit_message_text(
        f"👋 Hey *{first_name}*\\! What would you like to do?\n\n"
        "Choose an option from the menu below:",
        parse_mode="MarkdownV2",
        reply_markup=main_menu_keyboard(),
    )

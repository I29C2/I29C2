# telegram_bot/bot/handlers/premium.py
from __future__ import annotations

import httpx
import structlog
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.config import config
from bot.keyboards.menus import back_keyboard

logger = structlog.get_logger(__name__)


def _esc(text: str) -> str:
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)


async def _fetch_subscription_status(telegram_id: int) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{config.BACKEND_API_URL}/api/v1/users/telegram/{telegram_id}/subscription"
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Failed to fetch subscription status", error=str(exc))
        return {"is_premium": False, "expires_at": None}


PREMIUM_FEATURES = [
    ("📊", "Unlimited daily value bets \\(free: 3/day\\)"),
    ("🔥", "High\\-confidence picks with edge \\> 10%"),
    ("🛡", "Full integrity risk reports"),
    ("📈", "ROI tracking and performance analytics"),
    ("⚡", "Real\\-time match alerts via Telegram"),
    ("🏆", "All competitions \\(free: top 5 only\\)"),
    ("🤖", "Deep AI analysis for every match"),
    ("🎯", "Bankroll management suggestions"),
]

PRICING = [
    ("Monthly", "£9\\.99/month", "premium_monthly"),
    ("3 Months", "£24\\.99 \\(save 17%\\)", "premium_quarterly"),
    ("Annual", "£79\\.99 \\(save 33%\\)", "premium_annual"),
]


def _premium_keyboard(is_premium: bool) -> InlineKeyboardMarkup:
    keyboard = []
    if not is_premium:
        for label, price, cb in PRICING:
            keyboard.append(
                [InlineKeyboardButton("{} — {}".format(label, price.replace("\\", "")), callback_data=cb)]
            )
    keyboard.append([InlineKeyboardButton("« Main Menu", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)


async def premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle 'premium' callback — show premium info and pricing."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    user = update.effective_user
    if user is None:
        return

    status = await _fetch_subscription_status(user.id)
    is_premium = status.get("is_premium", False)
    expires_at = status.get("expires_at")

    if is_premium:
        expiry_text = f"\n📅 Expires: `{_esc(str(expires_at))}`" if expires_at else ""
        header = (
            f"⭐ *You're a Premium Member\\!*{expiry_text}\n\n"
            f"You have full access to all BetBot AI features:\n\n"
        )
    else:
        header = (
            f"⭐ *BetBot AI Premium*\n\n"
            f"Unlock the full power of AI sports betting analysis:\n\n"
        )

    features_text = "\n".join(f"   {icon} {desc}" for icon, desc in PREMIUM_FEATURES)

    if is_premium:
        cta = "\n\n✅ Enjoy your premium membership\\!"
    else:
        cta = (
            "\n\n💳 *Choose a plan below to upgrade:*\n"
            "_\\(Payments processed securely via Stripe\\)_"
        )

    text = header + features_text + cta

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=_premium_keyboard(is_premium),
    )


async def premium_plan_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle premium plan selection (placeholder — redirect to web)."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    plan_map = {
        "premium_monthly": ("Monthly", "£9.99"),
        "premium_quarterly": ("3-Month", "£24.99"),
        "premium_annual": ("Annual", "£79.99"),
    }
    plan_key = query.data or ""
    plan_name, plan_price = plan_map.get(plan_key, ("Unknown", "N/A"))

    await query.edit_message_text(
        f"💳 *{_esc(plan_name)} Plan — {_esc(plan_price)}*\n\n"
        f"To complete your subscription, visit our website:\n\n"
        f"🌐 https://betbot\\.ai/premium\n\n"
        f"_Your Telegram account will be linked automatically\\._",
        parse_mode="MarkdownV2",
        reply_markup=back_keyboard("premium"),
    )

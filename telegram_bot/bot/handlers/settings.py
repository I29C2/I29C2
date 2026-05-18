# telegram_bot/bot/handlers/settings.py
from __future__ import annotations

from typing import Any, Dict

import httpx
import structlog
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import config
from bot.keyboards.menus import settings_keyboard, threshold_keyboard, back_keyboard

logger = structlog.get_logger(__name__)


def _esc(text: str) -> str:
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)


async def _fetch_user_settings(telegram_id: int) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{config.BACKEND_API_URL}/api/v1/users/telegram/{telegram_id}/settings"
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Failed to fetch user settings", error=str(exc))
        return {"alert_threshold": 5, "notifications_enabled": True, "favorite_leagues": []}


async def _update_user_settings(telegram_id: int, patch: Dict[str, Any]) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.patch(
                f"{config.BACKEND_API_URL}/api/v1/users/telegram/{telegram_id}/settings",
                json=patch,
            )
            resp.raise_for_status()
            return True
    except Exception as exc:
        logger.warning("Failed to update user settings", error=str(exc))
        return False


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show settings menu."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    user = update.effective_user
    if user is None:
        return

    current = await _fetch_user_settings(user.id)
    threshold = current.get("alert_threshold", 5)
    notifications = current.get("notifications_enabled", True)
    fav_leagues = current.get("favorite_leagues", [])
    notif_label = "✅ On" if notifications else "❌ Off"

    text = (
        f"⚙️ *Your Settings*\n\n"
        f"📈 Edge Alert Threshold: *{_esc(str(threshold))}%*\n"
        f"🔔 Notifications: *{_esc(notif_label)}*\n"
        f"⭐ Favourite Leagues: *{_esc(str(len(fav_leagues)))} selected*\n\n"
        f"Use the buttons below to change your preferences:"
    )

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=settings_keyboard(current),
    )


async def settings_threshold_menu_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Show threshold selection."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    await query.edit_message_text(
        "📈 *Select Edge Alert Threshold*\n\n"
        "You'll receive alerts for value bets with an edge at or above your chosen threshold:",
        parse_mode="MarkdownV2",
        reply_markup=threshold_keyboard(),
    )


async def settings_threshold_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle 'settings_threshold_{value}' — save new threshold."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    user = update.effective_user
    if user is None:
        return

    data = query.data or ""
    try:
        value = int(data.split("_")[-1])
    except (ValueError, IndexError):
        value = 5

    success = await _update_user_settings(user.id, {"alert_threshold": value})
    if success:
        msg = f"✅ Alert threshold updated to *{_esc(str(value))}%*\\!"
    else:
        msg = "❌ Failed to update settings\\. Please try again\\."

    current = await _fetch_user_settings(user.id)
    await query.edit_message_text(
        msg + "\n\n⚙️ *Your Settings:*\n" + f"📈 Edge Threshold: *{_esc(str(value))}%*",
        parse_mode="MarkdownV2",
        reply_markup=settings_keyboard(current),
    )


async def settings_notifications_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Toggle notifications on/off."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    user = update.effective_user
    if user is None:
        return

    current = await _fetch_user_settings(user.id)
    new_val = not current.get("notifications_enabled", True)
    success = await _update_user_settings(user.id, {"notifications_enabled": new_val})

    label = "enabled ✅" if new_val else "disabled ❌"
    if success:
        msg = f"🔔 Notifications *{_esc(label)}*\\!"
    else:
        msg = "❌ Failed to update notifications\\. Please try again\\."

    updated = await _fetch_user_settings(user.id)
    await query.edit_message_text(
        msg,
        parse_mode="MarkdownV2",
        reply_markup=settings_keyboard(updated),
    )


async def settings_leagues_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Show favourite leagues setting (placeholder)."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    await query.edit_message_text(
        "⭐ *Favourite Leagues*\n\n"
        "This feature lets you receive alerts only for your preferred leagues\\.\n\n"
        "_Coming soon\\!_",
        parse_mode="MarkdownV2",
        reply_markup=back_keyboard("settings"),
    )

# telegram_bot/bot/handlers/picks.py
from __future__ import annotations

import math
from typing import List, Dict, Any

import httpx
import structlog
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.config import config
from bot.keyboards.menus import back_keyboard, picks_filter_keyboard

logger = structlog.get_logger(__name__)

PICKS_PER_PAGE = 3

_CONFIDENCE_EMOJI = {
    "very_high": "🔥🔥🔥",
    "high": "🔥🔥",
    "medium": "🔥",
    "low": "❄️",
}

_INTEGRITY_BADGE = {
    "low": "🟢 Low Risk",
    "medium": "🟡 Medium Risk",
    "high": "🟠 High Risk",
    "critical": "🔴 Critical",
}


def _confidence_label(prob: float) -> str:
    if prob >= 0.75:
        return "very_high"
    if prob >= 0.60:
        return "high"
    if prob >= 0.45:
        return "medium"
    return "low"


def _format_pick(pick: Dict[str, Any], index: int) -> str:
    match = pick.get("match", {})
    home = match.get("home_team", {}).get("name", "Home")
    away = match.get("away_team", {}).get("name", "Away")
    match_time = match.get("match_date", "TBD")
    league = match.get("league", {}).get("name", "Unknown League")

    market = pick.get("market", "1x2").upper()
    prediction = pick.get("predicted_outcome", "N/A")
    ai_prob = pick.get("probability", 0.0)
    market_odds = pick.get("market_odds", 0.0)
    edge = pick.get("edge", 0.0)

    conf_key = _confidence_label(ai_prob)
    conf_emoji = _CONFIDENCE_EMOJI.get(conf_key, "❄️")

    integrity_risk = pick.get("integrity_risk", "low").lower()
    integrity_badge = _INTEGRITY_BADGE.get(integrity_risk, "🟢 Low Risk")

    edge_str = f"+{edge:.1f}%" if edge >= 0 else f"{edge:.1f}%"
    edge_emoji = "✅" if edge >= 0 else "❌"

    lines = [
        f"*{index}\\. {_esc(home)} vs {_esc(away)}*",
        f"⏰ {_esc(str(match_time))} \\| 🏆 {_esc(league)}",
        f"",
        f"📌 Market: `{_esc(market)}`",
        f"🎯 Prediction: *{_esc(str(prediction))}*",
        f"🤖 AI Probability: *{ai_prob * 100:.1f}%*",
        f"📈 Market Odds: `{market_odds:.2f}`",
        f"{edge_emoji} Edge: *{_esc(edge_str)}*",
        f"💪 Confidence: {conf_emoji}",
        f"🛡 Integrity: {_esc(integrity_badge)}",
        "─" * 20,
    ]
    return "\n".join(lines)


def _esc(text: str) -> str:
    """Escape MarkdownV2 special characters."""
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)


async def _fetch_value_bets(page: int = 1, per_page: int = PICKS_PER_PAGE) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{config.BACKEND_API_URL}/api/v1/predictions/value-bets",
                params={"page": page, "per_page": per_page},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Failed to fetch value bets", error=str(exc))
        return {"items": [], "total": 0, "page": page, "pages": 1}


def _build_pagination_keyboard(current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    row: List[InlineKeyboardButton] = []
    if current_page > 1:
        row.append(
            InlineKeyboardButton("⬅️ Prev", callback_data=f"picks_page_{current_page - 1}")
        )
    if current_page < total_pages:
        row.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"picks_page_{current_page + 1}")
        )

    keyboard = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔽 Filter", callback_data="picks_filter")])
    keyboard.append([InlineKeyboardButton("« Main Menu", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)


async def _send_picks_page(
    update: Update, context: ContextTypes.DEFAULT_TYPE, page: int
) -> None:
    query = update.callback_query

    data = await _fetch_value_bets(page=page)
    picks: List[Dict[str, Any]] = data.get("items", [])
    total: int = data.get("total", 0)
    total_pages: int = max(1, data.get("pages", math.ceil(total / PICKS_PER_PAGE)))

    if not picks:
        text = (
            "📭 *No value bets found for today\\.*\n\n"
            "Check back later — our AI is continuously scanning matches\\!"
        )
        if query:
            await query.edit_message_text(
                text,
                parse_mode="MarkdownV2",
                reply_markup=back_keyboard("back_main"),
            )
        return

    header = (
        f"📊 *Today's Value Bets* \\— Page {page}/{total_pages}\n"
        f"🎯 Total found: *{total}*\n\n"
    )
    body = "\n\n".join(
        _format_pick(pick, (page - 1) * PICKS_PER_PAGE + i + 1)
        for i, pick in enumerate(picks)
    )
    text = header + body

    keyboard = _build_pagination_keyboard(page, total_pages)
    if query:
        await query.edit_message_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=keyboard,
        )


async def picks_today_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle 'picks_today' callback."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    await _send_picks_page(update, context, page=1)


async def picks_page_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle 'picks_page_{n}' callback."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    data = query.data or ""
    try:
        page = int(data.split("_")[-1])
    except (ValueError, IndexError):
        page = 1

    await _send_picks_page(update, context, page=page)


async def picks_filter_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Show picks filter options."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    await query.edit_message_text(
        "🔽 *Filter Today's Picks*\n\nSelect a filter to narrow down the value bets:",
        parse_mode="MarkdownV2",
        reply_markup=picks_filter_keyboard(),
    )

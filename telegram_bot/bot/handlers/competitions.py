# telegram_bot/bot/handlers/competitions.py
from __future__ import annotations

from typing import Any, Dict, List

import httpx
import structlog
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.config import config
from bot.keyboards.menus import back_keyboard, comp_detail_keyboard

logger = structlog.get_logger(__name__)


def _esc(text: str) -> str:
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)


async def _fetch_leagues() -> List[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{config.BACKEND_API_URL}/api/v1/leagues")
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else data.get("items", [])
    except Exception as exc:
        logger.error("Failed to fetch leagues", error=str(exc))
        return []


async def _fetch_league_detail(league_id: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{config.BACKEND_API_URL}/api/v1/leagues/{league_id}"
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Failed to fetch league detail", error=str(exc))
        return {}


def _group_by_region(leagues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for league in leagues:
        region = league.get("country", "International")
        grouped.setdefault(region, []).append(league)
    return grouped


def _build_competitions_keyboard(
    grouped: Dict[str, List[Dict[str, Any]]]
) -> InlineKeyboardMarkup:
    keyboard: List[List[InlineKeyboardButton]] = []
    for region, leagues in grouped.items():
        # Region header row (non-clickable, but we use a dummy callback)
        keyboard.append(
            [InlineKeyboardButton(f"── {region} ──", callback_data="noop")]
        )
        row: List[InlineKeyboardButton] = []
        for i, league in enumerate(leagues):
            btn = InlineKeyboardButton(
                league.get("name", "League"),
                callback_data=f"comp_league_{league.get('id', i)}",
            )
            row.append(btn)
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

    keyboard.append([InlineKeyboardButton("« Main Menu", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)


async def competitions_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle 'competitions' callback — list all leagues by region."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    leagues = await _fetch_leagues()
    if not leagues:
        await query.edit_message_text(
            "😕 No competitions found at the moment\\. Try again later\\.",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard("back_main"),
        )
        return

    grouped = _group_by_region(leagues)
    total = len(leagues)

    await query.edit_message_text(
        f"🏆 *Competitions Browser*\n\n"
        f"Tracking *{_esc(str(total))}* competitions worldwide\\.\n"
        f"Select a league to view details:",
        parse_mode="MarkdownV2",
        reply_markup=_build_competitions_keyboard(grouped),
    )


async def comp_league_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle 'comp_league_{id}' callback — show league stats."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    data = query.data or ""
    league_id = data.replace("comp_league_", "")

    league = await _fetch_league_detail(league_id)
    if not league:
        await query.edit_message_text(
            "❌ League details not found\\.",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard("competitions"),
        )
        return

    name = league.get("name", "Unknown")
    country = league.get("country", "N/A")
    season = league.get("current_season", "N/A")
    total_matches = league.get("total_matches", 0)
    predictions_made = league.get("predictions_made", 0)
    accuracy = league.get("accuracy_rate", 0.0)
    roi = league.get("roi", 0.0)

    roi_sign = "\\+" if roi >= 0 else ""
    roi_str = f"{roi_sign}{roi:.1f}%"
    acc_str = f"{accuracy * 100:.1f}%"

    text = (
        f"🏆 *{_esc(name)}*\n"
        f"🌍 Country: {_esc(country)}\n"
        f"📅 Season: {_esc(str(season))}\n\n"
        f"📊 *Statistics*\n"
        f"   Total Matches: `{total_matches}`\n"
        f"   Predictions Made: `{predictions_made}`\n"
        f"   Accuracy Rate: *{_esc(acc_str)}*\n"
        f"   ROI: *{_esc(roi_str)}*\n"
    )

    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=comp_detail_keyboard(league_id),
    )

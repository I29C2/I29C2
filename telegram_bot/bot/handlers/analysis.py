# telegram_bot/bot/handlers/analysis.py
from __future__ import annotations

from typing import Dict, Any, Optional

import httpx
import structlog
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import config
from bot.keyboards.menus import (
    competition_keyboard,
    match_keyboard,
    market_keyboard,
    back_keyboard,
)

logger = structlog.get_logger(__name__)


def _esc(text: str) -> str:
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)


async def _get_leagues() -> list:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{config.BACKEND_API_URL}/api/v1/leagues/active")
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else data.get("items", [])
    except Exception as exc:
        logger.error("Failed to fetch leagues", error=str(exc))
        return []


async def _get_matches(league_id: str) -> list:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{config.BACKEND_API_URL}/api/v1/matches",
                params={"league_id": league_id, "status": "scheduled"},
            )
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else data.get("items", [])
    except Exception as exc:
        logger.error("Failed to fetch matches", error=str(exc), league_id=league_id)
        return []


async def _get_analysis(match_id: str, market: str) -> Optional[Dict[str, Any]]:
    market_map = {
        "market_1x2": "1x2",
        "market_over_under": "over_under_2_5",
        "market_btts": "btts",
    }
    market_key = market_map.get(market, market)
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                f"{config.BACKEND_API_URL}/api/v1/predictions/match/{match_id}",
                params={"market": market_key},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Failed to fetch analysis", error=str(exc), match_id=match_id)
        return None


def _format_analysis(analysis: Dict[str, Any]) -> str:
    match = analysis.get("match", {})
    home = match.get("home_team", {}).get("name", "Home")
    away = match.get("away_team", {}).get("name", "Away")
    league = match.get("league", {}).get("name", "League")
    match_date = match.get("match_date", "TBD")

    market = analysis.get("market", "1x2").upper()
    outcome = analysis.get("predicted_outcome", "N/A")
    prob = analysis.get("probability", 0.0)
    odds = analysis.get("market_odds", 0.0)
    fair_odds = 1 / prob if prob > 0 else 0
    edge = analysis.get("edge", 0.0)
    bankroll = analysis.get("bankroll_suggestion", 2.0)

    integrity = analysis.get("integrity_score", {})
    risk_level = integrity.get("risk_level", "low").lower()
    integrity_score = integrity.get("score", 0)

    _risk_icons = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
    risk_icon = _risk_icons.get(risk_level, "🟢")

    conf_key: str
    if prob >= 0.75:
        conf_key = "Very High 🔥🔥🔥"
    elif prob >= 0.60:
        conf_key = "High 🔥🔥"
    elif prob >= 0.45:
        conf_key = "Medium 🔥"
    else:
        conf_key = "Low ❄️"

    factors = integrity.get("contributing_factors", [])
    factors_text = ""
    if factors:
        factor_lines = "\n".join(f"   • {_esc(str(f))}" for f in factors[:3])
        factors_text = f"\n🔎 *Factors:*\n{factor_lines}"

    lines = [
        f"━━━━━━━━━━━━━━━━━━━━",
        f"🤖 *AI MATCH ANALYSIS*",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"",
        f"⚽ *{_esc(home)} vs {_esc(away)}*",
        f"🏆 {_esc(league)}",
        f"⏰ {_esc(str(match_date))}",
        f"",
        f"📌 *Market:* `{_esc(market)}`",
        f"🎯 *Prediction:* {_esc(str(outcome))}",
        f"",
        f"📊 *Probabilities*",
        f"   AI Probability: *{prob * 100:.1f}%*",
        f"   Market Odds: `{odds:.2f}`",
        f"   Fair Odds: `{fair_odds:.2f}`",
        "   Edge: *" + ("\\+" if edge >= 0 else "") + f"{edge:.1f}%*",
        f"",
        f"💪 *Confidence:* {_esc(conf_key)}",
        f"💰 *Suggested Stake:* {bankroll:.1f}% of bankroll",
        f"",
        f"🛡 *Integrity Assessment*",
        f"   {risk_icon} Risk Level: *{_esc(risk_level.capitalize())}*",
        f"   Score: `{integrity_score}/100`",
        factors_text,
        f"",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"⚠️ _For informational purposes only\\. Gamble responsibly\\._",
    ]
    return "\n".join(l for l in lines)


# ─── Callbacks ────────────────────────────────────────────────────────────────

async def analyze_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Step 1: Show competition list."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    leagues = await _get_leagues()
    if not leagues:
        await query.edit_message_text(
            "😕 No competitions available right now\\. Try again later\\.",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard("back_main"),
        )
        return

    await query.edit_message_text(
        "🔍 *Analyze a Match*\n\nSelect a competition:",
        parse_mode="MarkdownV2",
        reply_markup=competition_keyboard(leagues),
    )


async def analyze_league_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Step 2: Show matches for selected league."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    data = query.data or ""
    league_id = data.replace("analyze_league_", "")

    matches = await _get_matches(league_id)
    if not matches:
        await query.edit_message_text(
            "😕 No upcoming matches found for this competition\\.",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard("analyze"),
        )
        return

    await query.edit_message_text(
        "⚽ *Select a Match:*",
        parse_mode="MarkdownV2",
        reply_markup=match_keyboard(matches),
    )


async def analyze_match_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Step 3: Show market selection for a match."""
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    data = query.data or ""
    match_id = data.replace("analyze_match_", "")

    # Store match_id in context for next step
    if context.user_data is not None:
        context.user_data["pending_match_id"] = match_id

    await query.edit_message_text(
        "📊 *Select a Market to Analyse:*",
        parse_mode="MarkdownV2",
        reply_markup=market_keyboard(),
    )


async def analyze_market_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Step 4: Return full analysis for match + market."""
    query = update.callback_query
    if query is None:
        return
    await query.answer("⏳ Fetching AI analysis...")

    market = (query.data or "").replace("market_", "")
    match_id: str = ""
    if context.user_data is not None:
        match_id = str(context.user_data.get("pending_match_id", ""))

    if not match_id:
        await query.edit_message_text(
            "❌ Session expired\\. Please start the analysis flow again\\.",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard("analyze"),
        )
        return

    analysis = await _get_analysis(match_id, f"market_{market}")
    if not analysis:
        await query.edit_message_text(
            "❌ Could not retrieve analysis\\. Please try again later\\.",
            parse_mode="MarkdownV2",
            reply_markup=back_keyboard("analyze"),
        )
        return

    text = _format_analysis(analysis)
    await query.edit_message_text(
        text,
        parse_mode="MarkdownV2",
        reply_markup=back_keyboard("analyze"),
    )

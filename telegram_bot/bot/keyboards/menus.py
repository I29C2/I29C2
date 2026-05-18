# telegram_bot/bot/keyboards/menus.py
from typing import List, Dict, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build the main menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Today's Picks", callback_data="picks_today"),
            InlineKeyboardButton("🔍 Analyze Match", callback_data="analyze"),
        ],
        [
            InlineKeyboardButton("🏆 Competitions", callback_data="competitions"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
        ],
        [
            InlineKeyboardButton("⭐ Premium", callback_data="premium"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def competition_keyboard(leagues: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Build keyboard with competition buttons from a list of leagues."""
    keyboard = []
    row: List[InlineKeyboardButton] = []
    for i, league in enumerate(leagues):
        btn = InlineKeyboardButton(
            f"🏆 {league.get('name', 'League')}",
            callback_data=f"analyze_league_{league.get('id', i)}",
        )
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("« Back", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)


def match_keyboard(matches: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Build keyboard with match buttons."""
    keyboard = []
    for match in matches:
        home = match.get("home_team", {}).get("name", "Home")
        away = match.get("away_team", {}).get("name", "Away")
        match_id = match.get("id", "0")
        label = f"{home} vs {away}"
        keyboard.append(
            [InlineKeyboardButton(label, callback_data=f"analyze_match_{match_id}")]
        )
    keyboard.append([InlineKeyboardButton("« Back", callback_data="analyze")])
    return InlineKeyboardMarkup(keyboard)


def market_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for market selection."""
    keyboard = [
        [InlineKeyboardButton("1X2", callback_data="market_1x2")],
        [InlineKeyboardButton("Over/Under 2.5", callback_data="market_over_under")],
        [InlineKeyboardButton("Both Teams Score", callback_data="market_btts")],
        [InlineKeyboardButton("« Back", callback_data="analyze")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Build a simple back button keyboard."""
    keyboard = [[InlineKeyboardButton("« Back", callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)


def picks_filter_keyboard() -> InlineKeyboardMarkup:
    """Build the picks filter keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🔥 High Value", callback_data="picks_filter_high"),
            InlineKeyboardButton("✅ All Picks", callback_data="picks_filter_all"),
        ],
        [
            InlineKeyboardButton("⚽ Premier League", callback_data="picks_filter_pl"),
            InlineKeyboardButton("🇪🇸 La Liga", callback_data="picks_filter_laliga"),
        ],
        [InlineKeyboardButton("« Main Menu", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def comp_detail_keyboard(league_id: Any) -> InlineKeyboardMarkup:
    """Build keyboard for competition detail view."""
    keyboard = [
        [
            InlineKeyboardButton(
                "🔍 Analyze Match", callback_data=f"analyze_league_{league_id}"
            )
        ],
        [InlineKeyboardButton("« Back", callback_data="competitions")],
    ]
    return InlineKeyboardMarkup(keyboard)


def settings_keyboard(current: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Build settings keyboard based on current user settings."""
    threshold = current.get("alert_threshold", 5)
    keyboard = [
        [
            InlineKeyboardButton(
                f"📈 Edge Threshold: {threshold}%", callback_data="settings_threshold_menu"
            )
        ],
        [
            InlineKeyboardButton("🏆 Favorite Leagues", callback_data="settings_leagues"),
            InlineKeyboardButton("🔔 Notifications", callback_data="settings_notifications"),
        ],
        [InlineKeyboardButton("« Main Menu", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def threshold_keyboard() -> InlineKeyboardMarkup:
    """Build threshold selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("3%", callback_data="settings_threshold_3"),
            InlineKeyboardButton("5%", callback_data="settings_threshold_5"),
            InlineKeyboardButton("7%", callback_data="settings_threshold_7"),
            InlineKeyboardButton("10%", callback_data="settings_threshold_10"),
        ],
        [InlineKeyboardButton("« Back", callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)

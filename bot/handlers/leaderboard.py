"""
Leaderboard handler for Kingdom Conquest.
Shows rankings for players and alliances.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import Database
from utils.formatters import format_number
from utils.keyboards import leaderboard_keyboard, back_button_keyboard


db = Database()


async def handle_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /leaderboard command."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    if kingdom:
        db.update_leaderboard(user_id, kingdom.get('power', 0))
    all_kingdoms = db.get_all_kingdoms()
    all_kingdoms.sort(key=lambda k: k.get('power', 0), reverse=True)
    lines = ["🏆 <b>LEADERBOARD</b>", "━━━━━━━━━━━━━━", "", "👤 <b>TOP PLAYERS</b>"]
    user_rank = None
    for i, k in enumerate(all_kingdoms[:50], 1):
        rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"#{i}")
        lines.append(f"{rank_emoji} {k.get('kingdom_name', 'Unknown')} {k.get('flag', '')} — {format_number(k.get('power', 0))} Power")
        if k['user_id'] == user_id: user_rank = i
    lines.append(f"\n🎯 <b>Your Rank:</b> {'#' + str(user_rank) if user_rank else 'Not ranked yet'}")
    await update.message.reply_text(text="\n".join(lines), reply_markup=leaderboard_keyboard(), parse_mode='HTML')


async def menu_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leaderboard menu."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Update leaderboard data
    kingdom = db.get_kingdom(user_id)
    if kingdom:
        db.update_leaderboard(user_id, kingdom.get('power', 0))
    
    await show_player_leaderboard(update, context)


async def show_player_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top players leaderboard."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Get top kingdoms by power
    all_kingdoms = db.get_all_kingdoms()
    all_kingdoms.sort(key=lambda k: k.get('power', 0), reverse=True)
    
    lines = [
        "🏆 <b>LEADERBOARD</b>",
        "━━━━━━━━━━━━━━",
        "",
        "👤 <b>TOP PLAYERS</b>",
    ]
    
    user_rank = None
    for i, k in enumerate(all_kingdoms[:50], 1):
        rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"#{i}")
        lines.append(
            f"{rank_emoji} {k.get('kingdom_name', 'Unknown')} {k.get('flag', '')} "
            f"— {format_number(k.get('power', 0))} Power"
        )
        
        if k['user_id'] == user_id:
            user_rank = i
    
    if user_rank:
        lines.append(f"\n🎯 <b>Your Rank:</b> #{user_rank}")
    else:
        lines.append(f"\n🎯 <b>Your Rank:</b> Not ranked yet")
    
    lines.append(f"\n<i>Season resets in 14 days</i>")
    
    text = "\n".join(lines)
    
    await query.edit_message_text(
        text=text,
        reply_markup=leaderboard_keyboard(),
        parse_mode='HTML'
    )


async def show_alliance_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top alliances leaderboard."""
    query = update.callback_query
    
    # Get all alliances
    all_kingdoms = db.get_all_kingdoms()
    alliances_seen = set()
    alliances = []
    
    for k in all_kingdoms:
        alliance = db.get_alliance_by_member(k['user_id'])
        if alliance and alliance['id'] not in alliances_seen:
            alliances_seen.add(alliance['id'])
            alliances.append(alliance)
    
    alliances.sort(key=lambda a: a.get('power', 0), reverse=True)
    
    lines = [
        "🏆 <b>LEADERBOARD</b>",
        "━━━━━━━━━━━━━━",
        "",
        "🤝 <b>TOP ALLIANCES</b>",
    ]
    
    for i, a in enumerate(alliances[:20], 1):
        rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"#{i}")
        lines.append(
            f"{rank_emoji} {a.get('name', 'Unknown')} "
            f"— {format_number(a.get('power', 0))} Power "
            f"({a.get('member_count', 0)} members)"
        )
    
    if not alliances:
        lines.append("❌ Koi alliance abhi nahi hai!")
    
    text = "\n".join(lines)
    
    await query.edit_message_text(
        text=text,
        reply_markup=leaderboard_keyboard(),
        parse_mode='HTML'
    )


async def handle_leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leaderboard callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "menu_leaderboard":
        await menu_leaderboard(update, context)
    elif data == "lb_players":
        await show_player_leaderboard(update, context)
    elif data == "lb_alliances":
        await show_alliance_leaderboard(update, context)

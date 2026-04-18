"""
Settings handler for Kingdom Conquest.
Manages preferences, notifications, stats, and help.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import Database
from utils.formatters import format_number
from utils.keyboards import settings_keyboard, back_button_keyboard


db = Database()


async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command."""
    user_id = update.effective_user.id
    text = """⚙️ <b>SETTINGS</b>
━━━━━━━━━━━━━━
<b>Options:</b>
🔔 <b>Notifications</b> - Alerts on/off
🌐 <b>Language</b> - Hindi/English
📊 <b>Stats</b> - Your game statistics
❓ <b>Help</b> - How to play guide
<i>Apni preferences set karo!</i>"""
    await update.message.reply_text(text=text, reply_markup=settings_keyboard(), parse_mode='HTML')


async def menu_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu."""
    query = update.callback_query
    await query.answer()
    
    text = """
⚙️ <b>SETTINGS</b>
━━━━━━━━━━━━━━

<b>Options:</b>
🔔 <b>Notifications</b> - Alerts on/off
🌐 <b>Language</b> - Hindi/English
📊 <b>Stats</b> - Your game statistics
❓ <b>Help</b> - How to play guide

<i>Apni preferences set karo!</i>
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=settings_keyboard(),
        parse_mode='HTML'
    )


async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "menu_settings":
        await menu_settings(update, context)
    elif data == "settings_notifs":
        await toggle_notifications(update, context)
    elif data == "settings_lang":
        await show_language_options(update, context)
    elif data == "settings_stats":
        await show_stats(update, context)
    elif data == "settings_help":
        from .start import show_how_to_play
        await show_how_to_play(update, context, page=1)


async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle notifications setting."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        return
    
    current = kingdom.get('notifications_enabled', 1)
    new_val = 0 if current else 1
    
    db.update_kingdom(user_id, notifications_enabled=new_val)
    
    status = "ON ✅" if new_val else "OFF ❌"
    
    await query.edit_message_text(
        f"🔔 <b>Notifications</b>\n\n"
        f"Status: <b>{status}</b>\n\n"
        f"Aapko battle alerts, energy full, aur events ki notifications {status.split()[0]} kar di gayi hain.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 Toggle", callback_data="settings_notifs")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu_settings")],
        ]),
        parse_mode='HTML'
    )


async def show_language_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection."""
    query = update.callback_query
    
    text = """
🌐 <b>LANGUAGE</b>
━━━━━━━━━━━━━━

<b>Current:</b> Hindi + English

<i>Abhi sirf Hindi/English mixed supported hai.</i>
<i>More languages coming soon!</i>
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="menu_settings")],
        ]),
        parse_mode='HTML'
    )


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show player statistics."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        return
    
    army = db.get_army(user_id)
    buildings = db.get_buildings(user_id)
    heroes = db.get_heroes(user_id)
    achievements = db.get_achievements(user_id)
    
    total_army = army.get('infantry', 0) + army.get('archers', 0) + army.get('cavalry', 0) if army else 0
    total_building_levels = sum(b.get('level', 1) for b in buildings)
    
    text = f"""
📊 <b>YOUR STATISTICS</b>
━━━━━━━━━━━━━━

👑 <b>Kingdom:</b> {kingdom.get('kingdom_name', 'Unknown')} {kingdom.get('flag', '')}
🏆 <b>Level:</b> {kingdom.get('level', 1)}
⚡ <b>Power:</b> {format_number(kingdom.get('power', 0))}

⚔️ <b>Battles:</b>
   Won: {kingdom.get('battles_won', 0)}
   Lost: {kingdom.get('battles_lost', 0)}
   Total: {kingdom.get('battles_fought', 0)}

⚔️ <b>Army:</b> {total_army}
   🗡 {army.get('infantry', 0) if army else 0}
   🏹 {army.get('archers', 0) if army else 0}
   🐎 {army.get('cavalry', 0) if army else 0}

🏗 <b>Buildings:</b> {len(buildings)}
   Total Levels: {total_building_levels}

🧙 <b>Heroes:</b> {len([h for h in heroes if h.get('is_unlocked')])}/{len(heroes)}

🏆 <b>Achievements:</b> {len(achievements)}

💰 <b>Gold Earned:</b> {format_number(kingdom.get('gold', 0))}
🍖 <b>Food:</b> {format_number(kingdom.get('food', 0))}
💎 <b>Gems:</b> {kingdom.get('gems', 0)}
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="menu_settings")],
        ]),
        parse_mode='HTML'
    )

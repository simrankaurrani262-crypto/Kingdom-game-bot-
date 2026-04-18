"""
Dashboard handler for Kingdom Conquest.
Main HUD that displays kingdom status and navigation.
"""
from telegram import Update
from telegram.ext import ContextTypes

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import Database
from services.energy_service import EnergyService
from services.economy import EconomyService
from utils.keyboards import main_dashboard_keyboard
from utils.formatters import format_number, get_defense_rating, create_resource_bar
from config import MAX_ENERGY


db = Database()
energy_service = EnergyService()


async def render_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Render the main dashboard HUD."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    
    if not kingdom:
        # No kingdom yet, redirect to start
        from .start import handler_start
        await handler_start(update, context)
        return
    
    # Get fresh data
    army = db.get_army(user_id)
    buildings = db.get_buildings(user_id)
    heroes = db.get_heroes(user_id)
    
    # Calculate current energy
    energy = energy_service.calculate_current_energy(
        kingdom.get('energy', MAX_ENERGY),
        kingdom.get('last_energy_regen')
    )
    energy_display = energy_service.get_energy_display(
        kingdom.get('energy', MAX_ENERGY),
        kingdom.get('last_energy_regen')
    )
    
    # Calculate defense rating
    wall_level = 1
    for b in buildings:
        if b['building_type'] == 'wall':
            wall_level = b['level']
            break
    
    infantry = army.get('infantry', 0)
    archers = army.get('archers', 0)
    cavalry = army.get('cavalry', 0)
    total_army = infantry + archers + cavalry
    
    defense_value = (wall_level * 10) + (infantry * 1) + (archers * 1.5) + (cavalry * 2)
    defense_rating = get_defense_rating(defense_value)
    
    # Get shield status
    shield = kingdom.get('shield_expires')
    if shield:
        from datetime import datetime
        if isinstance(shield, str):
            shield = datetime.fromisoformat(shield.replace('Z', '+00:00'))
        if shield > datetime.now():
            from utils.formatters import format_time_remaining
            shield_text = format_time_remaining(shield)
        else:
            shield_text = "❌ None"
    else:
        shield_text = "❌ None"
    
    # Get XP progress
    level = kingdom.get('level', 1)
    xp = kingdom.get('xp', 0)
    xp_needed = EconomyService.calculate_xp_for_level(level)
    xp_bar = create_resource_bar(xp, xp_needed)
    
    # Power calculation
    power = EconomyService.calculate_kingdom_power(kingdom, army, buildings, heroes,
                                                    kingdom.get('battles_won', 0))
    db.update_kingdom(user_id, power=power)
    
    # Build dashboard text
    dashboard_text = f"""
👑 <b>Kingdom:</b> {kingdom.get('kingdom_name', 'Unknown')} {kingdom.get('flag', '')}
━━━━━━━━━━━━━━
🏆 <b>Level:</b> {level}  |  ⭐ <b>XP:</b> {xp_bar}
💰 <b>Gold:</b> {format_number(kingdom.get('gold', 0))}  |  🍖 <b>Food:</b> {format_number(kingdom.get('food', 0))}
⚡ <b>Energy:</b> {energy_display}

⚔️ <b>Army:</b> {total_army}
   🗡 {infantry}  🏹 {archers}  🐎 {cavalry}
🛡 <b>Defense:</b> {defense_rating}  |  <b>Wall Lv.{wall_level}</b>

📍 <b>Location:</b> ({kingdom.get('map_x', 0)},{kingdom.get('map_y', 0)})
🟢 <b>Status:</b> {kingdom.get('status', 'Online')}
🛡 <b>Shield:</b> {shield_text}
⚡ <b>Power:</b> {format_number(power)}
━━━━━━━━━━━━━━
"""
    
    # Edit existing message if callback, else send new
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=dashboard_text,
                reply_markup=main_dashboard_keyboard(),
                parse_mode='HTML'
            )
        except Exception:
            # If edit fails, send new message
            await context.bot.send_message(
                chat_id=user_id,
                text=dashboard_text,
                reply_markup=main_dashboard_keyboard(),
                parse_mode='HTML'
            )
    else:
        await update.message.reply_text(
            text=dashboard_text,
            reply_markup=main_dashboard_keyboard(),
            parse_mode='HTML'
        )


async def handle_dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dashboard navigation callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "back_dashboard":
        await render_dashboard(update, context)
    elif data == "noop":
        pass  # Do nothing for no-op buttons

"""
Army management handler for Kingdom Conquest.
Handles training, viewing, and managing army units.
"""
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import Database
from services.economy import EconomyService
from utils.formatters import format_number
from utils.keyboards import army_menu_keyboard, back_button_keyboard


db = Database()
economy = EconomyService()


async def handle_army(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /army command."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    army = db.get_army(user_id)
    buildings = db.get_buildings(user_id)
    if not kingdom or not army:
        await update.message.reply_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    barracks_level = 1
    for b in buildings:
        if b['building_type'] == 'barracks':
            barracks_level = b['level']
            break
    infantry = army.get('infantry', 0); archers = army.get('archers', 0); cavalry = army.get('cavalry', 0)
    total = infantry + archers + cavalry
    food_consumption = economy.calculate_army_food_consumption(infantry, archers, cavalry)
    text = f"""⚔️ <b>ARMY MANAGEMENT</b>
━━━━━━━━━━━━━━

⚔️ <b>Total Army:</b> {total}
🗡 <b>Infantry:</b> {infantry} | 💰50 🍖20
🏹 <b>Archers:</b> {archers} | 💰80 🍖30 (Barracks Lv.2)
🐎 <b>Cavalry:</b> {cavalry} | 💰150 🍖50 (Barracks Lv.4)

⚠️ <b>Food Consumption:</b> {format_number(food_consumption)}/hr"""
    await update.message.reply_text(text=text, reply_markup=army_menu_keyboard(army, barracks_level), parse_mode='HTML')


async def menu_army(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show army management menu (callback version)."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    army = db.get_army(user_id)
    buildings = db.get_buildings(user_id)
    
    if not kingdom or not army:
        await query.edit_message_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    
    # Get barracks level
    barracks_level = 1
    for b in buildings:
        if b['building_type'] == 'barracks':
            barracks_level = b['level']
            break
    
    infantry = army.get('infantry', 0)
    archers = army.get('archers', 0)
    cavalry = army.get('cavalry', 0)
    total = infantry + archers + cavalry
    
    # Calculate food consumption
    food_consumption = economy.calculate_army_food_consumption(infantry, archers, cavalry)
    
    text = f"""
⚔️ <b>ARMY MANAGEMENT</b>
━━━━━━━━━━━━━━

⚔️ <b>Total Army:</b> {total}

🗡 <b>Infantry:</b> {infantry}
   Attack: 10 | Defense: 8 | Speed: Slow
   💰50 🍖20 per batch

🏹 <b>Archers:</b> {archers}
   Attack: 12 | Defense: 5 | Speed: Medium
   💰80 🍖30 per batch
   {"✅ Unlocked" if barracks_level >= 2 else "🔒 Unlock: Barracks Lv.2"}

🐎 <b>Cavalry:</b> {cavalry}
   Attack: 18 | Defense: 12 | Speed: Fast
   💰150 🍖50 per batch
   {"✅ Unlocked" if barracks_level >= 4 else "🔒 Unlock: Barracks Lv.4"}

━━━━━━━━━━━━━━
⚠️ <b>Food Consumption:</b> {format_number(food_consumption)}/hr
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=army_menu_keyboard(army, barracks_level),
        parse_mode='HTML'
    )


async def handle_army_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle army menu callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "menu_army":
        await menu_army(update, context)
    elif data.startswith("army_train:"):
        unit_type = data.split(":")[1]
        await train_units(update, context, unit_type)


async def train_units(update: Update, context: ContextTypes.DEFAULT_TYPE, unit_type: str):
    """Train a batch of army units."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    army = db.get_army(user_id)
    buildings = db.get_buildings(user_id)
    
    if not kingdom or not army:
        await query.edit_message_text("❌ Error!", parse_mode='HTML')
        return
    
    # Get barracks level
    barracks_level = 1
    for b in buildings:
        if b['building_type'] == 'barracks':
            barracks_level = b['level']
            break
    
    # Check unlock requirements
    unlock_requirements = {
        'infantry': 1,
        'archers': 2,
        'cavalry': 4,
    }
    
    if barracks_level < unlock_requirements.get(unit_type, 99):
        await query.edit_message_text(
            f"🔒 <b>Not Unlocked!</b>\n\n"
            f"{unit_type.title()} require Barracks Lv.{unlock_requirements[unit_type]}",
            reply_markup=back_button_keyboard("menu_army"),
            parse_mode='HTML'
        )
        return
    
    # Calculate cost
    cost = economy.calculate_training_cost(unit_type)
    batch_size = 5
    
    # Check resources
    if kingdom['gold'] < cost['gold'] or kingdom['food'] < cost['food']:
        await query.edit_message_text(
            f"❌ <b>Not enough resources!</b>\n\n"
            f"Required: 💰{format_number(cost['gold'])} 🍖{format_number(cost['food'])}\n"
            f"You have: 💰{format_number(kingdom['gold'])} 🍖{format_number(kingdom['food'])}",
            reply_markup=back_button_keyboard("menu_army"),
            parse_mode='HTML'
        )
        return
    
    # Deduct resources and add units
    new_gold = kingdom['gold'] - cost['gold']
    new_food = kingdom['food'] - cost['food']
    
    unit_field = unit_type  # infantry, archers, cavalry
    current = army.get(unit_field, 0)
    new_count = current + batch_size
    
    db.update_kingdom(user_id, gold=new_gold, food=new_food)
    db.update_army(user_id, **{unit_field: new_count})
    
    unit_emoji = {'infantry': '🗡', 'archers': '🏹', 'cavalry': '🐎'}.get(unit_type, '⚔️')
    
    text = f"""
✅ <b>TRAINING COMPLETE!</b>
━━━━━━━━━━━━━━

{unit_emoji} <b>{unit_type.title()}:</b> +{batch_size}

New total: <b>{new_count}</b> {unit_emoji}

💰 Gold: -{format_number(cost['gold'])}
🍖 Food: -{format_number(cost['food'])}

<i>Aur train karne ke liye button dabao!</i>
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"⬆️ Train More {unit_type.title()}", callback_data=f"army_train:{unit_type}")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu_army")],
        ]),
        parse_mode='HTML'
    )

"""
Building system handler for Kingdom Conquest.
Manages all building-related interactions.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import Database
from services.economy import EconomyService
from utils.formatters import format_number, format_duration
from utils.keyboards import building_menu_keyboard, building_action_keyboard, back_button_keyboard


db = Database()
economy = EconomyService()


async def handle_build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /build command."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    buildings = db.get_buildings(user_id)
    
    if not kingdom:
        await update.message.reply_text("❌ Kingdom not found! /start se shuru karo.", parse_mode='HTML')
        return
    
    lines = ["🏗 <b>BUILDING MENU</b>", "━━━━━━━━━━━━━━"]
    for b in buildings:
        btype = b['building_type']
        emoji = {'town_hall': '🏰', 'gold_mine': '⛏', 'farm': '🌾', 'barracks': '🏹', 'wall': '🛡'}.get(btype, '🏗')
        name = btype.replace('_', ' ').title()
        level = b['level']
        status = "⬆️ Upgrading" if b.get('is_upgrading') else "✅ Ready"
        rate = economy.calculate_production_rate(btype, level)
        lines.append(f"{emoji} <b>{name}</b> Lv.{level} - {status}")
        if rate > 0:
            lines.append(f"   📊 Production: {format_number(rate)}/hr")
        if not b.get('is_upgrading') and level < 25:
            cost = economy.calculate_upgrade_cost(btype, level)
            lines.append(f"   ⬆️ Cost: 💰{format_number(cost['gold'])} 🍖{format_number(cost['food'])} ⏱️{format_duration(cost['time'])}")
        lines.append("")
    lines.append("━━━━━━━━━━━━━━")
    lines.append("<i>Use buttons to manage buildings!</i>")
    
    await update.message.reply_text(text="\n".join(lines), reply_markup=building_menu_keyboard(buildings), parse_mode='HTML')


async def menu_build(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show building management menu (callback version)."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    buildings = db.get_buildings(user_id)
    
    if not kingdom:
        await query.edit_message_text("❌ Kingdom not found! /start se shuru karo.", parse_mode='HTML')
        return
    
    # Build building list text
    lines = ["🏗 <b>BUILDING MENU</b>", "━━━━━━━━━━━━━━"]
    
    for b in buildings:
        btype = b['building_type']
        emoji = {'town_hall': '🏰', 'gold_mine': '⛏', 'farm': '🌾',
                 'barracks': '🏹', 'wall': '🛡'}.get(btype, '🏗')
        name = btype.replace('_', ' ').title()
        level = b['level']
        
        # Get production rate
        rate = economy.calculate_production_rate(btype, level)
        
        # Check if upgrading
        if b.get('is_upgrading'):
            status = f"⬆️ Upgrading..."
        else:
            status = f"✅ Active"
        
        lines.append(f"{emoji} <b>{name}</b> Lv.{level} - {status}")
        
        if rate > 0:
            lines.append(f"   📊 Production: {format_number(rate)}/hr")
        
        # Show upgrade cost
        if not b.get('is_upgrading') and level < 25:
            cost = economy.calculate_upgrade_cost(btype, level)
            lines.append(f"   ⬆️ Cost: 💰{format_number(cost['gold'])} 🍖{format_number(cost['food'])} ⏱️{format_duration(cost['time'])}")
        
        lines.append("")
    
    lines.append("━━━━━━━━━━━━━━")
    lines.append("<i>⬆️ = Upgrade | 📥 = Collect</i>")
    
    text = "\n".join(lines)
    
    await query.edit_message_text(
        text=text,
        reply_markup=building_menu_keyboard(buildings),
        parse_mode='HTML'
    )


async def handle_build_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle building menu callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "menu_build":
        await menu_build(update, context)
    elif data.startswith("build_upgrade:"):
        btype = data.split(":")[1]
        await upgrade_building(update, context, btype)
    elif data.startswith("build_collect:"):
        btype = data.split(":")[1]
        await collect_resources(update, context, btype)
    elif data.startswith("build_info:"):
        btype = data.split(":")[1]
        await building_info(update, context, btype)


async def upgrade_building(update: Update, context: ContextTypes.DEFAULT_TYPE, btype: str):
    """Start building upgrade."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    building = db.get_building(user_id, btype)
    
    if not kingdom or not building:
        await query.edit_message_text("❌ Error! Building not found.", parse_mode='HTML')
        return
    
    # Check if already upgrading
    if building.get('is_upgrading'):
        await query.edit_message_text(
            "❌ Building already upgrading!\nThoda wait karo.",
            reply_markup=back_button_keyboard("menu_build"),
            parse_mode='HTML'
        )
        return
    
    # Check max level
    if building['level'] >= 25:
        await query.edit_message_text(
            "❌ Max level reached! (Lv.25)",
            reply_markup=back_button_keyboard("menu_build"),
            parse_mode='HTML'
        )
        return
    
    # Calculate cost
    cost = economy.calculate_upgrade_cost(btype, building['level'])
    
    # Check resources
    if kingdom['gold'] < cost['gold'] or kingdom['food'] < cost['food']:
        await query.edit_message_text(
            f"❌ <b>Not enough resources!</b>\n\n"
            f"Required:\n"
            f"💰 Gold: {format_number(cost['gold'])} (You: {format_number(kingdom['gold'])})\n"
            f"🍖 Food: {format_number(cost['food'])} (You: {format_number(kingdom['food'])})",
            reply_markup=back_button_keyboard("menu_build"),
            parse_mode='HTML'
        )
        return
    
    # Deduct resources
    new_gold = kingdom['gold'] - cost['gold']
    new_food = kingdom['food'] - cost['food']
    
    # Calculate completion time
    minutes = cost['time']
    completes_at = datetime.now() + timedelta(minutes=minutes)
    
    db.update_kingdom(user_id, gold=new_gold, food=new_food)
    db.update_building(
        user_id, btype,
        is_upgrading=1,
        upgrade_started=datetime.now(),
        upgrade_completes=completes_at
    )
    
    building_name = btype.replace('_', ' ').title()
    
    text = f"""
⬆️ <b>UPGRADE STARTED!</b>
━━━━━━━━━━━━━━

{building_name} → Level {building['level'] + 1}

⏱️ <b>Time:</b> {format_duration(minutes)}
⏳ <b>Completes:</b> {completes_at.strftime('%H:%M:%S')}

💰 Gold: -{format_number(cost['gold'])}
🍖 Food: -{format_number(cost['food'])}

<i>Upgrade complete hone par notification mil jayegi!</i>
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=back_button_keyboard("menu_build"),
        parse_mode='HTML'
    )


async def collect_resources(update: Update, context: ContextTypes.DEFAULT_TYPE, btype: str):
    """Collect resources from a building."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    building = db.get_building(user_id, btype)
    
    if not kingdom or not building:
        await query.edit_message_text("❌ Error!", parse_mode='HTML')
        return
    
    # Calculate collectible resources
    last_collected = building.get('last_collected')
    if isinstance(last_collected, str):
        last_collected = datetime.fromisoformat(last_collected.replace('Z', '+00:00'))
    
    amount = economy.calculate_collectible_resources(
        btype, building['level'], last_collected
    )
    
    if amount <= 0:
        resource_name = "resources"
        if btype == 'gold_mine':
            resource_name = "gold"
        elif btype == 'farm':
            resource_name = "food"
        elif btype == 'barracks':
            resource_name = "army units"
        
        await query.edit_message_text(
            f"❌ <b>No {resource_name} ready yet!</b>\n\n"
            f"Thodi der baad try karo.\n"
            f"Resources har hour produce hote hain.",
            reply_markup=back_button_keyboard("menu_build"),
            parse_mode='HTML'
        )
        return
    
    # Add resources
    resource_emoji = "📦"
    if btype == 'gold_mine':
        new_gold = kingdom['gold'] + amount
        db.update_kingdom(user_id, gold=new_gold)
        resource_emoji = "💰"
    elif btype == 'farm':
        new_food = kingdom['food'] + amount
        db.update_kingdom(user_id, food=new_food)
        resource_emoji = "🍖"
    elif btype == 'barracks':
        # Add army units
        army = db.get_army(user_id)
        if army:
            new_infantry = army.get('infantry', 0) + amount
            db.update_army(user_id, infantry=new_infantry)
        resource_emoji = "🗡"
    
    # Update last collected
    db.update_building(user_id, btype, last_collected=datetime.now())
    
    building_name = btype.replace('_', ' ').title()
    
    text = f"""
📥 <b>COLLECTED!</b>
━━━━━━━━━━━━━━

{resource_emoji} <b>{building_name}</b>

Collected: <b>+{format_number(amount)}</b> {resource_emoji} ✅

<i>Next collection jaldi hi available hoga!</i>
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=back_button_keyboard("menu_build"),
        parse_mode='HTML'
    )


async def building_info(update: Update, context: ContextTypes.DEFAULT_TYPE, btype: str):
    """Show detailed building information."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    building = db.get_building(user_id, btype)
    if not building:
        await query.edit_message_text("❌ Building not found!", parse_mode='HTML')
        return
    
    level = building['level']
    rate = economy.calculate_production_rate(btype, level)
    next_rate = economy.calculate_production_rate(btype, level + 1) if level < 25 else 0
    cost = economy.calculate_upgrade_cost(btype, level)
    
    building_name = btype.replace('_', ' ').title()
    emoji = {'town_hall': '🏰', 'gold_mine': '⛏', 'farm': '🌾',
             'barracks': '🏹', 'wall': '🛡'}.get(btype, '🏗')
    
    description = {
        'town_hall': 'Kingdom ka mukhya bhavan. Sab buildings ki max level decide karta hai.',
        'gold_mine': 'Sona produce karta hai. Har level par production badhta hai.',
        'farm': 'Khana produce karta hai. Army ke liye zaroori.',
        'barracks': 'Army train karta hai. Naye unit types unlock hote hain.',
        'wall': 'Defense badhata hai. Attack se kam damage hota hai.',
    }.get(btype, 'Building')
    
    text = f"""
{emoji} <b>{building_name} Info</b>
━━━━━━━━━━━━━━

📊 <b>Current Level:</b> {level}
📈 <b>Production:</b> {format_number(rate)}/hr

📝 <b>Description:</b>
<i>{description}</i>

⬆️ <b>Next Level:</b>
Production: {format_number(next_rate)}/hr
Cost: 💰{format_number(cost['gold'])} 🍖{format_number(cost['food'])}
Time: {format_duration(cost['time'])}
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=building_action_keyboard(btype, building.get('is_upgrading', False)),
        parse_mode='HTML'
    )


async def check_and_complete_upgrades():
    """Background task: Check for completed upgrades."""
    buildings = db.get_buildings(0)  # Get all buildings - need to modify query
    # This would be called by a scheduler
    pass

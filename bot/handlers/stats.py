"""
Stats & Analytics Command Handler for Kingdom Conquest Bot.
Provides /stats command with visual charts and detailed analytics.

Commands:
- /stats - Full statistics dashboard
- /army_chart - Army composition visual
- /resource_chart - Resource trends
- /battle_stats - Battle analytics
- /power_profile - Power radar chart
- /activity - Activity heatmap
- /economy - Economy overview
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import Database
from services.visual_reporter import get_visual_reporter, VISUALIZATIONS_AVAILABLE
from services.analytics import get_analytics
from utils.formatters import format_number
from utils.keyboards import back_button_keyboard

db = Database()
reporter = get_visual_reporter()
analytics = get_analytics()


# ====================================================================
# MAIN STATS COMMAND
# ====================================================================

async def handler_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /stats command - Show full statistics with visual charts.
    """
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text(
            "Create your kingdom first! Use /start",
            parse_mode='HTML'
        )
        return

    # Show loading message
    loading_msg = await update.message.reply_text("Generating your stats dashboard...")

    try:
        # Get kingdom data
        army = db.get_army(user_id)
        buildings = db.get_buildings(user_id)
        heroes = db.get_heroes(user_id)

        # Calculate totals
        infantry = army.get('infantry', 0)
        archers = army.get('archers', 0)
        cavalry = army.get('cavalry', 0)
        total_army = infantry + archers + cavalry

        wall_level = 1
        building_levels = {}
        total_building_level = 0
        for b in buildings:
            building_levels[b['building_type']] = b['level']
            total_building_level += b['level']
            if b['building_type'] == 'wall':
                wall_level = b['level']

        gold = kingdom.get('gold', 0)
        food = kingdom.get('food', 0)
        energy = kingdom.get('energy', 10)

        # Calculate power
        power = (total_army * 10) + (wall_level * 100) + (total_building_level * 50)

        kingdom_name = kingdom.get('name', 'Unknown Kingdom')

        # Generate visual reports
        reports = reporter.generate_full_dashboard(
            user_id=user_id,
            kingdom_name=kingdom_name,
            infantry=infantry,
            archers=archers,
            cavalry=cavalry,
            army={'infantry': infantry, 'archers': archers, 'cavalry': cavalry},
            buildings=buildings,
            heroes=heroes,
            wall_level=wall_level,
            building_levels=building_levels,
            gold=gold,
            food=food,
            energy=energy,
            total_army=total_army,
            power=power
        )

        # Build navigation keyboard
        keyboard = [
            [InlineKeyboardButton("Army Chart", callback_data='stats_army'),
             InlineKeyboardButton("Resources", callback_data='stats_resources')],
            [InlineKeyboardButton("Battle Stats", callback_data='stats_battle'),
             InlineKeyboardButton("Power Profile", callback_data='stats_power')],
            [InlineKeyboardButton("Activity Map", callback_data='stats_activity'),
             InlineKeyboardButton("Economy", callback_data='stats_economy')],
            [InlineKeyboardButton("Dashboard", callback_data='stats_dashboard')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send status card if available
        if reports.get('status') and os.path.exists(reports['status']):
            with open(reports['status'], 'rb') as f:
                await update.message.reply_photo(
                    photo=f,
                    caption=f"Stats for <b>{kingdom_name}</b>",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        else:
            # Text-based fallback
            stats_text = f"""
<b>Stats - {kingdom_name}</b>
Power: {format_number(power)}
Army: {format_number(total_army)} (I:{infantry} A:{archers} C:{cavalry})
Gold: {format_number(gold)} | Food: {format_number(food)}
Buildings: {total_building_level} total levels
            """
            await update.message.reply_text(stats_text, parse_mode='HTML', reply_markup=reply_markup)

        # Delete loading message
        await loading_msg.delete()

    except Exception as e:
        await loading_msg.edit_text(f"Error generating stats: {str(e)[:200]}")


# ====================================================================
# CALLBACK HANDLER
# ====================================================================

async def handler_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle stats inline keyboard callbacks."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await query.edit_message_text("Kingdom not found! /start to begin.")
        return

    kingdom_name = kingdom.get('name', 'Unknown Kingdom')

    try:
        if data == 'stats_army':
            await _send_army_chart(query, user_id, kingdom_name)
        elif data == 'stats_resources':
            await _send_resource_chart(query, user_id, kingdom_name)
        elif data == 'stats_battle':
            await _send_battle_chart(query, user_id, kingdom_name)
        elif data == 'stats_power':
            await _send_power_chart(query, user_id, kingdom_name)
        elif data == 'stats_activity':
            await _send_activity_chart(query, user_id, kingdom_name)
        elif data == 'stats_economy':
            await _send_economy_chart(query, user_id, kingdom_name)
        elif data == 'stats_dashboard':
            await _send_dashboard(query, user_id, kingdom_name)
    except Exception as e:
        await query.edit_message_text(f"Error: {str(e)[:300]}")


async def _send_army_chart(query, user_id, kingdom_name):
    """Send army composition chart."""
    army = db.get_army(user_id)
    infantry = army.get('infantry', 0)
    archers = army.get('archers', 0)
    cavalry = army.get('cavalry', 0)

    filepath = reporter.generate_army_report(user_id, infantry, archers, cavalry, kingdom_name)
    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            await query.edit_message_media(
                media=telegram.InputMediaPhoto(media=f, caption=f"Army Composition - {kingdom_name}")
            )
    else:
        await query.edit_message_text(
            f"Army: {infantry} Infantry, {archers} Archers, {cavalry} Cavalry\n\n<i>Charts require matplotlib. Install with: pip install matplotlib seaborn numpy</i>",
            parse_mode='HTML'
        )


async def _send_resource_chart(query, user_id, kingdom_name):
    """Send resource trends chart."""
    filepath = reporter.generate_resource_report(user_id, kingdom_name)
    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            await query.edit_message_media(
                media=telegram.InputMediaPhoto(media=f, caption=f"Resource Trends - {kingdom_name}")
            )
    else:
        kingdom = db.get_kingdom(user_id)
        await query.edit_message_text(
            f"Gold: {format_number(kingdom.get('gold', 0))}\nFood: {format_number(kingdom.get('food', 0))}\n\n<i>Not enough history for trends. Play more to generate data!</i>",
            parse_mode='HTML'
        )


async def _send_battle_chart(query, user_id, kingdom_name):
    """Send battle analytics chart."""
    filepath = reporter.generate_battle_report_chart(user_id, kingdom_name)
    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            await query.edit_message_media(
                media=telegram.InputMediaPhoto(media=f, caption=f"Battle Analytics - {kingdom_name}")
            )
    else:
        await query.edit_message_text(
            "No battle data yet. Start attacking to generate analytics!",
            parse_mode='HTML'
        )


async def _send_power_chart(query, user_id, kingdom_name):
    """Send power radar chart."""
    army = db.get_army(user_id)
    buildings = db.get_buildings(user_id)
    heroes = db.get_heroes(user_id)

    wall_level = 1
    for b in buildings:
        if b['building_type'] == 'wall':
            wall_level = b['level']

    filepath = reporter.generate_power_profile(user_id, army, buildings, heroes, wall_level, kingdom_name)
    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            await query.edit_message_media(
                media=telegram.InputMediaPhoto(media=f, caption=f"Power Profile - {kingdom_name}")
            )
    else:
        await query.edit_message_text(
            "Power profile requires matplotlib. Install with: pip install matplotlib seaborn numpy",
            parse_mode='HTML'
        )


async def _send_activity_chart(query, user_id, kingdom_name):
    """Send activity heatmap."""
    filepath = reporter.generate_activity_report(user_id, kingdom_name)
    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            await query.edit_message_media(
                media=telegram.InputMediaPhoto(media=f, caption=f"Activity Heatmap - {kingdom_name}")
            )
    else:
        await query.edit_message_text(
            "Not enough activity data yet. Keep playing to generate your heatmap!",
            parse_mode='HTML'
        )


async def _send_economy_chart(query, user_id, kingdom_name):
    """Send economy chart."""
    filepath = reporter.generate_economy_report(user_id, kingdom_name)
    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            await query.edit_message_media(
                media=telegram.InputMediaPhoto(media=f, caption=f"Economy Overview - {kingdom_name}")
            )
    else:
        await query.edit_message_text(
            "Economy data requires more play history. Keep collecting resources!",
            parse_mode='HTML'
        )


async def _send_dashboard(query, user_id, kingdom_name):
    """Send full dashboard view."""
    stats_text = f"""
<b>Stats Dashboard - {kingdom_name}</b>

Select a category to view detailed charts:

Army Chart - Visual army composition
Resources - Gold & food trends
Battle Stats - Win/loss analytics
Power Profile - 5-dimension power radar
Activity Map - Weekly activity heatmap
Economy - Production vs consumption
    """
    keyboard = [
        [InlineKeyboardButton("Army Chart", callback_data='stats_army'),
         InlineKeyboardButton("Resources", callback_data='stats_resources')],
        [InlineKeyboardButton("Battle Stats", callback_data='stats_battle'),
         InlineKeyboardButton("Power Profile", callback_data='stats_power')],
        [InlineKeyboardButton("Activity Map", callback_data='stats_activity'),
         InlineKeyboardButton("Economy", callback_data='stats_economy')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(stats_text, parse_mode='HTML', reply_markup=reply_markup)


# ====================================================================
# DIRECT CHART COMMANDS
# ====================================================================

async def handler_army_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/army_chart - Show army composition chart."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("Create your kingdom first! Use /start")
        return

    army = db.get_army(user_id)
    infantry = army.get('infantry', 0)
    archers = army.get('archers', 0)
    cavalry = army.get('cavalry', 0)
    kingdom_name = kingdom.get('name', 'Unknown')

    filepath = reporter.generate_army_report(user_id, infantry, archers, cavalry, kingdom_name)
    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            await update.message.reply_photo(photo=f, caption=f"Army of {kingdom_name}")
    else:
        await update.message.reply_text(
            f"Army Composition:\nInfantry: {infantry}\nArchers: {archers}\nCavalry: {cavalry}\n\n"
            f"<i>Install matplotlib for visual charts: pip install matplotlib seaborn numpy</i>",
            parse_mode='HTML'
        )


async def handler_resource_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/resource_chart - Show resource trends."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("Create your kingdom first! Use /start")
        return

    kingdom_name = kingdom.get('name', 'Unknown')
    filepath = reporter.generate_resource_report(user_id, kingdom_name)
    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            await update.message.reply_photo(photo=f, caption=f"Resource Trends - {kingdom_name}")
    else:
        await update.message.reply_text(
            f"Current Resources:\nGold: {format_number(kingdom.get('gold', 0))}\n"
            f"Food: {format_number(kingdom.get('food', 0))}\n\n"
            f"<i>Play more to generate trend data!</i>",
            parse_mode='HTML'
        )


async def handler_battle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/battle_stats - Show battle analytics."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("Create your kingdom first! Use /start")
        return

    kingdom_name = kingdom.get('name', 'Unknown')
    stats = analytics.get_battle_stats(user_id)

    text = f"""
<b>Battle Stats - {kingdom_name}</b>

Record: {stats['wins']}W - {stats['losses']}L - {stats['draws']}D
Win Rate: {stats['win_rate']:.1f}%
Total Battles: {stats['total_battles']}

Damage Dealt: {format_number(stats['total_damage_dealt'])}
Damage Taken: {format_number(stats['total_damage_taken'])}
Gold Looted: {format_number(stats['total_gold_looted'])}
Food Looted: {format_number(stats['total_food_looted'])}
    """

    filepath = reporter.generate_battle_report_chart(user_id, kingdom_name)
    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            await update.message.reply_photo(photo=f, caption=text, parse_mode='HTML')
    else:
        await update.message.reply_text(text, parse_mode='HTML')


async def handler_power_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/power_profile - Show power radar chart."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("Create your kingdom first! Use /start")
        return

    army = db.get_army(user_id)
    buildings = db.get_buildings(user_id)
    heroes = db.get_heroes(user_id)

    wall_level = 1
    for b in buildings:
        if b['building_type'] == 'wall':
            wall_level = b['level']

    kingdom_name = kingdom.get('name', 'Unknown')
    filepath = reporter.generate_power_profile(user_id, army, buildings, heroes, wall_level, kingdom_name)

    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            await update.message.reply_photo(photo=f, caption=f"Power Profile - {kingdom_name}")
    else:
        await update.message.reply_text(
            "<i>Power profile requires matplotlib.\nInstall: pip install matplotlib seaborn numpy</i>",
            parse_mode='HTML'
        )


# Import telegram for InputMediaPhoto
import telegram

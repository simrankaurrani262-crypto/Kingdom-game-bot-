"""
Black market handler for Kingdom Conquest.
Premium shop with gems-based purchases and real visual.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import random
import os

from models.database import Database
from config import BLACK_MARKET_ITEMS, BLACK_MARKET_REFRESH_HOURS, MAX_ENERGY
from utils.formatters import format_number
from utils.keyboards import black_market_keyboard, back_button_keyboard
from utils.assets import get_scene_image

db = Database()
user_markets = {}


async def handle_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    items = get_user_market(user_id)
    _, expiry = user_markets.get(user_id, (items, datetime.now() + timedelta(hours=6)))
    time_left = expiry - datetime.now()
    hours, mins = int(time_left.total_seconds() // 3600), int((time_left.total_seconds() % 3600) // 60)
    lines = ["🏪 <b>BLACK MARKET</b>", "━━━━━━━━━━━━━━", "🌙 <i>Secret deals... shhh!</i>", ""]
    for i, item in enumerate(items):
        lines.append(f"{i+1}. {item['name']} — 💎{item['price_gems']} ({item['stock']} left)")
    lines += ["", f"⏳ Refresh in: {hours}h {mins}m", "", f"💎 <b>Your Gems:</b> {kingdom.get('gems', 0)}"]
    text = "\n".join(lines)
    market_img = get_scene_image('black_market')
    if market_img and os.path.isfile(market_img):
        await update.message.reply_photo(photo=open(market_img, 'rb'), caption=text, reply_markup=black_market_keyboard(items), parse_mode='HTML')
    else:
        await update.message.reply_text(text=text, reply_markup=black_market_keyboard(items), parse_mode='HTML')


async def menu_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        if query: await query.edit_message_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    items = get_user_market(user_id)
    _, expiry = user_markets.get(user_id, (items, datetime.now() + timedelta(hours=6)))
    time_left = expiry - datetime.now()
    hours, mins = int(time_left.total_seconds() // 3600), int((time_left.total_seconds() % 3600) // 60)
    lines = ["🏪 <b>BLACK MARKET</b>", "━━━━━━━━━━━━━━", "🌙 <i>Secret deals... shhh!</i>", ""]
    for i, item in enumerate(items):
        lines.append(f"{i+1}. {item['name']} — 💎{item['price_gems']} ({item['stock']} left)")
    lines += ["", f"⏳ Refresh in: {hours}h {mins}m", "", f"💎 <b>Your Gems:</b> {kingdom.get('gems', 0)}"]
    await query.edit_message_text(text="\n".join(lines), reply_markup=black_market_keyboard(items), parse_mode='HTML')


async def handle_market_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    data = query.data; user_id = update.effective_user.id
    if data == "menu_market": await menu_market(update, context)
    elif data.startswith("market_buy:"): await buy_market_item(update, context, int(data.split(":")[1]))
    elif data == "market_refresh": await refresh_market(update, context)


def get_user_market(user_id: int) -> list:
    now = datetime.now()
    if user_id in user_markets:
        items, expiry = user_markets[user_id]
        if now < expiry: return items
    items = random.sample(BLACK_MARKET_ITEMS, k=min(4, len(BLACK_MARKET_ITEMS)))
    expiry = now + timedelta(hours=BLACK_MARKET_REFRESH_HOURS)
    user_markets[user_id] = (items, expiry)
    return items


async def buy_market_item(update: Update, context: ContextTypes.DEFAULT_TYPE, item_idx: int):
    query = update.callback_query; user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom: return
    items = get_user_market(user_id)
    if item_idx >= len(items):
        await query.edit_message_text("❌ Item not found!", reply_markup=back_button_keyboard("menu_market"), parse_mode='HTML')
        return
    item = items[item_idx]
    if kingdom.get('gems', 0) < item['price_gems']:
        await query.edit_message_text(f"❌ <b>Not enough Gems!</b>\n\nRequired: 💎{item['price_gems']}\nYou have: 💎{kingdom.get('gems', 0)}", reply_markup=back_button_keyboard("menu_market"), parse_mode='HTML')
        return
    new_gems = kingdom.get('gems', 0) - item['price_gems']
    effect = item['effect']; effect_message = ""
    if effect == 'skip_build_time':
        effect_message = "⏱️ All active upgrades instantly complete!"
    elif effect == 'refill_energy':
        db.update_kingdom(user_id, energy=MAX_ENERGY); effect_message = f"⚡ Energy refilled to {MAX_ENERGY}!"
    elif effect == 'extend_shield':
        shield_expires = datetime.now() + timedelta(hours=24)
        db.update_kingdom(user_id, gems=new_gems, shield_expires=shield_expires)
        effect_message = "🛡 24-hour shield activated!"
    elif effect == 'full_spy_report':
        effect_message = "📜 Next spy mission = Full intel guaranteed!"
    elif effect == 'add_gold':
        new_gold = kingdom.get('gold', 0) + 10000
        db.update_kingdom(user_id, gems=new_gems, gold=new_gold)
        effect_message = "💰 +10,000 Gold added!"
    elif effect == 'extra_dice_roll':
        effect_message = "🎲 Extra dice roll earned!"
    
    if effect not in ['extend_shield', 'add_gold']:
        db.update_kingdom(user_id, gems=new_gems)
    
    await query.edit_message_text(
        f"✅ <b>Purchased!</b>\n\n{item['name']}\n💎 -{item['price_gems']} Gems\n\n{effect_message}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏪 Market", callback_data="menu_market")],
            [InlineKeyboardButton("🏠 Dashboard", callback_data="back_dashboard")],
        ]),
        parse_mode='HTML'
    )


async def refresh_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; user_id = update.effective_user.id
    if user_id in user_markets: del user_markets[user_id]
    await menu_market(update, context)

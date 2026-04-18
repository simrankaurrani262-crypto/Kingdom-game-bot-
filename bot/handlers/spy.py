"""
Spy system handler for Kingdom Conquest.
Manages spy missions, reports, and intel gathering with real visuals.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import random
import os

from models.database import Database
from config import SPY_COST_GOLD, SPY_SUCCESS_BASE_CHANCE, SPY_TRAP_CHANCE, SPY_COOLDOWN_MINUTES
from utils.formatters import format_number
from utils.keyboards import spy_menu_keyboard, back_button_keyboard
from utils.assets import get_scene_image

db = Database()


async def handle_spy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    cooldown_remaining = db.get_cooldown_remaining(user_id, 'spy')
    cooldown_text = f"\n⏳ <b>Cooldown:</b> {cooldown_remaining // 60} minutes" if cooldown_remaining > 0 else ""
    text = f"""🕵️ <b>SPY MENU</b>
━━━━━━━━━━━━━━
🕵️ <b>Send Spy Mission</b>
💰 Cost: {format_number(SPY_COST_GOLD)} Gold
⏱️ Cooldown: {SPY_COOLDOWN_MINUTES} minutes
📊 Success Rate: {int(SPY_SUCCESS_BASE_CHANCE*100)}%{cooldown_text}

<i>Spy reveals enemy army size, wall level, and resources!</i>"""
    spy_img = get_scene_image('spy')
    if spy_img and os.path.isfile(spy_img):
        await update.message.reply_photo(photo=open(spy_img, 'rb'), caption=text, reply_markup=spy_menu_keyboard(), parse_mode='HTML')
    else:
        await update.message.reply_text(text=text, reply_markup=spy_menu_keyboard(), parse_mode='HTML')


async def menu_spy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await query.edit_message_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    cooldown_remaining = db.get_cooldown_remaining(user_id, 'spy')
    cooldown_text = f"\n⏳ <b>Cooldown:</b> {cooldown_remaining // 60} minutes" if cooldown_remaining > 0 else ""
    text = f"""🕵️ <b>SPY MENU</b>
━━━━━━━━━━━━━━
🕵️ <b>Send Spy Mission</b>
💰 Cost: {format_number(SPY_COST_GOLD)} Gold
⏱️ Cooldown: {SPY_COOLDOWN_MINUTES} minutes
📊 Success Rate: {int(SPY_SUCCESS_BASE_CHANCE*100)}%{cooldown_text}

<i>Spy reveals enemy army size, wall level, and resources!</i>"""
    await query.edit_message_text(text=text, reply_markup=spy_menu_keyboard(), parse_mode='HTML')


async def handle_spy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    data = query.data; user_id = update.effective_user.id
    if data == "menu_spy": await menu_spy(update, context)
    elif data == "spy_send": await start_spy_mission(update, context)
    elif data == "spy_reports": await show_past_reports(update, context)
    elif data.startswith("spy_target:"):
        target_id = int(data.split(":")[1])
        await execute_spy(update, context, target_id)


async def start_spy_mission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom: return
    cooldown_remaining = db.get_cooldown_remaining(user_id, 'spy')
    if cooldown_remaining > 0:
        await query.edit_message_text(f"⏳ <b>Spy Cooldown!</b>\n\n{cooldown_remaining // 60} minutes remaining.", reply_markup=back_button_keyboard("menu_spy"), parse_mode='HTML')
        return
    if kingdom.get('gold', 0) < SPY_COST_GOLD:
        await query.edit_message_text(f"❌ <b>Not enough Gold!</b>\n\nRequired: 💰{format_number(SPY_COST_GOLD)}\nYou have: 💰{format_number(kingdom.get('gold', 0))}", reply_markup=back_button_keyboard("menu_spy"), parse_mode='HTML')
        return
    all_kingdoms = db.get_all_kingdoms()
    targets = [k for k in all_kingdoms if k['user_id'] != user_id][:5]
    if not targets:
        await query.edit_message_text("❌ No targets available!", reply_markup=back_button_keyboard("menu_spy"), parse_mode='HTML')
        return
    lines = ["🕵️ <b>SELECT TARGET</b>", "━━━━━━━━━━━━━━"]; keyboard = []
    for t in targets:
        lines.append(f"👑 {t.get('kingdom_name', 'Unknown')} {t.get('flag', '')}\n   Level: {t.get('level', 1)} | Power: {format_number(t.get('power', 0))}")
        keyboard.append([InlineKeyboardButton(f"🕵️ Spy on {t.get('kingdom_name', 'Unknown')[:12]}", callback_data=f"spy_target:{t['user_id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_spy")])
    await query.edit_message_text(text="\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')


async def execute_spy(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    query = update.callback_query; user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id); target = db.get_kingdom(target_id); target_army = db.get_army(target_id)
    if not kingdom or not target:
        await query.edit_message_text("❌ Target not found!", parse_mode='HTML'); return
    new_gold = max(0, kingdom.get('gold', 0) - SPY_COST_GOLD)
    db.update_kingdom(user_id, gold=new_gold)
    expires = datetime.now() + timedelta(minutes=SPY_COOLDOWN_MINUTES)
    db.set_cooldown(user_id, 'spy', expires)
    if random.random() < SPY_TRAP_CHANCE:
        await query.edit_message_text(
            f"💀 <b>SPY CAUGHT!</b>\n\nYour spy was caught by {target.get('kingdom_name', 'Target')}'s guards!\n💰 {format_number(SPY_COST_GOLD)} Gold wasted.",
            reply_markup=back_button_keyboard("menu_spy"), parse_mode='HTML'
        ); return
    if random.random() > SPY_SUCCESS_BASE_CHANCE:
        await query.edit_message_text(
            "🕵️ <b>Spy Mission Failed!</b>\n\nNo intel gathered.\nTry again later.",
            reply_markup=back_button_keyboard("menu_spy"), parse_mode='HTML'
        ); return
    intel_level = random.choice(['basic', 'detailed', 'full'])
    report_lines = [f"🕵️ <b>SPY REPORT</b>", f"━━━━━━━━━━━━━━", f"", f"👑 <b>Target:</b> {target.get('kingdom_name', 'Unknown')} {target.get('flag', '')}"]
    if intel_level in ['basic', 'detailed', 'full']:
        total_army = target_army.get('infantry', 0) + target_army.get('archers', 0) + target_army.get('cavalry', 0) if target_army else 0
        report_lines.append(f"⚔️ <b>Army:</b> ~{total_army}")
        buildings = db.get_buildings(target_id)
        wall_level = 1
        for b in buildings:
            if b['building_type'] == 'wall': wall_level = b['level']; break
        report_lines.append(f"🛡 <b>Wall Level:</b> {wall_level}")
    if intel_level in ['detailed', 'full']:
        report_lines.append(f"💰 <b>Gold:</b> ~{format_number(target.get('gold', 0))}")
        report_lines.append(f"🍖 <b>Food:</b> ~{format_number(target.get('food', 0))}")
        report_lines.append(f"⚡ <b>Energy:</b> {target.get('energy', 0)}/10")
    if intel_level == 'full' and target_army:
        report_lines.append(f"🗡 <b>Infantry:</b> {target_army.get('infantry', 0)}")
        report_lines.append(f"🏹 <b>Archers:</b> {target_army.get('archers', 0)}")
        report_lines.append(f"🐎 <b>Cavalry:</b> {target_army.get('cavalry', 0)}")
    report_lines += [f"", f"━━━━━━━━━━━━━━", f"📊 <b>Intel Quality:</b> {intel_level.upper()}"]
    report_text = "\n".join(report_lines)
    db.save_spy_report(user_id, target_id, report_text, intel_level)
    await query.edit_message_text(
        text=report_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🕵️ Spy Menu", callback_data="menu_spy")],
            [InlineKeyboardButton("🏠 Dashboard", callback_data="back_dashboard")],
        ]),
        parse_mode='HTML'
    )


async def show_past_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; user_id = update.effective_user.id
    cursor = db.conn.cursor()
    cursor.execute('SELECT * FROM spy_reports WHERE spy_id = ? ORDER BY created_at DESC LIMIT 5', (user_id,))
    reports = [dict(r) for r in cursor.fetchall()]
    if not reports:
        await query.edit_message_text("📜 <b>No spy reports yet!</b>\n\nSend a spy mission first.", reply_markup=back_button_keyboard("menu_spy"), parse_mode='HTML')
        return
    lines = ["📜 <b>PAST REPORTS</b>", "━━━━━━━━━━━━━━"]
    for r in reports:
        target = db.get_kingdom(r['target_id'])
        target_name = target.get('kingdom_name', 'Unknown') if target else 'Unknown'
        lines.append(f"🕵️ {target_name} - {r.get('intel_level', 'unknown').upper()}")
    await query.edit_message_text(text="\n".join(lines), reply_markup=back_button_keyboard("menu_spy"), parse_mode='HTML')

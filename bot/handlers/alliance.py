"""
Alliance system handler for Kingdom Conquest.
Manages alliance creation, joining, wars, donations with real banner.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os

from models.database import Database
from services.economy import EconomyService
from utils.formatters import format_number
from utils.keyboards import alliance_hub_keyboard, back_button_keyboard
from utils.assets import get_scene_image
from config import ALLIANCE_CREATION_COST

db = Database()
economy = EconomyService()


async def handle_alliance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    alliance = db.get_alliance_by_member(user_id)
    if not alliance:
        text = f"""🤝 <b>ALLIANCE HUB</b>
━━━━━━━━━━━━━━
You are not in any alliance.
🏰 <b>Create Alliance</b> - 💰{format_number(ALLIANCE_CREATION_COST)} Gold
🔍 <b>Join Alliance</b> - Browse existing alliances
📋 <b>Invites</b> - Check pending invites"""
        alliance_img = get_scene_image('alliance')
        if alliance_img and os.path.isfile(alliance_img):
            await update.message.reply_photo(photo=open(alliance_img, 'rb'), caption=text, reply_markup=alliance_hub_keyboard(in_alliance=False), parse_mode='HTML')
        else:
            await update.message.reply_text(text=text, reply_markup=alliance_hub_keyboard(in_alliance=False), parse_mode='HTML')
    else:
        text = _get_alliance_info_text(alliance)
        alliance_img = get_scene_image('alliance')
        if alliance_img and os.path.isfile(alliance_img):
            await update.message.reply_photo(photo=open(alliance_img, 'rb'), caption=text, reply_markup=alliance_hub_keyboard(in_alliance=True), parse_mode='HTML')
        else:
            await update.message.reply_text(text=text, reply_markup=alliance_hub_keyboard(in_alliance=True), parse_mode='HTML')


def _get_alliance_info_text(alliance: dict) -> str:
    members = db.get_alliance_members(alliance['id'])
    leader = db.get_kingdom(alliance['leader_id'])
    member_lines = [f"{'👑' if m['role']=='leader' else '👤'} {m['kingdom_name']} {m['flag']}" for m in members[:10]]
    return f"""🤝 <b>{alliance.get('name', 'Alliance')}</b>
━━━━━━━━━━━━━━
👑 <b>Leader:</b> {leader.get('kingdom_name', 'Unknown') if leader else 'Unknown'}
👥 <b>Members:</b> {len(members)}/{alliance.get('max_members', 20)}
🏆 <b>Power:</b> {format_number(alliance.get('power', 0))}
💰 <b>Treasury:</b> {format_number(alliance.get('treasury_gold', 0))} Gold

<b>Members:</b>
{chr(10).join(member_lines)}"""


async def menu_alliance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await query.edit_message_text("❌ Kingdom not found!", parse_mode='HTML'); return
    
    alliance = db.get_alliance_by_member(user_id)
    if not alliance:
        text = f"""🤝 <b>ALLIANCE HUB</b>
━━━━━━━━━━━━━━
You are not in any alliance.
🏰 <b>Create Alliance</b> - 💰{format_number(ALLIANCE_CREATION_COST)} Gold
🔍 <b>Join Alliance</b> - Browse existing
📋 <b>Invites</b> - Check pending
<i>Alliances get team wars and shared rewards!</i>"""
        await query.edit_message_text(text=text, reply_markup=alliance_hub_keyboard(in_alliance=False), parse_mode='HTML')
    else:
        await show_alliance_info(update, context, alliance)


async def show_alliance_info(update: Update, context: ContextTypes.DEFAULT_TYPE, alliance: dict):
    query = update.callback_query
    members = db.get_alliance_members(alliance['id'])
    leader = db.get_kingdom(alliance['leader_id'])
    member_lines = []
    for m in members[:10]:
        role_emoji = '👑' if m['role'] == 'leader' else '👤'
        member_lines.append(f"{role_emoji} {m['kingdom_name']} {m['flag']} (Power: {format_number(m.get('power', 0))})")
    
    text = f"""
🤝 <b>{alliance.get('name', 'Alliance')}</b>
━━━━━━━━━━━━━━

👑 <b>Leader:</b> {leader.get('kingdom_name', 'Unknown') if leader else 'Unknown'}
👥 <b>Members:</b> {len(members)}/{alliance.get('max_members', 20)}
🏆 <b>Alliance Power:</b> {format_number(alliance.get('power', 0))}
💰 <b>Treasury:</b> {format_number(alliance.get('treasury_gold', 0))} Gold

<b>Members:</b>
{chr(10).join(member_lines)}

<i>Alliance wars with team rewards!</i>
"""
    user_id = update.effective_user.id
    is_leader = any(m for m in members if m['user_id'] == user_id and m['role'] == 'leader')
    keyboard = [
        [InlineKeyboardButton("👥 Members", callback_data="alliance_members"), InlineKeyboardButton("⚔️ Team War", callback_data="alliance_war")],
        [InlineKeyboardButton("💰 Donate", callback_data="alliance_donate"), InlineKeyboardButton("💬 Chat", callback_data="alliance_chat")],
    ]
    if is_leader:
        keyboard.append([InlineKeyboardButton("⚙️ Manage", callback_data="alliance_manage")])
    keyboard.append([InlineKeyboardButton("🚪 Leave", callback_data="alliance_leave")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")])
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')


async def handle_alliance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    data = query.data; user_id = update.effective_user.id
    if data == "menu_alliance":
        await menu_alliance(update, context)
    elif data == "alliance_create":
        await start_alliance_creation(update, context)
    elif data == "alliance_join":
        await show_alliance_list(update, context)
    elif data == "alliance_leave":
        await leave_alliance(update, context)
    elif data == "alliance_members":
        await show_alliance_members(update, context)
    elif data == "alliance_donate":
        await donate_to_alliance(update, context)
    elif data == "alliance_war":
        await show_alliance_war(update, context)
    elif data.startswith("join_alliance:"):
        alliance_id = int(data.split(":")[1])
        await join_alliance(update, context, alliance_id)


async def start_alliance_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom: return
    if kingdom['gold'] < ALLIANCE_CREATION_COST:
        await query.edit_message_text(
            f"❌ <b>Not enough Gold!</b>\n\nRequired: 💰{format_number(ALLIANCE_CREATION_COST)}\nYou have: 💰{format_number(kingdom['gold'])}",
            reply_markup=back_button_keyboard("menu_alliance"), parse_mode='HTML'
        ); return
    context.user_data['creating_alliance'] = True
    await query.edit_message_text(
        "🏰 <b>CREATE ALLIANCE</b>\n━━━━━━━━━━━━━━\n\nName your alliance:\n<i>3-20 characters</i>", parse_mode='HTML'
    )


async def process_alliance_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('creating_alliance'): return
    user_id = update.effective_user.id
    name = update.message.text.strip()
    if len(name) < 3 or len(name) > 20:
        await update.message.reply_text("❌ Invalid name! 3-20 characters needed.", parse_mode='HTML'); return
    kingdom = db.get_kingdom(user_id)
    if not kingdom or kingdom['gold'] < ALLIANCE_CREATION_COST:
        await update.message.reply_text("❌ Error creating alliance!", parse_mode='HTML'); return
    new_gold = kingdom['gold'] - ALLIANCE_CREATION_COST
    db.update_kingdom(user_id, gold=new_gold)
    alliance_id = db.create_alliance(name, user_id)
    if alliance_id:
        context.user_data.pop('creating_alliance', None)
        db.unlock_achievement(user_id, 'diplomat')
        await update.message.reply_text(
            f"🎉 <b>Alliance Created!</b>\n\n🏰 {name}\n👑 Leader: {kingdom.get('kingdom_name', 'You')}\n\nInvite other players now!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🤝 Alliance Hub", callback_data="menu_alliance")]]),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text("❌ Could not create alliance! Name must be unique.", parse_mode='HTML')


async def show_alliance_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    all_kingdoms = db.get_all_kingdoms()
    alliances_seen = set(); alliances = []
    for k in all_kingdoms:
        alliance = db.get_alliance_by_member(k['user_id'])
        if alliance and alliance['id'] not in alliances_seen:
            alliances_seen.add(alliance['id']); alliances.append(alliance)
    if not alliances:
        await query.edit_message_text(
            "❌ No alliances available!\n\nCreate your own!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏰 Create Alliance", callback_data="alliance_create")], [InlineKeyboardButton("🔙 Back", callback_data="menu_alliance")]]),
            parse_mode='HTML'
        ); return
    lines = ["🔍 <b>JOIN ALLIANCE</b>", "━━━━━━━━━━━━━━"]; keyboard = []
    for a in alliances[:10]:
        lines.append(f"🏰 {a.get('name', 'Unknown')}\n   👥 {a.get('member_count', 0)}/{a.get('max_members', 20)} members")
        keyboard.append([InlineKeyboardButton(f"Join {a.get('name', 'Unknown')[:15]}", callback_data=f"join_alliance:{a['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_alliance")])
    await query.edit_message_text(text="\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')


async def join_alliance(update: Update, context: ContextTypes.DEFAULT_TYPE, alliance_id: int):
    query = update.callback_query; user_id = update.effective_user.id
    alliance = db.get_alliance(alliance_id)
    if not alliance:
        await query.edit_message_text("❌ Alliance not found!", parse_mode='HTML'); return
    if alliance['member_count'] >= alliance['max_members']:
        await query.edit_message_text("❌ Alliance is full!", reply_markup=back_button_keyboard("menu_alliance"), parse_mode='HTML'); return
    success = db.join_alliance(alliance_id, user_id)
    if success:
        await query.edit_message_text(
            f"🎉 <b>Joined Alliance!</b>\n\n🏰 {alliance.get('name', 'Unknown')}\nWelcome to the team!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🤝 Alliance Hub", callback_data="menu_alliance")]]),
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text("❌ Could not join!", reply_markup=back_button_keyboard("menu_alliance"), parse_mode='HTML')


async def leave_alliance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; user_id = update.effective_user.id
    alliance = db.get_alliance_by_member(user_id)
    if not alliance:
        await query.edit_message_text("❌ You are not in an alliance!"); return
    db.leave_alliance(alliance['id'], user_id)
    await query.edit_message_text(
        f"🚪 <b>Left Alliance!</b>\n\nYou left {alliance.get('name', 'Unknown')}.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🤝 Alliance Hub", callback_data="menu_alliance")]]),
        parse_mode='HTML'
    )


async def show_alliance_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; user_id = update.effective_user.id
    alliance = db.get_alliance_by_member(user_id)
    if not alliance: return
    members = db.get_alliance_members(alliance['id'])
    lines = [f"👥 <b>{alliance.get('name', 'Alliance')} MEMBERS</b>", "━━━━━━━━━━━━━━"]
    for m in members:
        role_emoji = '👑' if m['role'] == 'leader' else ('⭐' if m['role'] == 'officer' else '👤')
        lines.append(f"{role_emoji} {m['kingdom_name']} {m['flag']} - Power: {format_number(m.get('power', 0))}")
    lines.append(f"\nTotal: {len(members)} members")
    await query.edit_message_text(text="\n".join(lines), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu_alliance")]]), parse_mode='HTML')


async def donate_to_alliance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id); alliance = db.get_alliance_by_member(user_id)
    if not kingdom or not alliance: return
    donation = min(1000, kingdom['gold'])
    if donation <= 0:
        await query.edit_message_text("❌ No Gold to donate!", reply_markup=back_button_keyboard("menu_alliance"), parse_mode='HTML'); return
    new_gold = kingdom['gold'] - donation
    db.update_kingdom(user_id, gold=new_gold)
    await query.edit_message_text(
        f"💰 <b>Donated!</b>\n\n💰 +{format_number(donation)} Gold to treasury!\nThank you!",
        reply_markup=back_button_keyboard("menu_alliance"), parse_mode='HTML'
    )


async def show_alliance_war(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text(
        "⚔️ <b>ALLIANCE WARS</b>\n━━━━━━━━━━━━━━\n\n<i>Coming Soon!</i>\n\nAlliance wars:\n- Two alliances compete\n- Combined member power\n- Shared rewards for winners\n- Weekly events\n\n<b>Stay tuned!</b>",
        reply_markup=back_button_keyboard("menu_alliance"), parse_mode='HTML'
    )

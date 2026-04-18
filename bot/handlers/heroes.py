"""
Hero system handler for Kingdom Conquest.
Manages hero roster with real portrait images, skills, level-ups, and skill tree.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os

from models.database import Database
from config import HEROES_DATA, SKILL_TREE
from utils.formatters import format_number
from utils.keyboards import heroes_menu_keyboard, hero_manage_keyboard, skill_tree_keyboard, back_button_keyboard
from utils.assets import get_hero_image

db = Database()


async def handle_heroes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /hero command."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    heroes = db.get_heroes(user_id)
    if not kingdom:
        await update.message.reply_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    ensure_heroes_exist(user_id, heroes); heroes = db.get_heroes(user_id)
    text = _render_heroes_text(user_id, heroes, kingdom)
    await update.message.reply_text(text=text, reply_markup=heroes_menu_keyboard(heroes), parse_mode='HTML')


def _render_heroes_text(user_id: int, heroes: list, kingdom: dict) -> str:
    lines = ["🧙 <b>HERO ROSTER</b>", "━━━━━━━━━━━━━━"]
    for hero in heroes:
        hkey, hero_data = hero['hero_key'], HEROES_DATA.get(hero['hero_key'], {})
        level, unlocked = hero.get('level', 1), hero.get('is_unlocked', 0)
        active_status = " ✅ ACTIVE" if hero.get('is_active') else ""
        lines.append(f"{hero_data.get('emoji', '⚔️')} <b>{hero_data.get('name', hkey)}</b>{active_status}\n   {'🔓' if unlocked else '🔒'} Level: {level} | 🎯 {hero_data.get('skill', '')}")
        if not unlocked:
            cost_text = f"💎 {hero_data.get('cost_gems', 0)} Gems" if hero_data.get('premium') else f"💰 {format_number(hero_data.get('cost_gold', 0))} Gold"
            lines.append(f"   🔒 Unlock: {cost_text}")
        lines.append("")
    lines.append("━━━━━━━━━━━━━━")
    lines.append(f"⭐ <b>Skill Points:</b> {kingdom.get('skill_points', 0)}")
    return "\n".join(lines)


async def menu_heroes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show hero roster (callback version)."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    heroes = db.get_heroes(user_id)
    
    if not kingdom:
        await query.edit_message_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    
    ensure_heroes_exist(user_id, heroes)
    heroes = db.get_heroes(user_id)
    
    lines = ["🧙 <b>HERO ROSTER</b>", "━━━━━━━━━━━━━━"]
    
    for hero in heroes:
        hkey = hero['hero_key']
        hero_data = HEROES_DATA.get(hkey, {})
        level = hero.get('level', 1)
        unlocked = hero.get('is_unlocked', 0)
        active = hero.get('is_active', 0)
        
        status = "🔓" if unlocked else "🔒"
        active_status = " ✅ ACTIVE" if active else ""
        
        lines.append(
            f"{hero_data.get('emoji', '⚔️')} <b>{hero_data.get('name', hkey)}</b>{active_status}\n"
            f"   {status} Level: {level}\n"
            f"   🎯 {hero_data.get('skill', '')}"
        )
        
        if not unlocked:
            if hero_data.get('premium'):
                lines.append(f"   💎 Unlock: {hero_data.get('cost_gems', 0)} Gems")
            else:
                lines.append(f"   💰 Unlock: {format_number(hero_data.get('cost_gold', 0))} Gold")
        
        lines.append("")
    
    lines.append("━━━━━━━━━━━━━━")
    lines.append(f"⭐ <b>Skill Points:</b> {kingdom.get('skill_points', 0)}")
    
    await query.edit_message_text(
        text="\n".join(lines),
        reply_markup=heroes_menu_keyboard(heroes),
        parse_mode='HTML'
    )


async def handle_heroes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "menu_heroes":
        await menu_heroes(update, context)
    elif data.startswith("hero_manage:"):
        hero_key = data.split(":")[1]
        await manage_hero(update, context, hero_key)
    elif data.startswith("hero_unlock:"):
        hero_key = data.split(":")[1]
        await unlock_hero(update, context, hero_key)
    elif data.startswith("hero_levelup:"):
        hero_key = data.split(":")[1]
        await levelup_hero(update, context, hero_key)
    elif data.startswith("hero_activate:"):
        hero_key = data.split(":")[1]
        await activate_hero(update, context, hero_key)
    elif data.startswith("skill_"):
        tree = data.split("_")[1]
        await show_skill_tree(update, context, tree)


def ensure_heroes_exist(user_id: int, existing_heroes: list):
    existing_keys = {h['hero_key'] for h in existing_heroes}
    for hkey in HEROES_DATA.keys():
        if hkey not in existing_keys:
            db.conn.cursor().execute(
                'INSERT OR IGNORE INTO heroes (user_id, hero_key, level, is_unlocked, is_active) VALUES (?, ?, 1, 0, 0)',
                (user_id, hkey)
            )
    db.conn.commit()


async def manage_hero(update: Update, context: ContextTypes.DEFAULT_TYPE, hero_key: str):
    """Show hero management screen with portrait image."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    hero = db.get_hero(user_id, hero_key)
    hero_data = HEROES_DATA.get(hero_key, {})
    
    if not hero or not hero.get('is_unlocked'):
        await query.edit_message_text(
            "🔒 <b>Hero Locked!</b>\n\nUnlock this hero first.",
            reply_markup=back_button_keyboard("menu_heroes"),
            parse_mode='HTML'
        )
        return
    
    level = hero.get('level', 1)
    is_active = hero.get('is_active', 0)
    levelup_cost = level * 500
    
    text = f"""
{hero_data.get('emoji', '⚔️')} <b>{hero_data.get('name', hero_key)}</b>
━━━━━━━━━━━━━━

📊 <b>Level:</b> {level}
🎯 <b>Skill:</b> {hero_data.get('skill', '')}

⚔️ <b>Attack Bonus:</b> +{hero_data.get('attack_bonus', 0)*100:.0f}%
🛡 <b>Defense Bonus:</b> +{hero_data.get('defense_bonus', 0)*100:.0f}%

⬆️ <b>Level Up Cost:</b> 💰{format_number(levelup_cost)}

<i>Active heroes give battle bonuses!</i>
"""
    
    hero_img = get_hero_image(hero_key)
    
    if hero_img and os.path.isfile(hero_img):
        try:
            await query.message.reply_photo(
                photo=open(hero_img, 'rb'),
                caption=text,
                reply_markup=hero_manage_keyboard(hero_key, is_active),
                parse_mode='HTML'
            )
            await query.edit_message_reply_markup(reply_markup=None)
            return
        except Exception:
            pass
    
    await query.edit_message_text(
        text=text,
        reply_markup=hero_manage_keyboard(hero_key, is_active),
        parse_mode='HTML'
    )


async def unlock_hero(update: Update, context: ContextTypes.DEFAULT_TYPE, hero_key: str):
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    hero_data = HEROES_DATA.get(hero_key, {})
    
    if not kingdom:
        return
    
    if hero_data.get('premium'):
        cost = hero_data.get('cost_gems', 0)
        if kingdom.get('gems', 0) < cost:
            await query.edit_message_text(
                f"❌ <b>Not enough Gems!</b>\n\nRequired: 💎{cost}\nYou have: 💎{kingdom.get('gems', 0)}",
                reply_markup=back_button_keyboard("menu_heroes"),
                parse_mode='HTML'
            )
            return
        new_gems = kingdom.get('gems', 0) - cost
        db.update_kingdom(user_id, gems=new_gems)
    else:
        cost = hero_data.get('cost_gold', 0)
        if kingdom.get('gold', 0) < cost:
            await query.edit_message_text(
                f"❌ <b>Not enough Gold!</b>\n\nRequired: 💰{format_number(cost)}\nYou have: 💰{format_number(kingdom.get('gold', 0))}",
                reply_markup=back_button_keyboard("menu_heroes"),
                parse_mode='HTML'
            )
            return
        new_gold = kingdom.get('gold', 0) - cost
        db.update_kingdom(user_id, gold=new_gold)
    
    db.update_hero(user_id, hero_key, is_unlocked=1)
    
    hero_img = get_hero_image(hero_key)
    
    if hero_img and os.path.isfile(hero_img):
        try:
            await query.message.reply_photo(
                photo=open(hero_img, 'rb'),
                caption=f"🎉 <b>Hero Unlocked!</b>\n\n{hero_data.get('emoji', '⚔️')} <b>{hero_data.get('name', hero_key)}</b>\n🎯 {hero_data.get('skill', '')}\n\nNow you can manage this hero!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🧙 Hero Roster", callback_data="menu_heroes")]]),
                parse_mode='HTML'
            )
            await query.edit_message_reply_markup(reply_markup=None)
            return
        except Exception:
            pass
    
    await query.edit_message_text(
        f"🎉 <b>Hero Unlocked!</b>\n\n{hero_data.get('emoji', '⚔️')} <b>{hero_data.get('name', hero_key)}</b>\n🎯 {hero_data.get('skill', '')}\n\nNow you can manage this hero!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🧙 Hero Roster", callback_data="menu_heroes")]]),
        parse_mode='HTML'
    )


async def levelup_hero(update: Update, context: ContextTypes.DEFAULT_TYPE, hero_key: str):
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    hero = db.get_hero(user_id, hero_key)
    
    if not kingdom or not hero:
        return
    
    level = hero.get('level', 1)
    cost = level * 500
    
    if kingdom.get('gold', 0) < cost:
        await query.edit_message_text(
            f"❌ <b>Not enough Gold!</b>\n\nRequired: 💰{format_number(cost)}",
            reply_markup=back_button_keyboard("menu_heroes"),
            parse_mode='HTML'
        )
        return
    
    new_gold = kingdom.get('gold', 0) - cost
    db.update_kingdom(user_id, gold=new_gold)
    db.update_hero(user_id, hero_key, level=level + 1)
    
    await query.edit_message_text(
        f"⬆️ <b>Level Up!</b>\n\n{hero_key.replace('_', ' ').title()} → Level {level + 1}\n\n💰 Gold: -{format_number(cost)}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🧙 Hero Roster", callback_data="menu_heroes")]]),
        parse_mode='HTML'
    )


async def activate_hero(update: Update, context: ContextTypes.DEFAULT_TYPE, hero_key: str):
    query = update.callback_query
    user_id = update.effective_user.id
    
    heroes = db.get_heroes(user_id)
    for h in heroes:
        db.update_hero(user_id, h['hero_key'], is_active=0)
    
    db.update_hero(user_id, hero_key, is_active=1)
    db.update_kingdom(user_id, active_hero=hero_key)
    
    hero_data = HEROES_DATA.get(hero_key, {})
    
    await query.edit_message_text(
        f"✅ <b>Hero Activated!</b>\n\n{hero_data.get('emoji', '⚔️')} {hero_data.get('name', hero_key)}\nThis hero will now help in battles!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🧙 Hero Roster", callback_data="menu_heroes")]]),
        parse_mode='HTML'
    )


async def show_skill_tree(update: Update, context: ContextTypes.DEFAULT_TYPE, tree: str):
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    skill_points = kingdom.get('skill_points', 0)
    
    tree_data = SKILL_TREE.get(tree, {})
    tree_emoji = {'attack': '⚔️', 'defense': '🛡', 'economy': '💰'}.get(tree, '⭐')
    tree_name = tree.title()
    
    lines = [f"{tree_emoji} <b>{tree_name} SKILL TREE</b>", "━━━━━━━━━━━━━━"]
    
    for tier, skill in tree_data.items():
        lines.append(
            f"<b>{skill['name']}</b> ({tier})\n"
            f"   🎯 {skill['desc']}\n"
            f"   ⭐ Cost: {skill['cost']} points"
        )
    
    lines.append(f"\n⭐ <b>Available Points:</b> {skill_points}")
    
    await query.edit_message_text(
        text="\n".join(lines),
        reply_markup=skill_tree_keyboard(),
        parse_mode='HTML'
    )

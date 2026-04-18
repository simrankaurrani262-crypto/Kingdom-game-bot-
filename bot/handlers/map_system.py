"""
Map system handler for Kingdom Conquest.
Manages 10x10 grid visualization and tile interactions.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import Database
from utils.keyboards import map_action_keyboard, back_button_keyboard
from config import MAP_SIZE


db = Database()


async def handle_map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /map command."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    await update.message.reply_text(text=_render_map_text(user_id, kingdom), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="menu_map")], [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")]]), parse_mode='HTML')

def _render_map_text(user_id: int, kingdom: dict) -> str:
    all_kingdoms = db.get_all_kingdoms()
    alliance = db.get_alliance_by_member(user_id)
    ally_ids = set()
    if alliance:
        members = db.get_alliance_members(alliance['id'])
        ally_ids = set(m['user_id'] for m in members)
    positions = {}
    for k in all_kingdoms:
        px, py = k.get('map_x'), k.get('map_y')
        if px and py: positions[(px, py)] = k
    lines = ["🗺 <b>KINGDOM MAP</b>", "━━━━━━━━━━━━━━", ""]
    header = "    "
    for x in range(1, MAP_SIZE + 1): header += f"{x:2d} "
    lines.append(header); lines.append("")
    for y in range(1, MAP_SIZE + 1):
        row = f"{y:2d}  "
        for x in range(1, MAP_SIZE + 1):
            occ = positions.get((x, y))
            if not occ: row += "⬜ "
            elif occ['user_id'] == user_id: row += "🟩 "
            elif occ['user_id'] in ally_ids: row += "🟦 "
            else: row += "🟥 "
        lines.append(row)
    lines.append(""); lines.append("🟩 You | 🟦 Ally | 🟥 Enemy | ⬜ Empty")
    lines.append(f"\n📍 <b>Your Position:</b> ({kingdom.get('map_x', 0)}, {kingdom.get('map_y', 0)})")
    return "\n".join(lines)

async def menu_map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Render the 10x10 world map (callback version)."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        if query:
            await query.edit_message_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    
    # Get all kingdoms
    all_kingdoms = db.get_all_kingdoms()
    
    # Get user's alliance
    alliance = db.get_alliance_by_member(user_id)
    ally_ids = set()
    if alliance:
        members = db.get_alliance_members(alliance['id'])
        ally_ids = set(m['user_id'] for m in members)
    
    # Build map grid
    grid_lines = ["🗺 <b>KINGDOM MAP</b>", "━━━━━━━━━━━━━━", ""]
    
    # Header row
    header = "    "
    for x in range(1, MAP_SIZE + 1):
        header += f"{x:2d} "
    grid_lines.append(header)
    grid_lines.append("")
    
    # Build position lookup
    positions = {}
    for k in all_kingdoms:
        px = k.get('map_x')
        py = k.get('map_y')
        if px and py:
            positions[(px, py)] = k
    
    # Grid rows
    for y in range(1, MAP_SIZE + 1):
        row = f"{y:2d}  "
        for x in range(1, MAP_SIZE + 1):
            occupant = positions.get((x, y))
            if not occupant:
                row += "⬜ "
            elif occupant['user_id'] == user_id:
                row += "🟩 "
            elif occupant['user_id'] in ally_ids:
                row += "🟦 "
            else:
                row += "🟥 "
        grid_lines.append(row)
    
    grid_lines.append("")
    grid_lines.append("🟩 You | 🟦 Ally | 🟥 Enemy | ⬜ Empty")
    grid_lines.append(f"\n📍 <b>Your Position:</b> ({kingdom.get('map_x', 0)}, {kingdom.get('map_y', 0)})")
    grid_lines.append("<i>Kisi tile par attack ya scout karne ke liye coordinates type karo:</i>")
    grid_lines.append("<b>Example:</b> /scout 5 3")
    
    text = "\n".join(grid_lines)
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="menu_map")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
    ]
    
    if query:
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )


async def handle_map_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle map-related callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "menu_map":
        await menu_map(update, context)
    elif data.startswith("map_attack:"):
        parts = data.split(":")
        x, y = int(parts[1]), int(parts[2])
        await scout_tile(update, context, x, y)
    elif data.startswith("map_spy:"):
        parts = data.split(":")
        x, y = int(parts[1]), int(parts[2])
        await scout_tile(update, context, x, y)


async def scout_tile(update: Update, context: ContextTypes.DEFAULT_TYPE, x: int, y: int):
    """Show information about a map tile."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Find kingdom at position
    all_kingdoms = db.get_all_kingdoms()
    occupant = None
    for k in all_kingdoms:
        if k.get('map_x') == x and k.get('map_y') == y:
            occupant = k
            break
    
    if not occupant:
        await query.edit_message_text(
            f"📍 <b>({x}, {y})</b>\n\n"
            f"⬜ <b>Empty Land</b>\n\n"
            f"Yahan koi kingdom nahi hai.",
            reply_markup=back_button_keyboard("menu_map"),
            parse_mode='HTML'
        )
        return
    
    is_self = occupant['user_id'] == user_id
    alliance = db.get_alliance_by_member(user_id)
    is_ally = False
    if alliance:
        members = db.get_alliance_members(alliance['id'])
        ally_ids = set(m['user_id'] for m in members)
        is_ally = occupant['user_id'] in ally_ids
    
    # Calculate distance
    my_kingdom = db.get_kingdom(user_id)
    distance = 0
    if my_kingdom:
        distance = abs(my_kingdom.get('map_x', 0) - x) + abs(my_kingdom.get('map_y', 0) - y)
    
    text = f"""
👑 <b>Kingdom:</b> {occupant.get('kingdom_name', 'Unknown')} {occupant.get('flag', '')}
━━━━━━━━━━━━━━

🏆 <b>Level:</b> {occupant.get('level', 1)}
⚔️ <b>Army:</b> ~{occupant.get('power', 0) // 10} (estimated)
⚡ <b>Power:</b> {occupant.get('power', 0):,}
🟢 <b>Status:</b> {occupant.get('status', 'Online')}
📍 <b>Distance:</b> {distance} tiles
"""
    
    keyboard = []
    if not is_self and not is_ally:
        keyboard.append([
            InlineKeyboardButton("⚔️ Attack", callback_data=f"attack_start:{occupant['user_id']}"),
            InlineKeyboardButton("🕵️ Spy", callback_data=f"spy_target:{occupant['user_id']}"),
        ])
        keyboard.append([
            InlineKeyboardButton("🤝 Invite Alliance", callback_data=f"alliance_invite:{occupant['user_id']}"),
        ])
    keyboard.append([InlineKeyboardButton("🔙 Back to Map", callback_data="menu_map")])
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def handle_scout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /scout command."""
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "❌ <b>Usage:</b> /scout x y\n\n"
                "Example: /scout 5 3",
                parse_mode='HTML'
            )
            return
        
        x = int(args[0])
        y = int(args[1])
        
        if x < 1 or x > MAP_SIZE or y < 1 or y > MAP_SIZE:
            await update.message.reply_text(
                f"❌ Invalid coordinates! 1-{MAP_SIZE} allowed.",
                parse_mode='HTML'
            )
            return
        
        # Show tile info
        user_id = update.effective_user.id
        all_kingdoms = db.get_all_kingdoms()
        occupant = None
        for k in all_kingdoms:
            if k.get('map_x') == x and k.get('map_y') == y:
                occupant = k
                break
        
        if not occupant:
            await update.message.reply_text(
                f"📍 <b>({x}, {y})</b> - Empty Land\n\n"
                f"Yahan koi kingdom nahi hai.",
                parse_mode='HTML'
            )
            return
        
        await update.message.reply_text(
            f"👑 <b>{occupant.get('kingdom_name', 'Unknown')}</b> {occupant.get('flag', '')}\n"
            f"🏆 Level: {occupant.get('level', 1)}\n"
            f"⚔️ Power: {occupant.get('power', 0):,}\n"
            f"🟢 Status: {occupant.get('status', 'Online')}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚔️ Attack", callback_data=f"attack_start:{occupant['user_id']}")],
            ]),
            parse_mode='HTML'
        )
    
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ <b>Invalid coordinates!</b>\n"
            "Usage: /scout x y",
            parse_mode='HTML'
        )

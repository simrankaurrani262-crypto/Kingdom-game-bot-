"""
Bounty system handler for Kingdom Conquest.
Place and claim bounties on players.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import Database
from utils.formatters import format_number
from utils.keyboards import back_button_keyboard


db = Database()


async def menu_bounty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bounty board."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    
    if not kingdom:
        await query.edit_message_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    
    # Get active bounties
    bounties = db.get_active_bounties()
    
    text_lines = [
        "💰 <b>BOUNTY BOARD</b>",
        "━━━━━━━━━━━━━━",
        "",
    ]
    
    if bounties:
        text_lines.append("<b>Active Bounties:</b>")
        for b in bounties:
            target = db.get_kingdom(b['target_id'])
            target_name = target.get('kingdom_name', 'Unknown') if target else 'Unknown'
            text_lines.append(
                f"💰 {format_number(b['reward_gold'])} Gold — {target_name}"
            )
    else:
        text_lines.append("<i>Koi active bounty nahi hai.</i>")
    
    text_lines.append("")
    text_lines.append("<b>Commands:</b>")
    text_lines.append("/bounty &lt;@user&gt; &lt;amount&gt; - Bounty lagao")
    text_lines.append("/bounties - Sab bounties dekho")
    
    text = "\n".join(text_lines)
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
        ]),
        parse_mode='HTML'
    )


async def handle_bounty_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /bounty command."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    
    if not kingdom:
        await update.message.reply_text("❌ Kingdom not found! /start se shuru karo.", parse_mode='HTML')
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ <b>Usage:</b> /bounty @user &lt;amount&gt;\n\n"
            "Example: /bounty @enemy 1000",
            parse_mode='HTML'
        )
        return
    
    target_username = context.args[0].replace("@", "")
    try:
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number!")
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ Amount positive hona chahiye!")
        return
    
    if kingdom.get('gold', 0) < amount:
        await update.message.reply_text(
            f"❌ <b>Not enough Gold!</b>\n"
            f"Required: 💰{format_number(amount)}\n"
            f"You have: 💰{format_number(kingdom.get('gold', 0))}",
            parse_mode='HTML'
        )
        return
    
    # Find target
    users = db.get_all_users()
    target = None
    for u in users:
        if u.get('username') == target_username:
            target = u
            break
    
    if not target:
        await update.message.reply_text(f"❌ User @{target_username} not found!")
        return
    
    # Deduct gold
    new_gold = kingdom.get('gold', 0) - amount
    db.update_kingdom(user_id, gold=new_gold)
    
    # Create bounty
    db.create_bounty(user_id, target['telegram_id'], amount)
    
    # Notify target
    try:
        await context.bot.send_message(
            chat_id=target['telegram_id'],
            text=f"💰 <b>BOUNTY ALERT!</b>\n\n"
                 f"Kisi ne aap par <b>{format_number(amount)} Gold</b> ka inaam rakha hai!\n"
                 f"Savdhaan rahein!",
            parse_mode='HTML'
        )
    except Exception:
        pass
    
    await update.message.reply_text(
        f"💰 <b>Bounty Placed!</b>\n\n"
        f"Target: @{target_username}\n"
        f"Reward: 💰{format_number(amount)} Gold\n\n"
        f"Jo bhi is player ko harega, usse bounty milegi!",
        parse_mode='HTML'
    )


async def handle_bounties_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /bounties command."""
    bounties = db.get_active_bounties()
    
    if not bounties:
        await update.message.reply_text(
            "💰 <b>BOUNTY BOARD</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            "Koi active bounty nahi hai.",
            parse_mode='HTML'
        )
        return
    
    lines = ["💰 <b>ACTIVE BOUNTIES</b>", "━━━━━━━━━━━━━━", ""]
    
    for b in bounties:
        target = db.get_kingdom(b['target_id'])
        target_name = target.get('kingdom_name', 'Unknown') if target else 'Unknown'
        lines.append(f"💰 {format_number(b['reward_gold'])} Gold — {target_name}")
    
    await update.message.reply_text("\n".join(lines), parse_mode='HTML')

"""
Admin handler for Kingdom Conquest.
Moderation commands, warnings, bans, and broadcast.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import Database
from config import ADMIN_TELEGRAM_ID
from utils.formatters import format_number


db = Database()


async def handle_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin commands."""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_TELEGRAM_ID:
        await update.message.reply_text("⛔ Admin access only!")
        return
    
    if not context.args:
        await show_admin_help(update, context)
        return
    
    command = context.args[0].lower()
    
    if command == "warn":
        await admin_warn(update, context)
    elif command == "ban":
        await admin_ban(update, context)
    elif command == "unban":
        await admin_unban(update, context)
    elif command == "give":
        await admin_give(update, context)
    elif command == "broadcast":
        await admin_broadcast(update, context)
    elif command == "stats":
        await admin_stats(update, context)
    elif command == "maintenance":
        await admin_maintenance(update, context)
    else:
        await show_admin_help(update, context)


async def show_admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin command help."""
    text = """
🛡 <b>ADMIN COMMANDS</b>
━━━━━━━━━━━━━━

/admin warn @user &lt;reason&gt;
/admin ban @user &lt;days&gt; &lt;reason&gt;
/admin unban @user
/admin give @user &lt;gold|gems|food&gt; &lt;amount&gt;
/admin broadcast &lt;message&gt;
/admin stats
/admin maintenance &lt;on|off&gt;
"""
    
    await update.message.reply_text(text, parse_mode='HTML')


async def admin_warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Warn a user."""
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /admin warn @user <reason>", parse_mode='HTML')
        return
    
    username = context.args[1].replace("@", "")
    reason = " ".join(context.args[2:])
    
    # Find user by username
    users = db.get_all_users()
    target = None
    for u in users:
        if u.get('username') == username:
            target = u
            break
    
    if not target:
        await update.message.reply_text(f"❌ User @{username} not found!")
        return
    
    # Increment warning
    current_warnings = target.get('warning_count', 0)
    db.conn.cursor().execute(
        'UPDATE users SET warning_count = ? WHERE telegram_id = ?',
        (current_warnings + 1, target['telegram_id'])
    )
    db.conn.commit()
    
    # Notify user
    try:
        await context.bot.send_message(
            chat_id=target['telegram_id'],
            text=f"🟡 <b>WARNING #{current_warnings + 1}</b>\n\n"
                 f"Reason: {reason}\n\n"
                 f"Please follow the rules!",
            parse_mode='HTML'
        )
    except Exception:
        pass
    
    await update.message.reply_text(
        f"🟡 <b>Warned</b> @{username}\n"
        f"Warning #{current_warnings + 1}\n"
        f"Reason: {reason}",
        parse_mode='HTML'
    )


async def admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user."""
    if len(context.args) < 4:
        await update.message.reply_text("Usage: /admin ban @user <days> <reason>", parse_mode='HTML')
        return
    
    username = context.args[1].replace("@", "")
    try:
        days = int(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ Days must be a number!")
        return
    
    reason = " ".join(context.args[3:])
    
    # Find user
    users = db.get_all_users()
    target = None
    for u in users:
        if u.get('username') == username:
            target = u
            break
    
    if not target:
        await update.message.reply_text(f"❌ User @{username} not found!")
        return
    
    db.ban_user(target['telegram_id'], reason, days)
    
    # Notify user
    try:
        await context.bot.send_message(
            chat_id=target['telegram_id'],
            text=f"🔴 <b>BANNED</b>\n\n"
                 f"Duration: {days} days\n"
                 f"Reason: {reason}\n\n"
                 f"Appeal: Contact admin",
            parse_mode='HTML'
        )
    except Exception:
        pass
    
    await update.message.reply_text(
        f"🔴 <b>Banned</b> @{username}\n"
        f"Duration: {days} days\n"
        f"Reason: {reason}",
        parse_mode='HTML'
    )


async def admin_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user."""
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /admin unban @user", parse_mode='HTML')
        return
    
    username = context.args[1].replace("@", "")
    
    users = db.get_all_users()
    target = None
    for u in users:
        if u.get('username') == username:
            target = u
            break
    
    if not target:
        await update.message.reply_text(f"❌ User @{username} not found!")
        return
    
    db.unban_user(target['telegram_id'])
    
    await update.message.reply_text(
        f"✅ <b>Unbanned</b> @{username}",
        parse_mode='HTML'
    )


async def admin_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Give resources to a user."""
    if len(context.args) < 4:
        await update.message.reply_text("Usage: /admin give @user <gold|gems|food> <amount>", parse_mode='HTML')
        return
    
    username = context.args[1].replace("@", "")
    resource = context.args[2].lower()
    try:
        amount = int(context.args[3])
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number!")
        return
    
    # Find user
    users = db.get_all_users()
    target = None
    for u in users:
        if u.get('username') == username:
            target = u
            break
    
    if not target:
        await update.message.reply_text(f"❌ User @{username} not found!")
        return
    
    kingdom = db.get_kingdom(target['telegram_id'])
    if not kingdom:
        await update.message.reply_text("❌ User has no kingdom!")
        return
    
    if resource == 'gold':
        new_amount = kingdom.get('gold', 0) + amount
        db.update_kingdom(target['telegram_id'], gold=new_amount)
    elif resource == 'gems':
        new_amount = kingdom.get('gems', 0) + amount
        db.update_kingdom(target['telegram_id'], gems=new_amount)
    elif resource == 'food':
        new_amount = kingdom.get('food', 0) + amount
        db.update_kingdom(target['telegram_id'], food=new_amount)
    else:
        await update.message.reply_text("❌ Resource must be gold/gems/food!")
        return
    
    # Notify user
    try:
        resource_emoji = {'gold': '💰', 'gems': '💎', 'food': '🍖'}.get(resource, '💰')
        await context.bot.send_message(
            chat_id=target['telegram_id'],
            text=f"🎁 <b>Admin Gift!</b>\n\n"
                 f"{resource_emoji} +{format_number(amount)} {resource.title()}!",
            parse_mode='HTML'
        )
    except Exception:
        pass
    
    await update.message.reply_text(
        f"✅ Gave {format_number(amount)} {resource} to @{username}",
        parse_mode='HTML'
    )


async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users."""
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /admin broadcast <message>", parse_mode='HTML')
        return
    
    message = " ".join(context.args[1:])
    
    # Get all users
    users = db.get_all_users()
    sent = 0
    failed = 0
    
    await update.message.reply_text(f"📢 Broadcasting to {len(users)} users...")
    
    for u in users:
        try:
            await context.bot.send_message(
                chat_id=u['telegram_id'],
                text=f"📢 <b>ANNOUNCEMENT</b>\n\n{message}",
                parse_mode='HTML'
            )
            sent += 1
            await asyncio.sleep(0.05)  # Rate limit
        except Exception:
            failed += 1
    
    await update.message.reply_text(
        f"✅ Broadcast complete!\n"
        f"Sent: {sent}\n"
        f"Failed: {failed}",
        parse_mode='HTML'
    )


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics."""
    stats = db.get_stats()
    
    text = f"""
📊 <b>BOT STATISTICS</b>
━━━━━━━━━━━━━━

👥 <b>Total Users:</b> {stats.get('total_users', 0)}
🏰 <b>Total Kingdoms:</b> {stats.get('total_kingdoms', 0)}
⚔️ <b>Total Battles:</b> {stats.get('total_battles', 0)}
🤝 <b>Total Alliances:</b> {stats.get('total_alliances', 0)}
💰 <b>Total Gold:</b> {format_number(stats.get('total_gold', 0))}

<i>Real-time statistics</i>
"""
    
    await update.message.reply_text(text, parse_mode='HTML')


async def admin_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle maintenance mode."""
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /admin maintenance <on|off>", parse_mode='HTML')
        return
    
    mode = context.args[1].lower()
    
    # Store in context.bot_data
    context.bot_data['maintenance'] = (mode == 'on')
    
    status = "ON 🔧" if mode == 'on' else "OFF ✅"
    
    await update.message.reply_text(
        f"🔧 <b>Maintenance Mode:</b> {status}",
        parse_mode='HTML'
    )


async def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id == ADMIN_TELEGRAM_ID

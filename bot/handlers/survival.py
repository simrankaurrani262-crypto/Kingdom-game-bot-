"""
Survival mode handler for Kingdom Conquest.
Co-op PvE survival against waves of enemies.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import random

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import Database
from config import SURVIVAL_WAVES
from utils.formatters import format_number
from utils.keyboards import back_button_keyboard


db = Database()


async def handle_survival(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /survival command."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    text = """🛡 <b>SURVIVAL MODE</b>
━━━━━━━━━━━━━━
<b>Wave-based PvE battles!</b>
Apni army se enemy waves ko roko!
🧟 Wave 1: 50 Skeletons - 💰 500 Gold
👹 Wave 2: 100 Goblins - 💰 1,000 Gold
🐺 Wave 3: 200 Werewolves - 💰 2,000 Gold
🐉 Wave 4: 350 Dragons - 💰 5,000 Gold
💀 Wave 5: 500 Demon Lord - 💰 10,000 Gold"""
    await update.message.reply_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚔️ Start Survival", callback_data="survival_start")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")]
        ]),
        parse_mode='HTML'
    )


async def menu_survival(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show survival mode menu."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    
    if not kingdom:
        await query.edit_message_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    
    text = """
🛡 <b>SURVIVAL MODE</b>
━━━━━━━━━━━━━━

<b>Wave-based PvE battles!</b>

Apni army se enemy waves ko roko!
Jitni zyada waves survive karo, utna bada reward!

<b>Waves:</b>
🧟 Wave 1: 50 Skeletons - 💰 500 Gold
👹 Wave 2: 100 Goblins - 💰 1,000 Gold
🐺 Wave 3: 200 Werewolves - 💰 2,000 Gold
🐉 Wave 4: 350 Dragons - 💰 5,000 Gold
💀 Wave 5: 500 Demon Lord - 💰 10,000 Gold

<i>Solo ya alliance members ke saath khelo!</i>
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚔️ Start Survival", callback_data="survival_start")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
        ]),
        parse_mode='HTML'
    )


async def handle_survival_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle survival mode callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "menu_survival":
        await menu_survival(update, context)
    elif data == "survival_start":
        await start_survival(update, context)
    elif data.startswith("survival_fight:"):
        wave = int(data.split(":")[1])
        await fight_wave(update, context, wave)


async def start_survival(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start survival mode - Wave 1."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    army = db.get_army(user_id)
    
    if not kingdom or not army:
        return
    
    total_army = army.get('infantry', 0) + army.get('archers', 0) + army.get('cavalry', 0)
    
    if total_army <= 0:
        await query.edit_message_text(
            "❌ <b>No Army!</b>\n\n"
            "Pehle army train karo!",
            reply_markup=back_button_keyboard("menu_survival"),
            parse_mode='HTML'
        )
        return
    
    context.user_data['survival_wave'] = 0
    context.user_data['survival_army'] = total_army
    
    await fight_wave(update, context, 0)


async def fight_wave(update: Update, context: ContextTypes.DEFAULT_TYPE, wave_idx: int):
    """Fight a survival wave."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if wave_idx >= len(SURVIVAL_WAVES):
        # All waves completed
        total_reward = sum(w['reward_gold'] for w in SURVIVAL_WAVES)
        kingdom = db.get_kingdom(user_id)
        if kingdom:
            new_gold = kingdom.get('gold', 0) + total_reward
            db.update_kingdom(user_id, gold=new_gold)
        
        await query.edit_message_text(
            f"🏆 <b>SURVIVAL COMPLETE!</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"🎉 Sab {len(SURVIVAL_WAVES)} waves survive kiye!\n\n"
            f"💰 Total Reward: {format_number(total_reward)} Gold\n\n"
            f"<b>Aap ek legend hain!</b>",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Dashboard", callback_data="back_dashboard")],
            ]),
            parse_mode='HTML'
        )
        return
    
    wave = SURVIVAL_WAVES[wave_idx]
    user_army = context.user_data.get('survival_army', 100)
    
    # Calculate battle result
    enemy_power = wave['enemies'] * 5
    user_power = user_army * 8
    
    win_chance = min(0.95, user_power / (user_power + enemy_power))
    won = random.random() < win_chance
    
    if won:
        # Calculate losses
        losses = int(wave['enemies'] * random.uniform(0.05, 0.15))
        remaining_army = max(0, user_army - losses)
        context.user_data['survival_army'] = remaining_army
        
        # Reward
        kingdom = db.get_kingdom(user_id)
        if kingdom:
            new_gold = kingdom.get('gold', 0) + wave['reward_gold']
            db.update_kingdom(user_id, gold=new_gold)
        
        text = f"""
✅ <b>WAVE {wave['wave']} CLEARED!</b>
━━━━━━━━━━━━━━

🧟 <b>Enemies:</b> {wave['enemies']} {wave['type']}
💀 <b>Your Losses:</b> {losses} soldiers
⚔️ <b>Remaining Army:</b> {remaining_army}

🎁 <b>Reward:</b> 💰{format_number(wave['reward_gold'])} Gold
"""
        
        if wave_idx + 1 < len(SURVIVAL_WAVES):
            next_wave = SURVIVAL_WAVES[wave_idx + 1]
            text += f"\n➡️ <b>Next Wave:</b> {next_wave['enemies']} {next_wave['type']}"
            keyboard = [
                [InlineKeyboardButton(f"⚔️ Fight Wave {wave_idx + 2}", callback_data=f"survival_fight:{wave_idx + 1}")],
                [InlineKeyboardButton("🏃 Retreat", callback_data="back_dashboard")],
            ]
        else:
            keyboard = [
                [InlineKeyboardButton("🏆 Claim Final Reward", callback_data=f"survival_fight:{wave_idx + 1}")],
            ]
    else:
        # Defeated
        text = f"""
💀 <b>WAVE {wave['wave']} DEFEAT!</b>
━━━━━━━━━━━━━━

🧟 <b>Enemies:</b> {wave['enemies']} {wave['type']}

<i>Aapki army haar gayi!</i>

🎁 <b>Rewards earned so far:</b> 💰{format_number(sum(w['reward_gold'] for w in SURVIVAL_WAVES[:wave_idx]))} Gold
"""
        keyboard = [
            [InlineKeyboardButton("🔄 Try Again", callback_data="survival_start")],
            [InlineKeyboardButton("🏠 Dashboard", callback_data="back_dashboard")],
        ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

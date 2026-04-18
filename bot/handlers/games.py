"""
Mini-games handler for Kingdom Conquest.
Dice game, lucky spin, and kingdom quiz.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import random

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import Database
from config import (
    DICE_COOLDOWN_HOURS, SPIN_COOLDOWN_HOURS, QUIZ_COOLDOWN_HOURS,
    MAX_ENERGY, QUIZ_QUESTIONS
)
from utils.formatters import format_number
from utils.keyboards import games_menu_keyboard, dice_game_keyboard, spin_wheel_keyboard, quiz_keyboard, back_button_keyboard


db = Database()

# Track game states
user_dice_bets = {}


async def handle_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /games command."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    text = """🎲 <b>MINI-GAMES</b>
━━━━━━━━━━━━━━
🎲 <b>Dice Game</b> - Dice roll karke Gold jeeto! (4h cooldown)
🎰 <b>Lucky Spin</b> - Wheel ghumao, prizes jeeto! (8h cooldown)
🧠 <b>Kingdom Quiz</b> - Sawaal jawab do, rewards lo! (6h cooldown)
<i>Mini-games se extra Gold aur rewards milte hain!</i>"""
    await update.message.reply_text(text=text, reply_markup=games_menu_keyboard(), parse_mode='HTML')


async def menu_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show mini-games menu."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    
    if not kingdom:
        await query.edit_message_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    
    text = """
🎲 <b>MINI-GAMES</b>
━━━━━━━━━━━━━━

🎲 <b>Dice Game</b>
   Dice roll karke Gold jeeto!
   Cooldown: 4 hours

🎰 <b>Lucky Spin</b>
   Wheel ghumao, prizes jeeto!
   Cooldown: 8 hours

🧠 <b>Kingdom Quiz</b>
   Sawaal jawab do, rewards lo!
   Cooldown: 6 hours

<i>Mini-games se extra Gold aur rewards milte hain!</i>
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=games_menu_keyboard(),
        parse_mode='HTML'
    )


async def handle_games_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mini-games menu callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "menu_games":
        await menu_games(update, context)
    elif data == "game_dice":
        await show_dice_game(update, context)
    elif data == "game_spin":
        await show_spin_wheel(update, context)
    elif data == "game_quiz":
        await show_quiz(update, context)
    elif data.startswith("dice_bet:"):
        bet = int(data.split(":")[1])
        await set_dice_bet(update, context, bet)
    elif data == "dice_roll":
        await roll_dice(update, context)
    elif data == "spin_spin":
        await spin_wheel(update, context)
    elif data.startswith("quiz_answer:"):
        parts = data.split(":")
        q_idx = int(parts[1])
        answer = int(parts[2])
        await answer_quiz(update, context, q_idx, answer)


# ==================== DICE GAME ====================

async def show_dice_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show dice game interface."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check cooldown
    cooldown = db.get_cooldown_remaining(user_id, 'dice')
    if cooldown > 0:
        hours = cooldown // 3600
        mins = (cooldown % 3600) // 60
        await query.edit_message_text(
            f"⏳ <b>Dice Cooldown!</b>\n\n"
            f"{hours}h {mins}m baad try karo.",
            reply_markup=back_button_keyboard("menu_games"),
            parse_mode='HTML'
        )
        return
    
    # Default bet
    user_dice_bets[user_id] = 100
    
    text = """
🎲 <b>DICE GAME</b>
━━━━━━━━━━━━━━

🎲 <b>Roll the dice!</b>

<b>Outcomes:</b>
🎲 1-2: ❌ Lose your bet
🎲 3-4: ➡️ Keep your bet
🎲 5: 💰 Win 2x your bet
🎲 6: 🔥 Win 5x your bet!

<b>Select your bet:</b>
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=dice_game_keyboard(),
        parse_mode='HTML'
    )


async def set_dice_bet(update: Update, context: ContextTypes.DEFAULT_TYPE, bet: int):
    """Set dice bet amount."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        return
    
    if kingdom.get('gold', 0) < bet:
        await query.answer("❌ Not enough Gold!", show_alert=True)
        return
    
    user_dice_bets[user_id] = bet
    
    await query.answer(f"💰 Bet set: {bet} Gold")
    
    # Update text to show selected bet
    text = f"""
🎲 <b>DICE GAME</b>
━━━━━━━━━━━━━━

🎲 <b>Roll the dice!</b>

<b>Outcomes:</b>
🎲 1-2: ❌ Lose your bet
🎲 3-4: ➡️ Keep your bet
🎲 5: 💰 Win 2x your bet
🎲 6: 🔥 Win 5x your bet!

💰 <b>Your Bet: {format_number(bet)} Gold</b>
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=dice_game_keyboard(),
        parse_mode='HTML'
    )


async def roll_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roll the dice."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        return
    
    bet = user_dice_bets.get(user_id, 100)
    
    if kingdom.get('gold', 0) < bet:
        await query.edit_message_text(
            "❌ <b>Not enough Gold!</b>",
            reply_markup=back_button_keyboard("menu_games"),
            parse_mode='HTML'
        )
        return
    
    # Set cooldown
    expires = datetime.now() + timedelta(hours=DICE_COOLDOWN_HOURS)
    db.set_cooldown(user_id, 'dice', expires)
    
    # Roll dice
    roll = random.randint(1, 6)
    
    # Calculate result
    if roll <= 2:
        # Lose bet
        new_gold = kingdom.get('gold', 0) - bet
        db.update_kingdom(user_id, gold=new_gold)
        
        result = f"❌ <b>LOST!</b>\n\n🎲 Rolled: {roll}\n💰 -{format_number(bet)} Gold"
    elif roll <= 4:
        # Keep bet (no change)
        result = f"➡️ <b>BREAK EVEN!</b>\n\n🎲 Rolled: {roll}\n💰 Bet returned"
    elif roll == 5:
        # Win 2x
        winnings = bet * 2
        new_gold = kingdom.get('gold', 0) + winnings
        db.update_kingdom(user_id, gold=new_gold)
        
        result = f"💰 <b>WIN!</b>\n\n🎲 Rolled: {roll}\n💰 +{format_number(winnings)} Gold"
    else:
        # Win 5x
        winnings = bet * 5
        new_gold = kingdom.get('gold', 0) + winnings
        db.update_kingdom(user_id, gold=new_gold)
        
        result = f"🔥 <b>JACKPOT!</b>\n\n🎲 Rolled: {roll}\n💰 +{format_number(winnings)} Gold"
    
    await query.edit_message_text(
        f"🎲 <b>DICE ROLL</b>\n━━━━━━━━━━━━━━\n\n{result}\n\n⏳ Next roll: {DICE_COOLDOWN_HOURS}h",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎲 Play Again", callback_data="game_dice")],
            [InlineKeyboardButton("🎲 Games Menu", callback_data="menu_games")],
        ]),
        parse_mode='HTML'
    )


# ==================== SPIN WHEEL ====================

async def show_spin_wheel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show lucky spin interface."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check cooldown
    cooldown = db.get_cooldown_remaining(user_id, 'spin')
    if cooldown > 0:
        hours = cooldown // 3600
        mins = (cooldown % 3600) // 60
        await query.edit_message_text(
            f"⏳ <b>Spin Cooldown!</b>\n\n"
            f"{hours}h {mins}m baad try karo.",
            reply_markup=back_button_keyboard("menu_games"),
            parse_mode='HTML'
        )
        return
    
    text = """
🎰 <b>LUCKY SPIN</b>
━━━━━━━━━━━━━━

🎰 <b>Wheel ghumao!</b>

<b>Prizes:</b>
💎 50 Gems
💰 5,000 Gold
🍖 2,000 Food
⚡ Full Energy
🛡 12h Shield
❌ Nothing
🎁 Mystery Box

<i>Free har {SPIN_COOLDOWN_HOURS} hours!</i>
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=spin_wheel_keyboard(),
        parse_mode='HTML'
    )


async def spin_wheel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Spin the wheel."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        return
    
    # Set cooldown
    expires = datetime.now() + timedelta(hours=SPIN_COOLDOWN_HOURS)
    db.set_cooldown(user_id, 'spin', expires)
    
    # Define prizes with weights
    prizes = [
        ('💎 50 Gems', 'gems', 50, 0.05),
        ('💰 5,000 Gold', 'gold', 5000, 0.20),
        ('🍖 2,000 Food', 'food', 2000, 0.20),
        ('⚡ Full Energy', 'energy', MAX_ENERGY, 0.15),
        ('🛡 12h Shield', 'shield', 12, 0.10),
        ('❌ Nothing', 'nothing', 0, 0.15),
        ('🎁 Mystery Box', 'mystery', 1, 0.15),
    ]
    
    # Weighted random selection
    total_weight = sum(p[3] for p in prizes)
    r = random.uniform(0, total_weight)
    cumulative = 0
    selected = prizes[0]
    
    for prize in prizes:
        cumulative += prize[3]
        if r <= cumulative:
            selected = prize
            break
    
    prize_name, prize_type, prize_value = selected[0], selected[1], selected[2]
    
    # Apply prize
    result_message = ""
    if prize_type == 'gems':
        new_gems = kingdom.get('gems', 0) + prize_value
        db.update_kingdom(user_id, gems=new_gems)
        result_message = f"💎 +{prize_value} Gems!"
    elif prize_type == 'gold':
        new_gold = kingdom.get('gold', 0) + prize_value
        db.update_kingdom(user_id, gold=new_gold)
        result_message = f"💰 +{format_number(prize_value)} Gold!"
    elif prize_type == 'food':
        new_food = kingdom.get('food', 0) + prize_value
        db.update_kingdom(user_id, food=new_food)
        result_message = f"🍖 +{format_number(prize_value)} Food!"
    elif prize_type == 'energy':
        db.update_kingdom(user_id, energy=MAX_ENERGY)
        result_message = f"⚡ Energy full!"
    elif prize_type == 'shield':
        shield_expires = datetime.now() + timedelta(hours=prize_value)
        db.update_kingdom(user_id, shield_expires=shield_expires)
        result_message = f"🛡 {prize_value}h Shield activated!"
    elif prize_type == 'nothing':
        result_message = "❌ Kuch nahi mila! Better luck next time!"
    elif prize_type == 'mystery':
        # Random mystery reward
        mystery_gold = random.randint(100, 2000)
        new_gold = kingdom.get('gold', 0) + mystery_gold
        db.update_kingdom(user_id, gold=new_gold)
        result_message = f"🎁 Mystery: +{format_number(mystery_gold)} Gold!"
    
    await query.edit_message_text(
        f"🎰 <b>SPIN RESULT</b>\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"🎰 Wheel stopped at:\n"
        f"<b>{prize_name}</b>\n\n"
        f"{result_message}\n\n"
        f"⏳ Next spin: {SPIN_COOLDOWN_HOURS}h",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎰 Spin Again", callback_data="game_spin")],
            [InlineKeyboardButton("🎲 Games Menu", callback_data="menu_games")],
        ]),
        parse_mode='HTML'
    )


# ==================== QUIZ ====================

async def show_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show quiz question."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check cooldown
    cooldown = db.get_cooldown_remaining(user_id, 'quiz')
    if cooldown > 0:
        hours = cooldown // 3600
        mins = (cooldown % 3600) // 60
        await query.edit_message_text(
            f"⏳ <b>Quiz Cooldown!</b>\n\n"
            f"{hours}h {mins}m baad try karo.",
            reply_markup=back_button_keyboard("menu_games"),
            parse_mode='HTML'
        )
        return
    
    # Select random question
    question = random.choice(QUIZ_QUESTIONS)
    q_idx = QUIZ_QUESTIONS.index(question)
    
    text = f"""
🧠 <b>KINGDOM QUIZ</b>
━━━━━━━━━━━━━━

❓ <b>{question['question']}</b>

<i>Sahi jawab = {question['reward_gold']} Gold + {question['reward_xp']} XP</i>
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=quiz_keyboard(q_idx, question['options'], question['correct']),
        parse_mode='HTML'
    )


async def answer_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE,
                     q_idx: int, answer: int):
    """Process quiz answer."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if q_idx >= len(QUIZ_QUESTIONS):
        return
    
    question = QUIZ_QUESTIONS[q_idx]
    correct = question['correct']
    
    # Set cooldown
    expires = datetime.now() + timedelta(hours=QUIZ_COOLDOWN_HOURS)
    db.set_cooldown(user_id, 'quiz', expires)
    
    if answer == correct:
        # Correct answer
        kingdom = db.get_kingdom(user_id)
        if kingdom:
            new_gold = kingdom.get('gold', 0) + question['reward_gold']
            new_xp = kingdom.get('xp', 0) + question['reward_xp']
            db.update_kingdom(user_id, gold=new_gold, xp=new_xp)
        
        await query.edit_message_text(
            f"🧠 <b>QUIZ RESULT</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"✅ <b>Sahi Jawab!</b>\n\n"
            f"🎁 Rewards:\n"
            f"💰 +{question['reward_gold']} Gold\n"
            f"⭐ +{question['reward_xp']} XP\n\n"
            f"⏳ Next quiz: {QUIZ_COOLDOWN_HOURS}h",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🧠 Next Quiz", callback_data="game_quiz")],
                [InlineKeyboardButton("🎲 Games Menu", callback_data="menu_games")],
            ]),
            parse_mode='HTML'
        )
    else:
        correct_letter = ['A', 'B', 'C', 'D'][correct]
        await query.edit_message_text(
            f"🧠 <b>QUIZ RESULT</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"❌ <b>Galat Jawab!</b>\n\n"
            f"Sahi answer: <b>{correct_letter}. {question['options'][correct]}</b>\n\n"
            f"⏳ Next quiz: {QUIZ_COOLDOWN_HOURS}h",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🧠 Try Again", callback_data="game_quiz")],
                [InlineKeyboardButton("🎲 Games Menu", callback_data="menu_games")],
            ]),
            parse_mode='HTML'
        )

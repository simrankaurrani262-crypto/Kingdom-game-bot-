"""
Events handler for Kingdom Conquest.
Decision events, world events, and time-limited events.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import random

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import Database
from config import DECISION_EVENTS, LIMITED_EVENTS
from utils.formatters import format_number
from utils.keyboards import decision_event_keyboard, back_button_keyboard


db = Database()


async def trigger_decision_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger a random decision event for the user."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    
    if not kingdom:
        return
    
    # 10% chance
    if random.random() > 0.10:
        return
    
    event = random.choice(DECISION_EVENTS)
    
    await context.bot.send_message(
        chat_id=user_id,
        text=event['message'],
        reply_markup=decision_event_keyboard(event['id']),
        parse_mode='HTML'
    )


async def handle_event_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle event-related callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data.startswith("decision:"):
        parts = data.split(":")
        event_id = parts[1]
        choice = parts[2]
        await process_decision(update, context, event_id, choice)


async def process_decision(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          event_id: str, choice: str):
    """Process a decision event choice."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        return
    
    # Find event
    event = None
    for e in DECISION_EVENTS:
        if e['id'] == event_id:
            event = e
            break
    
    if not event:
        await query.edit_message_text("❌ Event expired!")
        return
    
    outcome = event['outcomes'].get(choice, {'nothing': True, 'message': 'Kuch nahi hua...'})
    
    # Apply outcome
    result_message = outcome.get('message', 'Done!')
    
    if 'gold' in outcome:
        new_gold = kingdom.get('gold', 0) + outcome['gold']
        db.update_kingdom(user_id, gold=new_gold)
    
    if 'infantry' in outcome:
        army = db.get_army(user_id)
        if army:
            new_inf = army.get('infantry', 0) + outcome['infantry']
            db.update_army(user_id, infantry=new_inf)
    
    # Log decision
    db.conn.cursor().execute('''
        INSERT INTO decision_events (user_id, event_id, choice, outcome)
        VALUES (?, ?, ?, ?)
    ''', (user_id, event_id, choice, result_message))
    db.conn.commit()
    
    await query.edit_message_text(
        f"✅ <b>Decision Made!</b>\n\n"
        f"{result_message}\n\n"
        f"<i>Event complete!</i>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Dashboard", callback_data="back_dashboard")],
        ]),
        parse_mode='HTML'
    )


async def check_world_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check and announce active world events."""
    events = db.get_active_world_events()
    
    if not events:
        return
    
    # Show first active event
    event = events[0]
    
    text = f"""
🌍 <b>WORLD EVENT ACTIVE!</b>
━━━━━━━━━━━━━━

{event.get('message', 'Event active!')}

<i>World events sab players ko affect karte hain!</i>
"""
    
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=text,
        reply_markup=back_button_keyboard("back_dashboard"),
        parse_mode='HTML'
    )


async def spawn_world_event(context: ContextTypes.DEFAULT_TYPE):
    """Spawn a random world event (called by job queue)."""
    if random.random() > 0.3:
        return
    
    event_types = [
        {'type': 'treasure', 'message': '💎 Khazana mila! Sab players +500 Gold!',
         'effect': {'gold': 500}, 'duration': 2},
        {'type': 'plague', 'message': '😷 Plague! Food production -50% for 6 hours!',
         'effect': {'food_multiplier': 0.5}, 'duration': 6},
        {'type': 'festival', 'message': '🎉 Mahotsav! Training speed 2x for 12 hours!',
         'effect': {'training_multiplier': 2.0}, 'duration': 12},
        {'type': 'invasion', 'message': '🐉 Dragon sighted! Survival event active!',
         'effect': {'survival_active': True}, 'duration': 6},
    ]
    
    event = random.choice(event_types)
    
    # Save to database
    db.create_world_event(
        event['type'],
        event['message'],
        event['effect'],
        event['duration']
    )
    
    # Broadcast to all users
    users = db.get_all_users()
    for u in users:
        try:
            await context.bot.send_message(
                chat_id=u['telegram_id'],
                text=f"🌍 <b>WORLD EVENT!</b>\n\n{event['message']}\n\n<i>Event {event['duration']} hours ke liye active hai!</i>",
                parse_mode='HTML'
            )
        except Exception:
            pass


async def check_limited_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check for active limited-time events."""
    # Check if any limited events should be active
    # For now, randomly show if one is "active"
    
    text = """
📅 <b>TIME-LIMITED EVENTS</b>
━━━━━━━━━━━━━━

<i>Currently no active limited events.</i>

<b>Event Types:</b>
💰 Double Gold Weekend - 2x Gold production
🚫 No Walls Day - Wall defense zero
⚔️ Sudden War - 2x XP & Loot from battles

<i>Events randomly activate. Stay tuned!</i>
"""
    
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=text,
        reply_markup=back_button_keyboard("back_dashboard"),
        parse_mode='HTML'
    )

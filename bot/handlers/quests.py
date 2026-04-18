"""
Quest system handler for Kingdom Conquest.
Manages daily quests, milestones, and rewards.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import Database
from utils.formatters import format_number
from utils.keyboards import quest_menu_keyboard, back_button_keyboard


db = Database()


async def handle_quests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /quests command."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    init_quests_if_needed(user_id)
    text = _render_quests_text(user_id, kingdom)
    has_claimable = any(q.get('completed') and not q.get('claimed') for q in db.get_quests(user_id, daily=True))
    await update.message.reply_text(text=text, reply_markup=quest_menu_keyboard(has_claimable), parse_mode='HTML')

def _render_quests_text(user_id: int, kingdom: dict) -> str:
    daily_quests = db.get_quests(user_id, daily=True)
    lines = ["🎯 <b>QUEST BOARD</b>", "━━━━━━━━━━━━━━", "", "📅 <b>DAILY QUESTS</b>"]
    for q in daily_quests:
        progress, target = q.get('progress', 0), q.get('target', 1)
        status = "✅" if q.get('claimed') else ("🎁" if q.get('completed') else "⏳")
        lines.append(f"{status} {q.get('quest_type', 'Unknown')}: {format_number(progress)}/{format_number(target)}")
    lines += ["", "🏆 <b>MILESTONES</b>"]
    for ms in get_milestone_progress(user_id, kingdom):
        lines.append(f"{'✅' if ms['completed'] else '🔒'} {ms['name']}: {ms['progress']}")
    return "\n".join(lines)

async def menu_quests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show quest board (callback version)."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    
    if not kingdom:
        await query.edit_message_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    
    # Initialize quests if needed
    init_quests_if_needed(user_id)
    
    # Get daily quests
    daily_quests = db.get_quests(user_id, daily=True)
    
    lines = ["🎯 <b>QUEST BOARD</b>", "━━━━━━━━━━━━━━", ""]
    lines.append("📅 <b>DAILY QUESTS</b>")
    
    has_claimable = False
    for q in daily_quests:
        progress = q.get('progress', 0)
        target = q.get('target', 1)
        completed = q.get('completed', 0)
        claimed = q.get('claimed', 0)
        
        status = "✅" if claimed else ("🎁" if completed else "⏳")
        if completed and not claimed:
            has_claimable = True
        
        quest_name = q.get('quest_type', 'Unknown')
        lines.append(f"{status} {quest_name}: {format_number(progress)}/{format_number(target)}")
    
    # Milestone quests
    lines.append("")
    lines.append("🏆 <b>MILESTONES</b>")
    
    milestones = get_milestone_progress(user_id, kingdom)
    for ms in milestones:
        status = "✅" if ms['completed'] else "🔒"
        lines.append(f"{status} {ms['name']}: {ms['progress']}")
    
    lines.append("")
    lines.append("━━━━━━━━━━━━━━")
    if has_claimable:
        lines.append("<i>🎁 Claim karne layak rewards hain!</i>")
    
    text = "\n".join(lines)
    
    await query.edit_message_text(
        text=text,
        reply_markup=quest_menu_keyboard(has_claimable),
        parse_mode='HTML'
    )


async def handle_quest_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quest menu callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "menu_quests":
        await menu_quests(update, context)
    elif data == "quest_claim":
        await claim_quest_rewards(update, context)


def init_quests_if_needed(user_id: int):
    """Initialize quests for user if they don't exist."""
    existing = db.get_quests(user_id, daily=True)
    if not existing:
        # Create default daily quests
        default_quests = [
            ('Daily Battler', 'daily_battler', 2),
            ('Resource Collector', 'resource_collector', 5000),
            ('Builder', 'builder', 3),
            ('Army Trainer', 'army_trainer', 50),
            ('Spy Master', 'spy_master', 2),
        ]
        for qtype, qkey, target in default_quests:
            db.create_quest(user_id, qtype, qkey, target, daily=True)


def get_milestone_progress(user_id: int, kingdom: dict) -> list:
    """Get milestone quest progress."""
    milestones = []
    
    # First Blood
    battles_won = kingdom.get('battles_won', 0)
    milestones.append({
        'name': 'First Blood',
        'completed': battles_won >= 1,
        'progress': f"{min(battles_won, 1)}/1 wins",
    })
    
    # War Lord
    milestones.append({
        'name': 'War Lord',
        'completed': battles_won >= 50,
        'progress': f"{min(battles_won, 50)}/50 wins",
    })
    
    # Rich King
    gold = kingdom.get('gold', 0)
    milestones.append({
        'name': 'Rich King',
        'completed': gold >= 100000,
        'progress': f"{format_number(min(gold, 100000))}/100,000 Gold",
    })
    
    # Master Builder
    buildings = db.get_buildings(user_id)
    all_lv10 = all(b.get('level', 0) >= 10 for b in buildings)
    milestones.append({
        'name': 'Master Builder',
        'completed': all_lv10,
        'progress': "All Lv.10+" if all_lv10 else "In Progress",
    })
    
    # Spy Master
    spy_reports = len(db.get_all_kingdoms())  # Simplified
    milestones.append({
        'name': 'Spy Master',
        'completed': spy_reports >= 100,
        'progress': f"100 spy missions",
    })
    
    return milestones


async def claim_quest_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim completed quest rewards."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        return
    
    daily_quests = db.get_quests(user_id, daily=True)
    
    total_gold = 0
    total_xp = 0
    claimed_count = 0
    
    for q in daily_quests:
        if q.get('completed') and not q.get('claimed'):
            # Grant rewards based on quest type
            rewards = get_quest_rewards(q['quest_type'])
            total_gold += rewards.get('gold', 0)
            total_xp += rewards.get('xp', 0)
            claimed_count += 1
            
            # Mark as claimed
            db.update_quest_progress(q['id'], q['progress'])
    
    if claimed_count > 0:
        new_gold = kingdom.get('gold', 0) + total_gold
        new_xp = kingdom.get('xp', 0) + total_xp
        db.update_kingdom(user_id, gold=new_gold, xp=new_xp)
        
        await query.edit_message_text(
            f"🎉 <b>Rewards Claimed!</b>\n\n"
            f"📜 Quests: {claimed_count}\n"
            f"💰 Gold: +{format_number(total_gold)}\n"
            f"⭐ XP: +{total_xp}\n\n"
            f"Shukriya!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Quest Board", callback_data="menu_quests")],
                [InlineKeyboardButton("🏠 Dashboard", callback_data="back_dashboard")],
            ]),
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(
            "❌ <b>No claimable rewards!</b>\n\n"
            "Pehle quests poora karo.",
            reply_markup=back_button_keyboard("menu_quests"),
            parse_mode='HTML'
        )


def get_quest_rewards(quest_type: str) -> dict:
    """Get rewards for a quest type."""
    rewards = {
        'Daily Battler': {'gold': 500, 'xp': 50},
        'Resource Collector': {'gold': 300, 'xp': 30, 'gems': 1},
        'Builder': {'gold': 400, 'xp': 40, 'food': 100},
        'Army Trainer': {'gold': 200, 'xp': 20, 'food': 50},
        'Spy Master': {'gold': 250, 'xp': 25},
    }
    return rewards.get(quest_type, {'gold': 100, 'xp': 10})


async def update_quest_progress(user_id: int, quest_type: str, amount: int = 1):
    """Update quest progress for a user."""
    quests = db.get_quests(user_id, daily=True)
    for q in quests:
        if q['quest_type'] == quest_type and not q.get('completed'):
            new_progress = q.get('progress', 0) + amount
            db.update_quest_progress(q['id'], new_progress)
            break

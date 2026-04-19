"""
Attack handler for Kingdom Conquest.
PvP battles with hero bonuses, wall defense, and alliance support.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import random

from models.database import Database
from services.combat_engine import CombatEngine, calculate_battle_result
from config import ATTACK_ENERGY_COST, ATTACK_GOLD_MIN, MAX_ENERGY
from utils.formatters import format_number
from utils.keyboards import attack_menu_keyboard, back_button_keyboard

db = Database()


async def handle_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /attack command."""
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("❌ Kingdom not found! /start se shuru karo.", parse_mode='HTML')
        return
    if kingdom.get('energy', 0) < ATTACK_ENERGY_COST:
        await update.message.reply_text(
            f"⚡ <b>Not enough energy!</b>\n\nRequired: {ATTACK_ENERGY_COST}\nAvailable: {kingdom.get('energy', 0)}/{MAX_ENERGY}",
            parse_mode='HTML'
        )
        return
    matchmaker = Matchmaker()
    opponent = matchmaker.get_opponent(user_id, kingdom.get('power', 0))
    if not opponent:
        await update.message.reply_text("❌ No opponents found!", parse_mode='HTML')
        return
    await update.message.reply_text(
        text=_format_target_text(kingdom, opponent),
        reply_markup=attack_menu_keyboard(opponent),
        parse_mode='HTML'
    )


def _format_target_text(kingdom: dict, target: dict) -> str:
    return f"""⚔️ <b>ATTACK MENU</b>
━━━━━━━━━━━━━━
👑 <b>Target:</b> {target.get('kingdom_name', 'Unknown')} {target.get('flag', '')}
⚡ <b>Power:</b> {format_number(target.get('power', 0))}
🏆 <b>Level:</b> {target.get('level', 1)}

⚡ <b>Your Energy:</b> {kingdom.get('energy', 0)}/{MAX_ENERGY}
⚔️ <b>Your Power:</b> {format_number(kingdom.get('power', 0))}

<i>Attack se gold loot kar sakte ho!</i>"""


async def menu_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show attack menu (callback version)."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await query.edit_message_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    if kingdom.get('energy', 0) < ATTACK_ENERGY_COST:
        await query.edit_message_text(
            f"⚡ <b>Not enough energy!</b>\n\nRequired: {ATTACK_ENERGY_COST}\nYou have: {kingdom.get('energy', 0)}/{MAX_ENERGY}",
            reply_markup=back_button_keyboard("back_dashboard"),
            parse_mode='HTML'
        )
        return
    from services.matchmaking import Matchmaker
    matchmaker = Matchmaker()
    opponent = matchmaker.get_opponent(user_id, kingdom.get('power', 0))
    if not opponent:
        await query.edit_message_text("❌ No opponents found!", reply_markup=back_button_keyboard("back_dashboard"), parse_mode='HTML')
        return
    await query.edit_message_text(
        text=_format_target_text(kingdom, opponent),
        reply_markup=attack_menu_keyboard(opponent),
        parse_mode='HTML'
    )


async def handle_attack_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle attack-related callbacks."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    if data == "menu_attack":
        await menu_attack(update, context)
    elif data.startswith("attack_start:"):
        target_id = int(data.split(":")[1])
        await start_attack(update, context, target_id)
    elif data == "attack_ranked":
        await show_ranked_targets(update, context)
    elif data.startswith("attack_target:"):
        target_id = int(data.split(":")[1])
        await execute_attack(update, context, target_id)


async def start_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    """Show attack confirmation."""
    query = update.callback_query
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    target = db.get_kingdom(target_id)
    if not kingdom or not target:
        await query.edit_message_text("❌ Target not found!", parse_mode='HTML')
        return
    if kingdom.get('energy', 0) < ATTACK_ENERGY_COST:
        await query.edit_message_text("⚡ Not enough energy!", reply_markup=back_button_keyboard("menu_attack"), parse_mode='HTML')
        return
    text = f"""⚔️ <b>CONFIRM ATTACK</b>
━━━━━━━━━━━━━━
👑 <b>Target:</b> {target.get('kingdom_name', 'Unknown')} {target.get('flag', '')}
⚡ <b>Power:</b> {format_number(target.get('power', 0))}

⚡ <b>Cost:</b> {ATTACK_ENERGY_COST} Energy
⚔️ <b>Your Power:</b> {format_number(kingdom.get('power', 0))}

<i>Sure karein?</i>"""
    keyboard = [
        [InlineKeyboardButton("⚔️ ATTACK!", callback_data=f"attack_target:{target_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_attack")],
    ]
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')


async def show_ranked_targets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show ranked list of targets."""
    query = update.callback_query
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        return
    from services.matchmaking import Matchmaker
    matchmaker = Matchmaker()
    targets = matchmaker.get_ranked_opponents(user_id, kingdom.get('power', 0))
    if not targets:
        await query.edit_message_text("❌ No opponents found!", reply_markup=back_button_keyboard("menu_attack"), parse_mode='HTML')
        return
    lines = ["⚔️ <b>RANKED TARGETS</b>", "━━━━━━━━━━━━━━"]
    keyboard = []
    for t in targets:
        lines.append(f"👑 {t.get('kingdom_name', 'Unknown')} {t.get('flag', '')} — {format_number(t.get('power', 0))} Power")
        keyboard.append([InlineKeyboardButton(f"⚔️ Attack {t.get('kingdom_name', 'Unknown')[:12]}", callback_data=f"attack_start:{t['user_id']}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_attack")])
    await query.edit_message_text(text="\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')


async def execute_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    """Execute the attack."""
    query = update.callback_query
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    target = db.get_kingdom(target_id)
    target_army = db.get_army(target_id)
    attacker_army = db.get_army(user_id)

    if not kingdom or not target or not attacker_army:
        await query.edit_message_text("❌ <b>Error!</b> Data missing.", parse_mode='HTML')
        return

    if kingdom.get('energy', 0) < ATTACK_ENERGY_COST:
        await query.edit_message_text("⚡ <b>Not enough energy!</b>", reply_markup=back_button_keyboard("menu_attack"), parse_mode='HTML')
        return

    # Calculate hero bonuses
    attacker_bonus = await _get_hero_bonus(user_id)
    defender_bonus = await _get_hero_bonus(target_id)

    # Calculate wall defense
    target_buildings = db.get_buildings(target_id)
    wall_level = 0
    for b in target_buildings:
        if b.get('building_type') == 'wall':
            wall_level = b.get('level', 0)
            break
    defender_bonus += CombatEngine.calculate_wall_defense(wall_level)

    # Resolve battle
    attacker_dict = {
        'infantry': attacker_army.get('infantry', 0),
        'archers': attacker_army.get('archers', 0),
        'cavalry': attacker_army.get('cavalry', 0)
    }
    defender_dict = target_army or {'infantry': 0, 'archers': 0, 'cavalry': 0}

    result = calculate_battle_result(attacker_dict, defender_dict, attacker_bonus, defender_bonus)

    # Apply losses
    new_attacker_infantry = max(0, attacker_army.get('infantry', 0) - result['attacker_losses'])
    new_attacker_archers = max(0, attacker_army.get('archers', 0) - result['attacker_losses'] // 3)
    new_attacker_cavalry = max(0, attacker_army.get('cavalry', 0) - result['attacker_losses'] // 5)

    db.update_army(user_id,
        infantry=new_attacker_infantry,
        archers=new_attacker_archers,
        cavalry=new_attacker_cavalry
    )

    # Deduct energy
    new_energy = kingdom.get('energy', 0) - ATTACK_ENERGY_COST
    db.update_kingdom(user_id, energy=new_energy)

    if result['won']:
        # Calculate loot
        loot = CombatEngine.calculate_loot(target.get('gold', 0), result['loot_factor'])
        loot = max(ATTACK_GOLD_MIN, loot)

        new_target_infantry = max(0, target_army.get('infantry', 0) - result['defender_losses'])
        new_target_archers = max(0, target_army.get('archers', 0) - result['defender_losses'] // 3)
        new_target_cavalry = max(0, target_army.get('cavalry', 0) - result['defender_losses'] // 5)

        db.update_army(target_id,
            infantry=new_target_infantry,
            archers=new_target_archers,
            cavalry=new_target_cavalry
        )

        # Transfer gold
        attacker_gold = kingdom.get('gold', 0) + loot
        target_gold = max(0, target.get('gold', 0) - loot)
        damage_taken = result['defender_losses'] * 2

        db.update_kingdom(user_id, gold=attacker_gold, battles_fought=kingdom.get('battles_fought', 0) + 1, battles_won=kingdom.get('battles_won', 0) + 1)
        db.update_kingdom(target_id, gold=target_gold, battles_fought=target.get('battles_fought', 0) + 1, battles_lost=target.get('battles_lost', 0) + 1)

        # Log battle
        db.log_battle(user_id, target_id, 'win', loot, result['attacker_losses'], result['defender_losses'])

        # Power recalculation
        new_power = _calculate_power(db.get_army(user_id))
        db.update_kingdom(user_id, power=new_power)

        summary = f"""🎉 <b>VICTORY!</b>
━━━━━━━━━━━━━━

👑 Target: {target.get('kingdom_name', 'Unknown')} {target.get('flag', '')}
💰 Gold Looted: {format_number(loot)}
💀 Enemy Losses: {result['defender_losses']}
⚔️ Your Losses: {result['attacker_losses']}

⚡ Energy: {new_energy}/{MAX_ENERGY}"""
    else:
        # Attacker loses
        new_target_infantry = max(0, target_army.get('infantry', 0) - result['defender_losses'])
        new_target_archers = max(0, target_army.get('archers', 0) - result['defender_losses'] // 3)
        new_target_cavalry = max(0, target_army.get('cavalry', 0) - result['defender_losses'] // 5)

        db.update_army(target_id,
            infantry=new_target_infantry,
            archers=new_target_archers,
            cavalry=new_target_cavalry
        )

        db.update_kingdom(user_id, battles_fought=kingdom.get('battles_fought', 0) + 1, battles_lost=kingdom.get('battles_lost', 0) + 1)
        db.update_kingdom(target_id, battles_fought=target.get('battles_fought', 0) + 1, battles_won=target.get('battles_won', 0) + 1)
        db.log_battle(user_id, target_id, 'loss', 0, result['attacker_losses'], result['defender_losses'])

        summary = f"""💀 <b>DEFEAT!</b>
━━━━━━━━━━━━━━

👑 {target.get('kingdom_name', 'Unknown')} {target.get('flag', '')} ne aapko hara diya!
💀 Your Losses: {result['attacker_losses']}
⚔️ Enemy Losses: {result['defender_losses']}

⚡ Energy: {new_energy}/{MAX_ENERGY}"""

    await query.edit_message_text(
        text=summary,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚔️ Attack Again", callback_data="menu_attack")],
            [InlineKeyboardButton("🏠 Dashboard", callback_data="back_dashboard")],
        ]),
        parse_mode='HTML'
    )


async def _get_hero_bonus(user_id: int) -> float:
    """Get hero attack/defense bonus for a user."""
    heroes = db.get_heroes(user_id)
    bonus = 0.0
    for hero in heroes:
        if hero.get('is_active'):
            # Each active hero gives 5% bonus
            bonus += 0.05 * hero.get('level', 1)
    return bonus


def _calculate_power(army: dict) -> int:
    """Calculate total power from army."""
    if not army:
        return 0
    return (
        army.get('infantry', 0) * 5 +
        army.get('archers', 0) * 8 +
        army.get('cavalry', 0) * 12
    )


# Matchmaker import at end to avoid circular imports
from services.matchmaking import Matchmaker

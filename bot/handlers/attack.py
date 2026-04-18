"""
Attack system handler for Kingdom Conquest.
PvP attacks, raids, matchmaking, and battle flow with real visuals.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import random
import os

from models.database import Database
from services.combat_engine import BattleEngine
from services.matchmaking import MatchmakingService
from services.energy_service import EnergyService
from services.economy import EconomyService
from services.notification import NotificationService
from utils.formatters import format_number, format_time_remaining
from utils.keyboards import (
    attack_menu_keyboard, opponent_card_keyboard,
    battle_response_keyboard, back_button_keyboard, revenge_keyboard
)
from utils.assets import get_scene_image
from config import (
    ENERGY_COST_ATTACK, RAID_ENERGY_COST, RAID_LOOT_PERCENT,
    RAID_ARMY_LOSS_PERCENT, REVENGE_WINDOW_SECONDS, REVENGE_ATTACK_BONUS
)

db = Database()
matchmaking = MatchmakingService()
energy_service = EnergyService()


async def handle_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    
    if not kingdom:
        await update.message.reply_text("❌ Kingdom not found! /start to begin.", parse_mode='HTML')
        return
    
    energy = energy_service.calculate_current_energy(
        kingdom.get('energy', 10),
        kingdom.get('last_energy_regen')
    )
    
    text = f"""
⚔️ <b>ATTACK MODE</b>
━━━━━━━━━━━━━━

⚡ <b>Energy:</b> {energy}/10

<b>Options:</b>
🎯 <b>Find Opponent</b> - Fair matchmaking
🔥 <b>Revenge</b> - Attack your enemies
🗺 <b>Map Select</b> - Choose from map
🏃 <b>Quick Raid</b> - Fast loot (less risk)

<i>Each attack costs 1 energy.
Attacking breaks your shield!</i>
"""
    
    battle_img = get_scene_image('battle')
    if battle_img and os.path.isfile(battle_img):
        await update.message.reply_photo(
            photo=open(battle_img, 'rb'),
            caption=text,
            reply_markup=attack_menu_keyboard(),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(text=text, reply_markup=attack_menu_keyboard(), parse_mode='HTML')


async def menu_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    
    if not kingdom:
        await query.edit_message_text("❌ Kingdom not found!", parse_mode='HTML')
        return
    
    energy = energy_service.calculate_current_energy(
        kingdom.get('energy', 10),
        kingdom.get('last_energy_regen')
    )
    
    text = f"""
⚔️ <b>ATTACK MODE</b>
━━━━━━━━━━━━━━

⚡ <b>Energy:</b> {energy}/10

<b>Options:</b>
🎯 <b>Find Opponent</b> - Fair matchmaking
🔥 <b>Revenge</b> - Attack your enemies
🗺 <b>Map Select</b> - Choose from map
🏃 <b>Quick Raid</b> - Fast loot (less risk)

<i>Each attack costs 1 energy.
Attacking breaks your shield!</i>
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=attack_menu_keyboard(),
        parse_mode='HTML'
    )


async def handle_attack_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "menu_attack":
        await menu_attack(update, context)
    elif data == "attack_find":
        await find_opponent(update, context)
    elif data == "attack_next":
        await find_next_opponent(update, context)
    elif data == "attack_revenge":
        await show_revenge_options(update, context)
    elif data == "attack_map":
        from .map_system import menu_map
        await menu_map(update, context)
    elif data == "attack_raid":
        await show_raid_options(update, context)
    elif data.startswith("attack_start:"):
        target_id = int(data.split(":")[1])
        await initiate_attack(update, context, target_id)
    elif data.startswith("battle_accept:"):
        await query.edit_message_text("⚔️ <b>BATTLE ACCEPTED!</b>\n\nBattle starting...", parse_mode='HTML')
    elif data.startswith("battle_decline:"):
        await query.edit_message_text(
            "❌ <b>Battle Declined.</b>",
            reply_markup=back_button_keyboard("menu_attack"),
            parse_mode='HTML'
        )
    elif data.startswith("revenge_attack:"):
        attacker_id = int(data.split(":")[1])
        await execute_revenge(update, context, attacker_id)
    elif data.startswith("raid_execute:"):
        target_id = int(data.split(":")[1])
        await execute_raid(update, context, target_id)


async def find_opponent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        return
    
    energy = energy_service.calculate_current_energy(
        kingdom.get('energy', 10),
        kingdom.get('last_energy_regen')
    )
    if energy < ENERGY_COST_ATTACK:
        await query.edit_message_text(
            "❌ <b>Not enough energy!</b>\n\n1 energy needed for attack.\nEnergy regenerates every 30 min.",
            reply_markup=back_button_keyboard("menu_attack"),
            parse_mode='HTML'
        )
        return
    
    opponents = matchmaking.find_opponents(user_id, count=3)
    if not opponents:
        opponents = [matchmaking.get_dummy_opponent()]
    
    context.user_data['opponents'] = opponents
    context.user_data['current_opponent_idx'] = 0
    
    await show_opponent(update, context, opponents[0], 0, len(opponents))


async def find_next_opponent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    opponents = context.user_data.get('opponents', [])
    if not opponents:
        await find_opponent(update, context)
        return
    
    idx = context.user_data.get('current_opponent_idx', 0) + 1
    if idx >= len(opponents):
        idx = 0
    context.user_data['current_opponent_idx'] = idx
    
    await show_opponent(update, context, opponents[idx], idx, len(opponents))


async def show_opponent(update: Update, context: ContextTypes.DEFAULT_TYPE,
                       opponent: dict, idx: int, total: int):
    query = update.callback_query
    
    text = f"""
⚔️ <b>OPPONENT FOUND</b> ({idx+1}/{total})
━━━━━━━━━━━━━━

👑 <b>Kingdom:</b> {opponent.get('kingdom_name', 'Unknown')} {opponent.get('flag', '')}
🏆 <b>Level:</b> {opponent.get('level', 1)}
⚔️ <b>Army:</b> ~{opponent.get('power', 0) // 10} (estimated)
🛡 <b>Defense:</b> {opponent.get('defense_rating', 'Unknown')}
📍 <b>Distance:</b> {opponent.get('distance', 0)} tiles

<i>Attack costs 1 energy and breaks shield.</i>
"""
    
    target_id = opponent.get('user_id', 0)
    keyboard = [
        [InlineKeyboardButton("⚔️ Attack", callback_data=f"attack_start:{target_id}"),
         InlineKeyboardButton("🕵️ Spy", callback_data=f"spy_target:{target_id}")],
        [InlineKeyboardButton("⏭️ Next", callback_data="attack_next"),
         InlineKeyboardButton("🔙 Back", callback_data="menu_attack")],
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def initiate_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    query = update.callback_query
    user_id = update.effective_user.id
    
    attacker = db.get_kingdom(user_id)
    if not attacker:
        return
    
    energy = energy_service.calculate_current_energy(
        attacker.get('energy', 10),
        attacker.get('last_energy_regen')
    )
    if energy < ENERGY_COST_ATTACK:
        await query.edit_message_text(
            "❌ Not enough energy!",
            reply_markup=back_button_keyboard("menu_attack"),
            parse_mode='HTML'
        )
        return
    
    if target_id == 0:
        await execute_tutorial_battle(update, context)
        return
    
    defender = db.get_kingdom(target_id)
    if not defender:
        await query.edit_message_text("❌ Opponent not found!", reply_markup=back_button_keyboard("menu_attack"), parse_mode='HTML')
        return
    
    shield = defender.get('shield_expires')
    if shield:
        if isinstance(shield, str):
            shield = datetime.fromisoformat(shield.replace('Z', '+00:00'))
        if shield > datetime.now():
            await query.edit_message_text(
                "🛡 <b>Opponent has shield!</b>\n\nCannot attack. Try later.",
                reply_markup=back_button_keyboard("menu_attack"),
                parse_mode='HTML'
            )
            return
    
    await execute_battle(update, context, user_id, target_id)


async def execute_battle(update: Update, context: ContextTypes.DEFAULT_TYPE,
                        attacker_id: int, defender_id: int, is_revenge: bool = False):
    query = update.callback_query
    
    attacker = db.get_kingdom(attacker_id)
    defender = db.get_kingdom(defender_id)
    attacker_army = db.get_army(attacker_id)
    defender_army = db.get_army(defender_id)
    attacker_heroes = db.get_heroes(attacker_id)
    defender_heroes = db.get_heroes(defender_id)
    
    if not all([attacker, defender, attacker_army, defender_army]):
        await query.edit_message_text("❌ Battle error!", parse_mode='HTML')
        return
    
    revenge_bonus = REVENGE_ATTACK_BONUS if is_revenge else 0.0
    engine = BattleEngine(attacker, defender, attacker_army, defender_army,
                          attacker_heroes, defender_heroes, revenge_bonus)
    
    report = engine.simulate_battle()
    await apply_battle_results(attacker_id, defender_id, report)
    
    # Send battle report with battle scene image
    battle_img = get_scene_image('battle')
    
    if battle_img and os.path.isfile(battle_img):
        try:
            await query.message.reply_photo(
                photo=open(battle_img, 'rb'),
                caption=report['message'],
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Attack Menu", callback_data="menu_attack")],
                    [InlineKeyboardButton("🏠 Dashboard", callback_data="back_dashboard")],
                ]),
                parse_mode='HTML'
            )
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            await query.edit_message_text(
                text=report['message'],
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Attack Menu", callback_data="menu_attack")],
                    [InlineKeyboardButton("🏠 Dashboard", callback_data="back_dashboard")],
                ]),
                parse_mode='HTML'
            )
    else:
        await query.edit_message_text(
            text=report['message'],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Attack Menu", callback_data="menu_attack")],
                [InlineKeyboardButton("🏠 Dashboard", callback_data="back_dashboard")],
            ]),
            parse_mode='HTML'
        )
    
    # Notify defender
    try:
        if context.bot:
            await context.bot.send_message(
                chat_id=defender_id,
                text=f"⚔️ <b>YOU WERE ATTACKED!</b>\n\n"
                     f"{attacker.get('kingdom_name', 'Unknown')} attacked you!\n\n"
                     f"{report['message'][:300]}...",
                parse_mode='HTML'
            )
    except Exception:
        pass


async def apply_battle_results(attacker_id: int, defender_id: int, report: dict):
    attacker = db.get_kingdom(attacker_id)
    defender = db.get_kingdom(defender_id)
    
    if not attacker or not defender:
        return
    
    a_army = db.get_army(attacker_id)
    if a_army:
        new_inf = max(0, a_army.get('infantry', 0) - report['attacker_losses'].get('infantry', 0))
        new_arc = max(0, a_army.get('archers', 0) - report['attacker_losses'].get('archers', 0))
        new_cav = max(0, a_army.get('cavalry', 0) - report['attacker_losses'].get('cavalry', 0))
        db.update_army(attacker_id, infantry=new_inf, archers=new_arc, cavalry=new_cav)
    
    d_army = db.get_army(defender_id)
    if d_army:
        new_inf = max(0, d_army.get('infantry', 0) - report['defender_losses'].get('infantry', 0))
        new_arc = max(0, d_army.get('archers', 0) - report['defender_losses'].get('archers', 0))
        new_cav = max(0, d_army.get('cavalry', 0) - report['defender_losses'].get('cavalry', 0))
        db.update_army(defender_id, infantry=new_inf, archers=new_arc, cavalry=new_cav)
    
    if report['winner'] == 'attacker':
        gold_loot = report['gold_loot']
        new_att_gold = attacker.get('gold', 0) + gold_loot
        new_def_gold = max(0, defender.get('gold', 0) - gold_loot)
        new_xp = attacker.get('xp', 0) + report['xp_gain']
        new_wins = attacker.get('battles_won', 0) + 1
        new_fought = attacker.get('battles_fought', 0) + 1
        def_fought = defender.get('battles_fought', 0) + 1
        def_losses = defender.get('battles_lost', 0) + 1
        
        db.update_kingdom(
            attacker_id, gold=new_att_gold, xp=new_xp,
            battles_won=new_wins, battles_fought=new_fought,
            energy=attacker.get('energy', 10) - 1,
            shield_expires=datetime.now()
        )
        db.update_kingdom(
            defender_id, gold=new_def_gold,
            battles_fought=def_fought, battles_lost=def_losses,
        )
        
        expires = datetime.now() + timedelta(seconds=REVENGE_WINDOW_SECONDS)
        db.create_revenge_opportunity(defender_id, attacker_id, expires)
        
        if random.random() < 0.3:
            building_types = ['gold_mine', 'farm', 'barracks']
            damaged = random.choice(building_types)
            building = db.get_building(defender_id, damaged)
            if building and building['level'] > 1:
                db.update_building(defender_id, damaged, level=building['level'] - 1)
    else:
        new_xp = defender.get('xp', 0) + report['xp_gain']
        att_xp = attacker.get('xp', 0) + 25
        
        db.update_kingdom(
            attacker_id, xp=att_xp,
            battles_fought=attacker.get('battles_fought', 0) + 1,
            energy=attacker.get('energy', 10) - 1,
            shield_expires=datetime.now()
        )
        db.update_kingdom(defender_id, xp=new_xp)
    
    db.save_battle(
        attacker_id, defender_id, report['winner'],
        report['gold_loot'], report['xp_gain'],
        report['attacker_losses'], report['defender_losses'],
        report['rounds'], report['message']
    )
    
    if report['winner'] == 'attacker':
        total_wins = db.get_kingdom(attacker_id).get('battles_won', 0)
        if total_wins == 1:
            db.unlock_achievement(attacker_id, 'first_blood')


async def execute_tutorial_battle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        return
    
    report = {
        'message': f"""
⚔️ <b>BATTLE REPORT</b>
━━━━━━━━━━━━━━
🏆 <b>VICTORY!</b>

⚔️ ATTACKER: {kingdom.get('kingdom_name', 'You')} {kingdom.get('flag', '')}
🛡 DEFENDER: Training Dummy 🎯

⚔️ Rounds:
Round 1 → 🗡 Infantry charges! ⚔️
   💥 Damage: 150
   ⚔️ ATK HP: 500 | 🛡 DEF HP: 0

💀 Losses:
Attacker: 🗡-0 🏹-0 🐎-0
Defender: 🗡-50 🏹-0 🐎-0

🏆 Rewards:
💰 +500 Gold
⭐ +50 XP
━━━━━━━━━━━━━━
""",
        'winner': 'attacker', 'gold_loot': 500, 'xp_gain': 50,
        'rounds': [{'round': 1, 'action': 'Infantry charges!', 'damage': 150,
                     'attacker_remaining': 500, 'defender_remaining': 0}],
        'attacker_losses': {'infantry': 0, 'archers': 0, 'cavalry': 0},
        'defender_losses': {'infantry': 50, 'archers': 0, 'cavalry': 0},
    }
    
    new_gold = kingdom.get('gold', 0) + 500
    new_xp = kingdom.get('xp', 0) + 50
    
    db.update_kingdom(user_id, gold=new_gold, xp=new_xp,
                      battles_won=1, battles_fought=1,
                      energy=kingdom.get('energy', 10) - 1,
                      tutorial_step=3)
    
    db.unlock_achievement(user_id, 'first_blood')
    
    battle_img = get_scene_image('battle')
    if battle_img and os.path.isfile(battle_img):
        try:
            await query.message.reply_photo(
                photo=open(battle_img, 'rb'),
                caption=report['message'],
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎉 Complete Tutorial!", callback_data="tutorial_done")],
                ]),
                parse_mode='HTML'
            )
            await query.edit_message_reply_markup(reply_markup=None)
            return
        except Exception:
            pass
    
    await query.edit_message_text(
        text=report['message'],
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎉 Complete Tutorial!", callback_data="tutorial_done")],
        ]),
        parse_mode='HTML'
    )


async def show_revenge_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    opportunities = db.get_revenge_opportunities(user_id)
    
    if not opportunities:
        await query.edit_message_text(
            "🔥 <b>NO REVENGE AVAILABLE</b>\n\nNo recent attacks on you.\nWhen someone attacks, it will appear here!",
            reply_markup=back_button_keyboard("menu_attack"),
            parse_mode='HTML'
        )
        return
    
    lines = ["🔥 <b>REVENGE OPPORTUNITIES</b>", "━━━━━━━━━━━━━━"]
    keyboard = []
    
    for opp in opportunities:
        attacker = db.get_kingdom(opp['attacker_id'])
        if attacker:
            expires = opp.get('expires_at')
            if isinstance(expires, str):
                expires = datetime.fromisoformat(expires.replace('Z', '+00:00'))
            time_left = format_time_remaining(expires)
            lines.append(f"👑 {attacker.get('kingdom_name', 'Unknown')} {attacker.get('flag', '')}\n   ⏳ {time_left} remaining")
            keyboard.append([InlineKeyboardButton(f"🔥 Revenge {attacker.get('kingdom_name', '')}", callback_data=f"revenge_attack:{opp['attacker_id']}")])
    
    lines.append("━━━━━━━━━━━━━━")
    lines.append("<i>Revenge gives +10% attack bonus!</i>")
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_attack")])
    
    await query.edit_message_text(
        text="\n".join(lines),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def execute_revenge(update: Update, context: ContextTypes.DEFAULT_TYPE, attacker_id: int):
    query = update.callback_query
    user_id = update.effective_user.id
    
    opportunities = db.get_revenge_opportunities(user_id)
    revenge_opp = None
    for opp in opportunities:
        if opp['attacker_id'] == attacker_id:
            revenge_opp = opp
            break
    
    if not revenge_opp:
        await query.edit_message_text(
            "❌ <b>Revenge expired!</b>\n\nThe 1-hour window has passed.",
            reply_markup=back_button_keyboard("menu_attack"),
            parse_mode='HTML'
        )
        return
    
    db.use_revenge(revenge_opp['id'])
    await execute_battle(update, context, user_id, attacker_id, is_revenge=True)


async def show_raid_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        return
    
    energy = energy_service.calculate_current_energy(
        kingdom.get('energy', 10),
        kingdom.get('last_energy_regen')
    )
    
    if energy < RAID_ENERGY_COST:
        await query.edit_message_text(
            "❌ Not enough energy! Raid needs 1 energy.",
            reply_markup=back_button_keyboard("menu_attack"),
            parse_mode='HTML'
        )
        return
    
    opponents = matchmaking.find_opponents(user_id, count=3)
    if not opponents:
        await query.edit_message_text(
            "❌ No raid targets available!",
            reply_markup=back_button_keyboard("menu_attack"),
            parse_mode='HTML'
        )
        return
    
    lines = ["🏃 <b>RAID TARGETS</b>", "━━━━━━━━━━━━━━"]
    keyboard = []
    
    for opp in opponents:
        lines.append(f"👑 {opp.get('kingdom_name', 'Unknown')} {opp.get('flag', '')}\n   Level: {opp.get('level', 1)} | Distance: {opp.get('distance', 0)}")
        keyboard.append([InlineKeyboardButton(f"🏃 Raid {opp.get('kingdom_name', '')}", callback_data=f"raid_execute:{opp['user_id']}")])
    
    lines.append(f"\n<i>Raid gives {int(RAID_LOOT_PERCENT*100)}% loot, lower risk!</i>")
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_attack")])
    
    await query.edit_message_text(
        text="\n".join(lines),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def execute_raid(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    query = update.callback_query
    user_id = update.effective_user.id
    
    kingdom = db.get_kingdom(user_id)
    defender = db.get_kingdom(target_id)
    
    if not kingdom or not defender:
        return
    
    # Simple raid calculation
    loot = int(defender.get('gold', 0) * RAID_LOOT_PERCENT)
    loss_rate = RAID_ARMY_LOSS_PERCENT
    
    army = db.get_army(user_id)
    if army:
        new_inf = max(0, int(army.get('infantry', 0) * (1 - loss_rate)))
        new_arc = max(0, int(army.get('archers', 0) * (1 - loss_rate)))
        new_cav = max(0, int(army.get('cavalry', 0) * (1 - loss_rate)))
        db.update_army(user_id, infantry=new_inf, archers=new_arc, cavalry=new_cav)
    
    new_gold = kingdom.get('gold', 0) + loot
    db.update_kingdom(user_id, gold=new_gold, energy=kingdom.get('energy', 10) - 1)
    
    text = f"""
🏃 <b>RAID COMPLETE!</b>
━━━━━━━━━━━━━━

👑 Target: {defender.get('kingdom_name', 'Unknown')} {defender.get('flag', '')}

💰 <b>Loot:</b> +{format_number(loot)} Gold
⚔️ <b>Army Loss:</b> {int(loss_rate * 100)}%

<i>Quick and stealthy!</i>
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏃 Another Raid", callback_data="attack_raid")],
            [InlineKeyboardButton("🔙 Attack Menu", callback_data="menu_attack")],
        ]),
        parse_mode='HTML'
    )

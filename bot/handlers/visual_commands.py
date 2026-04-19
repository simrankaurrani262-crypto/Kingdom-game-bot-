"""
Visual Commands Handler for Kingdom Conquest Bot.
Provides commands for animations, dynamic cards, and rich visual content.

Commands:
- /animate_battle - Battle animation GIF
- /hero_card - Hero stat card image
- /kingdom_banner - Kingdom banner image
- /battle_report - Visual battle report
- /spy_report - Visual spy report
- /compare - Compare with another player
- /achievements - Achievement progress chart
- /leaderboard_chart - Visual leaderboard
- /spin - Animated spin wheel
- /notify_test - Test notification card
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import Database
from services.visual_reporter import get_visual_reporter
from services.analytics import get_analytics
from utils.formatters import format_number

db = Database()
reporter = get_visual_reporter()
analytics = get_analytics()


# ====================================================================
# ANIMATION COMMANDS
# ====================================================================

async def handler_animate_battle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /animate_battle - Generate battle animation GIF.
    Usage: /animate_battle [defender_name] [result]
    """
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("Create your kingdom first! Use /start")
        return

    args = context.args
    defender_name = args[0] if args else "Enemy"
    result = args[1] if len(args) > 1 else "victory"

    kingdom_name = kingdom.get('name', 'Attacker')
    army = db.get_army(user_id)
    total_army = sum(army.values())

    # Generate loading effect
    loading_msg = await update.message.reply_text("Rendering battle animation...")

    try:
        filepath = reporter.generate_battle_animation(
            attacker_name=kingdom_name,
            defender_name=defender_name,
            attacker_army=total_army,
            defender_army=max(total_army // 2, 50),
            result=result
        )

        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_animation(
                    animation=f,
                    caption=f"Battle: {kingdom_name} vs {defender_name}"
                )
            await loading_msg.delete()
        else:
            await loading_msg.edit_text(
                "Animation engine not available. Install PIL:\n<code>pip install Pillow numpy</code>",
                parse_mode='HTML'
            )
    except Exception as e:
        await loading_msg.edit_text(f"Animation error: {str(e)[:200]}")


async def handler_levelup_animation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /levelup_anim - Show level-up celebration animation.
    Usage: /levelup_anim [entity_name] [type] [old_level] [new_level]
    """
    args = context.args
    entity_name = args[0] if args else "Town Hall"
    entity_type = args[1] if len(args) > 1 else "building"
    old_level = int(args[2]) if len(args) > 2 else 1
    new_level = int(args[3]) if len(args) > 3 else 2

    loading_msg = await update.message.reply_text("Rendering level-up animation...")

    try:
        filepath = reporter.generate_levelup_animation(entity_name, entity_type, old_level, new_level)
        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_animation(
                    animation=f,
                    caption=f"{entity_name} leveled up! Lv.{old_level} -> Lv.{new_level}"
                )
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("Animation engine requires Pillow and numpy.")
    except Exception as e:
        await loading_msg.edit_text(f"Error: {str(e)[:200]}")


async def handler_reward_animation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /reward_anim - Show reward collection animation.
    Usage: /reward_anim [type] [amount] [bonus_text]
    """
    args = context.args
    reward_type = args[0] if args else "gold"
    amount = int(args[1]) if len(args) > 1 else 1000
    bonus_text = " ".join(args[2:]) if len(args) > 2 else ""

    loading_msg = await update.message.reply_text("Rendering reward animation...")

    try:
        filepath = reporter.generate_reward_animation(reward_type, amount, bonus_text)
        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_animation(
                    animation=f,
                    caption=f"+{format_number(amount)} {reward_type.title()}!"
                )
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("Animation engine requires Pillow and numpy.")
    except Exception as e:
        await loading_msg.edit_text(f"Error: {str(e)[:200]}")


async def handler_training_animation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /train_anim - Show army training animation.
    Usage: /train_anim [unit_type] [count]
    """
    args = context.args
    unit_type = args[0] if args else "infantry"
    count = int(args[1]) if len(args) > 1 else 100

    loading_msg = await update.message.reply_text("Rendering training animation...")

    try:
        filepath = reporter.generate_training_animation(unit_type, count)
        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_animation(
                    animation=f,
                    caption=f"Training {count} {unit_type}..."
                )
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("Animation engine requires Pillow and numpy.")
    except Exception as e:
        await loading_msg.edit_text(f"Error: {str(e)[:200]}")


async def handler_achievement_animation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /achievement_anim - Show achievement unlock animation.
    Usage: /achievement_anim [name] [rarity]
    """
    args = context.args
    achievement_name = " ".join(args[:-1]) if len(args) > 1 else "First Victory"
    rarity = args[-1] if args and args[-1] in ['common', 'rare', 'epic', 'legendary'] else 'common'

    loading_msg = await update.message.reply_text("Rendering achievement animation...")

    try:
        filepath = reporter.generate_achievement_unlock_animation(achievement_name, rarity)
        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_animation(
                    animation=f,
                    caption=f"Achievement Unlocked: {achievement_name} [{rarity.upper()}]"
                )
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("Animation engine requires Pillow and numpy.")
    except Exception as e:
        await loading_msg.edit_text(f"Error: {str(e)[:200]}")


# ====================================================================
# IMAGE CARD COMMANDS
# ====================================================================

async def handler_hero_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /hero_card - Generate hero stat card.
    Usage: /hero_card [hero_name]
    """
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("Create your kingdom first! Use /start")
        return

    args = context.args
    hero_name = args[0] if args else "Sir Aldric"

    # Get hero from database or use defaults
    heroes = db.get_heroes(user_id)
    hero = None
    for h in heroes:
        if h.get('name', '').lower() == hero_name.lower():
            hero = h
            break

    if not hero:
        await update.message.reply_text(f"Hero '{hero_name}' not found. Check /heroes")
        return

    loading_msg = await update.message.reply_text("Generating hero card...")

    try:
        stats = {
            'attack': hero.get('attack', 75),
            'defense': hero.get('defense', 60),
            'hp': hero.get('hp', 1000),
            'speed': hero.get('speed', 50)
        }
        skill_tree = hero.get('skills', {'attack': 2, 'defense': 1, 'economy': 0})
        level = hero.get('level', 1)
        rarity = hero.get('rarity', 'common')
        exp = hero.get('experience', 0)
        exp_next = level * 100
        title = hero.get('title', 'Warrior')
        image_path = f"bot/assets/hero_{hero_name.lower().replace(' ', '_')}.png"

        filepath = reporter.generate_hero_card(
            hero_name=hero.get('name', hero_name),
            hero_title=title,
            level=level,
            rarity=rarity,
            stats=stats,
            skill_tree=skill_tree,
            experience=exp,
            exp_to_next=exp_next,
            image_path=image_path if os.path.exists(image_path) else None
        )

        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_photo(photo=f, caption=f"Hero Card - {hero_name}")
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("Image renderer requires Pillow.")
    except Exception as e:
        await loading_msg.edit_text(f"Error: {str(e)[:200]}")


async def handler_kingdom_banner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /kingdom_banner - Generate kingdom banner image.
    """
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("Create your kingdom first! Use /start")
        return

    loading_msg = await update.message.reply_text("Generating kingdom banner...")

    try:
        army = db.get_army(user_id)
        buildings = db.get_buildings(user_id)
        heroes = db.get_heroes(user_id)

        total_army = sum(army.values())
        total_building_level = sum(b.get('level', 0) for b in buildings)
        power = (total_army * 10) + total_building_level * 50

        filepath = reporter.generate_kingdom_banner(
            kingdom_name=kingdom.get('name', 'Unknown'),
            king_name=kingdom.get('king_name', 'Unknown'),
            flag_emoji=kingdom.get('flag', ''),
            power=power,
            gold=kingdom.get('gold', 0),
            food=kingdom.get('food', 0),
            army=total_army,
            buildings=total_building_level,
            wins=kingdom.get('wins', 0),
            rank=kingdom.get('rank', 99)
        )

        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_photo(photo=f, caption=kingdom.get('name', 'Kingdom Banner'))
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("Image renderer requires Pillow.")
    except Exception as e:
        await loading_msg.edit_text(f"Error: {str(e)[:200]}")


async def handler_battle_report_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /battle_report - Generate visual battle report card.
    Usage: /battle_report [defender_name] [result]
    """
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("Create your kingdom first! Use /start")
        return

    args = context.args
    defender_name = args[0] if args else "Enemy"
    result = args[1] if len(args) > 1 else "victory"

    loading_msg = await update.message.reply_text("Generating battle report...")

    try:
        # Simulate battle data
        army = db.get_army(user_id)
        attacker_losses = {
            'infantry': max(0, army.get('infantry', 0) // 10),
            'archers': max(0, army.get('archers', 0) // 15),
            'cavalry': max(0, army.get('cavalry', 0) // 20)
        }
        defender_losses = {
            'infantry': attacker_losses['infantry'] * 2,
            'archers': attacker_losses['archers'] * 2,
            'cavalry': attacker_losses['cavalry'] * 2
        }

        filepath = reporter.generate_battle_report_card(
            attacker_name=kingdom.get('name', 'Attacker'),
            defender_name=defender_name,
            attacker_losses=attacker_losses,
            defender_losses=defender_losses,
            loot_gold=500,
            loot_food=300,
            result=result,
            battle_rounds=5,
            total_damage=2000
        )

        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_photo(photo=f, caption=f"Battle Report: {result.upper()}")
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("Image renderer requires Pillow.")
    except Exception as e:
        await loading_msg.edit_text(f"Error: {str(e)[:200]}")


async def handler_spy_report_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /spy_report_card - Generate visual spy report.
    Usage: /spy_report_card [target_name] [intel_level]
    """
    args = context.args
    target_name = args[0] if args else "Enemy"
    intel_level = args[1] if len(args) > 1 else "detailed"

    loading_msg = await update.message.reply_text("Generating spy report...")

    try:
        filepath = reporter.generate_spy_report_card(
            target_name=target_name,
            intel_level=intel_level,
            resources={'gold': 50000, 'food': 30000},
            army={'infantry': 500, 'archers': 300, 'cavalry': 200},
            buildings={'town_hall': 10, 'gold_mine': 8, 'farm': 7, 'barracks': 9, 'wall': 5},
            defense_rating=650,
            risk_level='medium'
        )

        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_photo(photo=f, caption=f"Spy Report: {target_name}")
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("Image renderer requires Pillow.")
    except Exception as e:
        await loading_msg.edit_text(f"Error: {str(e)[:200]}")


# ====================================================================
# COMPARISON & LEADERBOARD COMMANDS
# ====================================================================

async def handler_compare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /compare - Compare with another player.
    Usage: /compare [player_name or @username]
    """
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("Create your kingdom first! Use /start")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: /compare [player_name]")
        return

    target_name = " ".join(args)

    loading_msg = await update.message.reply_text(f"Comparing with {target_name}...")

    try:
        # Get comparison data from database
        # In real implementation, lookup player by name
        kingdom_name = kingdom.get('name', 'You')

        filepath = reporter.generate_comparison_report(
            player1_name=kingdom_name,
            player1_id=user_id,
            player2_name=target_name,
            player2_id=0  # Would lookup real ID
        )

        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_photo(
                    photo=f,
                    caption=f"Comparison: {kingdom_name} vs {target_name}"
                )
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("Comparison requires matplotlib.")
    except Exception as e:
        await loading_msg.edit_text(f"Error: {str(e)[:200]}")


async def handler_achievements_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /achievements_chart - Show achievement progress chart.
    """
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    if not kingdom:
        await update.message.reply_text("Create your kingdom first! Use /start")
        return

    kingdom_name = kingdom.get('name', 'Unknown')

    # Default achievements config
    achievements_config = [
        {'name': 'First Blood', 'type': 'kills', 'target': 1},
        {'name': 'Warrior', 'type': 'kills', 'target': 10},
        {'name': 'Conqueror', 'type': 'kills', 'target': 50},
        {'name': 'Treasure Hunter', 'type': 'loot', 'target': 100000},
        {'name': 'Loyal', 'type': 'streak', 'target': 7},
    ]

    loading_msg = await update.message.reply_text("Generating achievement chart...")

    try:
        filepath = reporter.generate_achievement_report(user_id, achievements_config, kingdom_name)
        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_photo(
                    photo=f,
                    caption=f"Achievement Progress - {kingdom_name}"
                )
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("Achievement chart requires matplotlib.")
    except Exception as e:
        await loading_msg.edit_text(f"Error: {str(e)[:200]}")


async def handler_leaderboard_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /leaderboard_chart - Show visual leaderboard.
    """
    loading_msg = await update.message.reply_text("Generating leaderboard...")

    try:
        # Sample data - in real implementation, fetch from database
        players = [
            {'name': 'Player1', 'power': 15000, 'gold': 500000, 'wins': 120, 'alliance': 'Dragons'},
            {'name': 'Player2', 'power': 12000, 'gold': 400000, 'wins': 95, 'alliance': 'Wolves'},
            {'name': 'Player3', 'power': 10000, 'gold': 350000, 'wins': 80, 'alliance': 'Eagles'},
            {'name': 'Player4', 'power': 8500, 'gold': 300000, 'wins': 70, 'alliance': 'Bears'},
            {'name': 'Player5', 'power': 7000, 'gold': 250000, 'wins': 55, 'alliance': 'Lions'},
        ]

        filepath = reporter.generate_leaderboard_visual(players, 'power', 'Top Players by Power')
        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_photo(photo=f, caption="Leaderboard - Top Players")
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("Leaderboard chart requires matplotlib.")
    except Exception as e:
        await loading_msg.edit_text(f"Error: {str(e)[:200]}")


async def handler_leaderboard_podium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /podium - Show top 3 leaderboard podium.
    """
    loading_msg = await update.message.reply_text("Generating podium...")

    try:
        players = [
            {'name': 'Champion1', 'power': 20000, 'alliance': 'Dragons'},
            {'name': 'RunnerUp2', 'power': 16000, 'alliance': 'Wolves'},
            {'name': 'Third3', 'power': 12000, 'alliance': 'Eagles'},
        ]

        filepath = reporter.generate_leaderboard_podium_card(players, 'power')
        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_photo(photo=f, caption="Top 3 Champions!")
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("Podium renderer requires Pillow.")
    except Exception as e:
        await loading_msg.edit_text(f"Error: {str(e)[:200]}")


# ====================================================================
# UTILITY COMMANDS
# ====================================================================

async def handler_spin_wheel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /spin - Animated lucky spin wheel.
    """
    items = ["1000 Gold", "500 Food", "50 Gems", "Epic Chest", "10 Energy", "Shield", "XP Boost", "Nothing"]
    win_index = 0  # Would be random in real implementation

    loading_msg = await update.message.reply_text("Spinning the wheel...")

    try:
        filepath = reporter.generate_spin_animation(items, win_index)
        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_animation(
                    animation=f,
                    caption=f"You won: {items[win_index]}!"
                )
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("Spin animation requires Pillow and numpy.")
    except Exception as e:
        await loading_msg.edit_text(f"Error: {str(e)[:200]}")


async def handler_notification_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /notify_test - Test notification card.
    Usage: /notify_test [type] [title] [message]
    """
    args = context.args
    notif_type = args[0] if args else "info"
    title = args[1] if len(args) > 1 else "Test Notification"
    message = " ".join(args[2:]) if len(args) > 2 else "This is a test notification card."

    loading_msg = await update.message.reply_text("Generating notification...")

    try:
        filepath = reporter.generate_notification_card(title, message, notif_type, "View Details")
        if filepath and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                await update.message.reply_photo(photo=f, caption=f"Notification: {title}")
            await loading_msg.delete()
        else:
            await loading_msg.edit_text("Notification renderer requires Pillow.")
    except Exception as e:
        await loading_msg.edit_text(f"Error: {str(e)[:200]}")


async def handler_visual_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /visual_help - Show all visual commands.
    """
    help_text = """
<b>Visual & Animation Commands</b>

<u>Charts & Graphs</u>
/stats - Full stats dashboard
/army_chart - Army composition chart
/resource_chart - Resource trends
/battle_stats - Battle analytics
/power_profile - Power radar chart
/achievements_chart - Achievement progress
/leaderboard_chart - Visual leaderboard
/compare [name] - Compare with player

<u>Animations (GIFs)</u>
/animate_battle [enemy] [result] - Battle animation
/levelup_anim [name] [type] [old] [new] - Level up
/reward_anim [type] [amount] - Reward animation
/train_anim [unit] [count] - Training animation
/achievement_anim [name] [rarity] - Achievement unlock
/spin - Lucky spin wheel

<u>Image Cards</u>
/hero_card [name] - Hero stat card
/kingdom_banner - Kingdom banner
/battle_report [enemy] [result] - Battle report
/spy_report_card [target] [intel] - Spy report
/podium - Top 3 podium

<u>Utility</u>
/notify_test - Test notification
/visual_help - This menu

<i>Note: Install dependencies for full visuals:</i>
<code>pip install matplotlib seaborn Pillow numpy</code>
    """
    await update.message.reply_text(help_text, parse_mode='HTML')

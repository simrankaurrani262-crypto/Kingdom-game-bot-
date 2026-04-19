"""
Inline keyboard builders for Kingdom Conquest.
Clean, consistent button layouts for all game menus.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.constants import BUILDINGS, ARMY_UNITS


def main_menu_keyboard():
    """Main game menu after /start."""
    buttons = [
        [InlineKeyboardButton("⚔️ Attack", callback_data="menu_attack"),
         InlineKeyboardButton("🏰 Kingdom", callback_data="menu_kingdom")],
        [InlineKeyboardButton("🏗 Buildings", callback_data="menu_build"),
         InlineKeyboardButton("🎖 Army", callback_data="menu_army")],
        [InlineKeyboardButton("🗺 Map", callback_data="menu_map"),
         InlineKeyboardButton("🎯 Quests", callback_data="menu_quests")],
        [InlineKeyboardButton("🤝 Alliance", callback_data="menu_alliance"),
         InlineKeyboardButton("🧙 Heroes", callback_data="menu_heroes")],
        [InlineKeyboardButton("🕵️ Spy", callback_data="menu_spy"),
         InlineKeyboardButton("🎲 Games", callback_data="menu_games")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="menu_leaderboard"),
         InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")],
    ]
    return InlineKeyboardMarkup(buttons)


def dashboard_keyboard():
    """Alternative dashboard layout."""
    return main_menu_keyboard()


def build_menu_keyboard(buildings):
    """Building menu with upgrade buttons."""
    buttons = []
    for btype, info in BUILDINGS.items():
        found = False
        level = 0
        is_upgrading = False
        for b in buildings:
            if b.get('building_type') == btype:
                found = True
                level = b.get('level', 1)
                is_upgrading = b.get('is_upgrading', 0) == 1
                break
        status = " 🔨" if is_upgrading else ""
        buttons.append([InlineKeyboardButton(
            f"{info['emoji']} {info['name']} (Lv.{level}){status}",
            callback_data=f"build_upgrade:{btype}"
        )])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")])
    return InlineKeyboardMarkup(buttons)


def building_upgrade_keyboard(btype):
    """Confirm/cancel for building upgrade."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬆️ Upgrade", callback_data=f"build_confirm:{btype}")],
        [InlineKeyboardButton("ℹ️ Info", callback_data=f"build_info:{btype}")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_build")],
    ])


def army_menu_keyboard():
    """Army training menu."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗡 Train Infantry", callback_data="army_train:infantry"),
         InlineKeyboardButton("🏹 Train Archers", callback_data="army_train:archers")],
        [InlineKeyboardButton("🐎 Train Cavalry", callback_data="army_train:cavalry")],
        [InlineKeyboardButton("📊 Army Status", callback_data="army_status")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
    ])


def train_confirm_keyboard(unit_type, count):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ Train {count}", callback_data=f"train_confirm:{unit_type}:{count}")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_army")],
    ])


def attack_menu_keyboard(target):
    """Attack options for a target."""
    target_id = target.get('user_id', 0)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Quick Attack", callback_data=f"attack_start:{target_id}")],
        [InlineKeyboardButton("📋 Ranked Targets", callback_data="attack_ranked")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
    ])


def attack_confirm_keyboard(target_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ ATTACK!", callback_data=f"attack_target:{target_id}")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="menu_attack")],
    ])


def battle_result_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Attack Again", callback_data="menu_attack")],
        [InlineKeyboardButton("🏠 Dashboard", callback_data="back_dashboard")],
    ])


def spy_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🕵️ Send Spy", callback_data="spy_send")],
        [InlineKeyboardButton("📜 Past Reports", callback_data="spy_reports")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
    ])


def spy_target_keyboard(targets):
    buttons = []
    for t in targets:
        buttons.append([InlineKeyboardButton(
            f"🕵️ {t.get('kingdom_name', 'Unknown')[:15]}",
            callback_data=f"spy_target:{t['user_id']}"
        )])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="menu_spy")])
    return InlineKeyboardMarkup(buttons)


def games_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Dice Game", callback_data="game_dice")],
        [InlineKeyboardButton("🎰 Lucky Spin", callback_data="game_spin")],
        [InlineKeyboardButton("🧠 Kingdom Quiz", callback_data="game_quiz")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
    ])


def dice_game_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Bet 100", callback_data="dice_bet:100"),
         InlineKeyboardButton("💰 Bet 500", callback_data="dice_bet:500")],
        [InlineKeyboardButton("💰 Bet 1000", callback_data="dice_bet:1000"),
         InlineKeyboardButton("💰 Bet 5000", callback_data="dice_bet:5000")],
        [InlineKeyboardButton("🎲 Roll!", callback_data="dice_roll")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_games")],
    ])


def spin_wheel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 Spin!", callback_data="spin_spin")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_games")],
    ])


def quiz_keyboard(q_idx, options, correct_idx):
    buttons = []
    for i, opt in enumerate(options):
        buttons.append([InlineKeyboardButton(
            f"{'ABCD'[i]}. {opt}",
            callback_data=f"quiz_answer:{q_idx}:{i}"
        )])
    return InlineKeyboardMarkup(buttons)


def alliance_hub_keyboard(in_alliance=False):
    if in_alliance:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 Members", callback_data="alliance_members"),
             InlineKeyboardButton("💰 Donate", callback_data="alliance_donate")],
            [InlineKeyboardButton("⚔️ Team War", callback_data="alliance_war")],
            [InlineKeyboardButton("🚪 Leave", callback_data="alliance_leave")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏰 Create Alliance", callback_data="alliance_create")],
        [InlineKeyboardButton("🔍 Join Alliance", callback_data="alliance_join")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
    ])


def heroes_menu_keyboard(heroes):
    buttons = []
    for hero in heroes:
        hkey = hero.get('hero_key', 'unknown')
        unlocked = hero.get('is_unlocked', 0)
        status = "🔓" if unlocked else "🔒"
        buttons.append([InlineKeyboardButton(
            f"{status} {hkey.replace('_', ' ').title()}",
            callback_data=f"hero_manage:{hkey}" if unlocked else f"hero_unlock:{hkey}"
        )])
    buttons.append([InlineKeyboardButton("🌲 Skill Trees", callback_data="skill_trees")])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")])
    return InlineKeyboardMarkup(buttons)


def hero_manage_keyboard(hero_key, is_active):
    buttons = [
        [InlineKeyboardButton("⬆️ Level Up", callback_data=f"hero_levelup:{hero_key}")],
    ]
    if is_active:
        buttons.append([InlineKeyboardButton("✅ Active", callback_data="noop")])
    else:
        buttons.append([InlineKeyboardButton("🔄 Activate", callback_data=f"hero_activate:{hero_key}")])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="menu_heroes")])
    return InlineKeyboardMarkup(buttons)


def skill_tree_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚔️ Attack", callback_data="skill_attack")],
        [InlineKeyboardButton("🛡 Defense", callback_data="skill_defense")],
        [InlineKeyboardButton("💰 Economy", callback_data="skill_economy")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_heroes")],
    ])


def leaderboard_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Players", callback_data="lb_players"),
         InlineKeyboardButton("🤝 Alliances", callback_data="lb_alliances")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
    ])


def quest_menu_keyboard(has_claimable=False):
    buttons = []
    if has_claimable:
        buttons.append([InlineKeyboardButton("🎁 Claim Rewards", callback_data="quest_claim")])
    buttons.append([InlineKeyboardButton("🔄 Refresh", callback_data="menu_quests")])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")])
    return InlineKeyboardMarkup(buttons)


def settings_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Notifications", callback_data="settings_notifs")],
        [InlineKeyboardButton("🌐 Language", callback_data="settings_lang")],
        [InlineKeyboardButton("📊 Stats", callback_data="settings_stats")],
        [InlineKeyboardButton("❓ Help", callback_data="settings_help")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
    ])


def map_action_keyboard():
    """Map action keyboard - added to fix missing import in map_system.py."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="menu_map")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
    ])


def back_button_keyboard(back_callback="back_dashboard"):
    """Simple back button."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data=back_callback)],
    ])

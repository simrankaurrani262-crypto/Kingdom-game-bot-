"""
Inline keyboard factories for all bot menus.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Main dashboard navigation keyboard."""
    keyboard = [
        [InlineKeyboardButton("⚔️ Attack", callback_data="menu_attack"),
         InlineKeyboardButton("🏗 Build", callback_data="menu_build")],
        [InlineKeyboardButton("🗺 Map", callback_data="menu_map"),
         InlineKeyboardButton("🤝 Alliance", callback_data="menu_alliance")],
        [InlineKeyboardButton("🧙 Heroes", callback_data="menu_heroes"),
         InlineKeyboardButton("🕵️ Spy", callback_data="menu_spy")],
        [InlineKeyboardButton("🎯 Quests", callback_data="menu_quests"),
         InlineKeyboardButton("🏆 Leaderboard", callback_data="menu_leaderboard")],
        [InlineKeyboardButton("🎲 Mini-Games", callback_data="menu_games"),
         InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")],
    ]
    return InlineKeyboardMarkup(keyboard)


def attack_menu_keyboard() -> InlineKeyboardMarkup:
    """Attack mode menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🎯 Find Opponent", callback_data="attack_find")],
        [InlineKeyboardButton("🔥 Revenge", callback_data="attack_revenge")],
        [InlineKeyboardButton("🗺 Map Select", callback_data="attack_map")],
        [InlineKeyboardButton("🏃 Quick Raid", callback_data="attack_raid")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
    ]
    return InlineKeyboardMarkup(keyboard)


def opponent_card_keyboard(target_id: int) -> InlineKeyboardMarkup:
    """Opponent action buttons."""
    keyboard = [
        [InlineKeyboardButton("⚔️ Attack", callback_data=f"attack_start:{target_id}"),
         InlineKeyboardButton("🕵️ Spy", callback_data=f"spy_target:{target_id}")],
        [InlineKeyboardButton("⏭️ Next", callback_data="attack_next"),
         InlineKeyboardButton("🔙 Back", callback_data="menu_attack")],
    ]
    return InlineKeyboardMarkup(keyboard)


def battle_response_keyboard(request_id: str) -> InlineKeyboardMarkup:
    """Defender battle response keyboard."""
    keyboard = [
        [InlineKeyboardButton("✅ Accept Fight", callback_data=f"battle_accept:{request_id}"),
         InlineKeyboardButton("❌ Decline", callback_data=f"battle_decline:{request_id}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def building_menu_keyboard(buildings: list) -> InlineKeyboardMarkup:
    """Building menu with upgrade/collect buttons."""
    keyboard = []
    for b in buildings:
        btype = b['building_type']
        emoji = {'town_hall': '🏰', 'gold_mine': '⛏', 'farm': '🌾',
                 'barracks': '🏹', 'wall': '🛡'}.get(btype, '🏗')
        name = btype.replace('_', ' ').title()
        level = b['level']
        
        row = [
            InlineKeyboardButton(f"{emoji} {name} Lv.{level}", callback_data=f"build_info:{btype}"),
            InlineKeyboardButton("⬆️", callback_data=f"build_upgrade:{btype}"),
            InlineKeyboardButton("📥", callback_data=f"build_collect:{btype}"),
        ]
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")])
    return InlineKeyboardMarkup(keyboard)


def building_action_keyboard(btype: str, is_upgrading: bool = False) -> InlineKeyboardMarkup:
    """Individual building action keyboard."""
    keyboard = []
    if not is_upgrading:
        keyboard.append([InlineKeyboardButton("⬆️ Upgrade", callback_data=f"build_upgrade:{btype}")])
    keyboard.append([InlineKeyboardButton("📥 Collect Resources", callback_data=f"build_collect:{btype}")])
    keyboard.append([InlineKeyboardButton("ℹ️ Info", callback_data=f"build_info:{btype}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_build")])
    return InlineKeyboardMarkup(keyboard)


def army_menu_keyboard(army: dict, barracks_level: int = 1) -> InlineKeyboardMarkup:
    """Army management keyboard."""
    keyboard = [
        [InlineKeyboardButton(f"🗡 Train Infantry (+5) 💰50", callback_data="army_train:infantry")],
    ]
    if barracks_level >= 2:
        keyboard.append([InlineKeyboardButton(f"🏹 Train Archers (+5) 💰80", callback_data="army_train:archers")])
    if barracks_level >= 4:
        keyboard.append([InlineKeyboardButton(f"🐎 Train Cavalry (+5) 💰150", callback_data="army_train:cavalry")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")])
    return InlineKeyboardMarkup(keyboard)


def map_action_keyboard(x: int, y: int, has_kingdom: bool = False,
                        is_self: bool = False, is_ally: bool = False) -> InlineKeyboardMarkup:
    """Map tile action keyboard."""
    keyboard = []
    if has_kingdom and not is_self and not is_ally:
        keyboard.append([
            InlineKeyboardButton("⚔️ Attack", callback_data=f"map_attack:{x}:{y}"),
            InlineKeyboardButton("🕵️ Spy", callback_data=f"map_spy:{x}:{y}"),
        ])
    elif has_kingdom and is_ally:
        keyboard.append([InlineKeyboardButton("💬 Alliance Chat", callback_data="alliance_chat")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Map", callback_data="menu_map")])
    return InlineKeyboardMarkup(keyboard)


def alliance_hub_keyboard(in_alliance: bool = False) -> InlineKeyboardMarkup:
    """Alliance hub keyboard."""
    if not in_alliance:
        keyboard = [
            [InlineKeyboardButton("🏰 Create Alliance 💰10,000", callback_data="alliance_create")],
            [InlineKeyboardButton("🔍 Join Alliance", callback_data="alliance_join")],
            [InlineKeyboardButton("📋 Invites", callback_data="alliance_invites")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("👥 Members", callback_data="alliance_members"),
             InlineKeyboardButton("⚔️ Team War", callback_data="alliance_war")],
            [InlineKeyboardButton("💰 Donate", callback_data="alliance_donate"),
             InlineKeyboardButton("💬 Chat", callback_data="alliance_chat")],
            [InlineKeyboardButton("🚪 Leave", callback_data="alliance_leave")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
        ]
    return InlineKeyboardMarkup(keyboard)


def quest_menu_keyboard(has_claimable: bool = False) -> InlineKeyboardMarkup:
    """Quest menu keyboard."""
    keyboard = []
    if has_claimable:
        keyboard.append([InlineKeyboardButton("📥 Claim All Rewards", callback_data="quest_claim")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")])
    return InlineKeyboardMarkup(keyboard)


def heroes_menu_keyboard(heroes: list) -> InlineKeyboardMarkup:
    """Hero roster keyboard."""
    keyboard = []
    for hero in heroes:
        hkey = hero['hero_key']
        level = hero['level']
        if hero.get('is_unlocked'):
            status = f"Lv.{level}"
            btn_text = f"⚔️ {hkey.replace('_', ' ').title()} {status}"
            callback = f"hero_manage:{hkey}"
        else:
            btn_text = f"🔒 {hkey.replace('_', ' ').title()} (Unlock)"
            callback = f"hero_unlock:{hkey}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback)])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")])
    return InlineKeyboardMarkup(keyboard)


def hero_manage_keyboard(hero_key: str, is_active: bool = False) -> InlineKeyboardMarkup:
    """Hero management keyboard."""
    keyboard = [
        [InlineKeyboardButton("⬆️ Level Up", callback_data=f"hero_levelup:{hero_key}")],
        [InlineKeyboardButton("🎯 Set Active" if not is_active else "✅ Already Active",
                              callback_data=f"hero_activate:{hero_key}")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_heroes")],
    ]
    return InlineKeyboardMarkup(keyboard)


def skill_tree_keyboard() -> InlineKeyboardMarkup:
    """Skill tree keyboard."""
    keyboard = [
        [InlineKeyboardButton("⚔️ Attack Tree", callback_data="skill_attack"),
         InlineKeyboardButton("🛡 Defense Tree", callback_data="skill_defense")],
        [InlineKeyboardButton("💰 Economy Tree", callback_data="skill_economy")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_heroes")],
    ]
    return InlineKeyboardMarkup(keyboard)


def spy_menu_keyboard() -> InlineKeyboardMarkup:
    """Spy menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🕵️ Send Spy 💰300", callback_data="spy_send")],
        [InlineKeyboardButton("📜 Past Reports", callback_data="spy_reports")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
    ]
    return InlineKeyboardMarkup(keyboard)


def black_market_keyboard(items: list) -> InlineKeyboardMarkup:
    """Black market purchase keyboard."""
    keyboard = []
    for i, item in enumerate(items):
        keyboard.append([InlineKeyboardButton(
            f"{item['name']} — 💎{item['price_gems']}",
            callback_data=f"market_buy:{i}"
        )])
    keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="market_refresh")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")])
    return InlineKeyboardMarkup(keyboard)


def games_menu_keyboard() -> InlineKeyboardMarkup:
    """Mini-games menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🎲 Dice Game", callback_data="game_dice")],
        [InlineKeyboardButton("🎰 Lucky Spin", callback_data="game_spin")],
        [InlineKeyboardButton("🧠 Kingdom Quiz", callback_data="game_quiz")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
    ]
    return InlineKeyboardMarkup(keyboard)


def dice_game_keyboard() -> InlineKeyboardMarkup:
    """Dice game bet keyboard."""
    keyboard = [
        [InlineKeyboardButton("💰 100", callback_data="dice_bet:100"),
         InlineKeyboardButton("💰 500", callback_data="dice_bet:500"),
         InlineKeyboardButton("💰 1000", callback_data="dice_bet:1000")],
        [InlineKeyboardButton("🎲 Roll!", callback_data="dice_roll")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_games")],
    ]
    return InlineKeyboardMarkup(keyboard)


def spin_wheel_keyboard() -> InlineKeyboardMarkup:
    """Spin wheel keyboard."""
    keyboard = [
        [InlineKeyboardButton("🎰 SPIN!", callback_data="spin_spin")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_games")],
    ]
    return InlineKeyboardMarkup(keyboard)


def quiz_keyboard(question_idx: int, options: list, correct_idx: int) -> InlineKeyboardMarkup:
    """Quiz answer keyboard."""
    keyboard = []
    letters = ['A', 'B', 'C', 'D']
    row = []
    for i, option in enumerate(options):
        row.append(InlineKeyboardButton(
            f"{letters[i]}. {option}",
            callback_data=f"quiz_answer:{question_idx}:{i}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_games")])
    return InlineKeyboardMarkup(keyboard)


def leaderboard_keyboard() -> InlineKeyboardMarkup:
    """Leaderboard view keyboard."""
    keyboard = [
        [InlineKeyboardButton("👤 Players", callback_data="lb_players"),
         InlineKeyboardButton("🤝 Alliances", callback_data="lb_alliances")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
    ]
    return InlineKeyboardMarkup(keyboard)


def settings_keyboard() -> InlineKeyboardMarkup:
    """Settings menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔔 Notifications", callback_data="settings_notifs")],
        [InlineKeyboardButton("🌐 Language", callback_data="settings_lang")],
        [InlineKeyboardButton("📊 Stats", callback_data="settings_stats")],
        [InlineKeyboardButton("❓ Help", callback_data="settings_help")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")],
    ]
    return InlineKeyboardMarkup(keyboard)


def revenge_keyboard(attacker_id: int) -> InlineKeyboardMarkup:
    """Revenge action keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔥 Revenge!", callback_data=f"revenge_attack:{attacker_id}")],
        [InlineKeyboardButton("🛡 Ignore", callback_data="revenge_ignore")],
    ]
    return InlineKeyboardMarkup(keyboard)


def decision_event_keyboard(event_id: str) -> InlineKeyboardMarkup:
    """Decision event choice keyboard."""
    keyboard = [
        [InlineKeyboardButton("💰 Option A", callback_data=f"decision:{event_id}:A")],
        [InlineKeyboardButton("⚔️ Option B", callback_data=f"decision:{event_id}:B")],
        [InlineKeyboardButton("🚪 Option C", callback_data=f"decision:{event_id}:C")],
    ]
    return InlineKeyboardMarkup(keyboard)


def confirm_action_keyboard(action: str, **kwargs) -> InlineKeyboardMarkup:
    """Generic confirmation keyboard."""
    params = ":".join(f"{v}" for v in kwargs.values())
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data=f"confirm:{action}:{params}"),
         InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_button_keyboard(back_callback: str = "back_dashboard") -> InlineKeyboardMarkup:
    """Simple back button."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data=back_callback)],
    ])


def welcome_keyboard() -> InlineKeyboardMarkup:
    """Initial welcome keyboard."""
    keyboard = [
        [InlineKeyboardButton("🎮 Start Game", callback_data="start_game")],
        [InlineKeyboardButton("📖 How to Play", callback_data="how_to_play")],
    ]
    return InlineKeyboardMarkup(keyboard)


def trait_selection_keyboard() -> InlineKeyboardMarkup:
    """Kingdom trait selection keyboard."""
    keyboard = [
        [InlineKeyboardButton("⚔️ Aakramak (+10% Attack)", callback_data="trait:aggressive")],
        [InlineKeyboardButton("🛡 Surakshit (+15% Defense)", callback_data="trait:defensive")],
        [InlineKeyboardButton("💰 Dhanwan (+20% Gold)", callback_data="trait:rich")],
        [InlineKeyboardButton("⚖️ Santulit (+5% All)", callback_data="trait:balanced")],
    ]
    return InlineKeyboardMarkup(keyboard)


def flag_selection_keyboard() -> InlineKeyboardMarkup:
    """Flag emoji selection keyboard (4x6 grid)."""
    flags = [
        '🔥', '⚡', '🌊', '🌪', '🌑', '☀️',
        '❄️', '🍃', '💀', '👑', '🦁', '🐉',
        '🦅', '🐺', '🦊', '🐻', '🌹', '🍁',
        '🌵', '💎', '⚜️', '🏴', '🏳', '🎯',
    ]
    keyboard = []
    row = []
    for i, flag in enumerate(flags):
        row.append(InlineKeyboardButton(flag, callback_data=f"flag:{flag}"))
        if (i + 1) % 6 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def how_to_play_keyboard(page: int = 1, max_pages: int = 5) -> InlineKeyboardMarkup:
    """Paginated how to play keyboard."""
    keyboard = []
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"help_page:{page-1}"))
    nav_row.append(InlineKeyboardButton(f"{page}/{max_pages}", callback_data="noop"))
    if page < max_pages:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f"help_page:{page+1}"))
    keyboard.append(nav_row)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_welcome")])
    return InlineKeyboardMarkup(keyboard)


def tutorial_step_keyboard(step: int) -> InlineKeyboardMarkup:
    """Tutorial interactive buttons."""
    if step == 1:
        keyboard = [
            [InlineKeyboardButton("🏗 Build Menu", callback_data="tutorial_build")],
        ]
    elif step == 2:
        keyboard = [
            [InlineKeyboardButton("⬆️ Upgrade Town Hall", callback_data="tutorial_upgrade")],
        ]
    elif step == 3:
        keyboard = [
            [InlineKeyboardButton("⚔️ Attack!", callback_data="tutorial_attack")],
        ]
    else:
        keyboard = [[InlineKeyboardButton("🎮 Continue", callback_data="tutorial_done")]]
    return InlineKeyboardMarkup(keyboard)

# Add to existing keyboards.py

def stats_menu_keyboard():
    """Main stats menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("Army Composition", callback_data='stats_army'),
         InlineKeyboardButton("Resource Trends", callback_data='stats_resources')],
        [InlineKeyboardButton("Battle Analytics", callback_data='stats_battle'),
         InlineKeyboardButton("Power Profile", callback_data='stats_power')],
        [InlineKeyboardButton("Activity Heatmap", callback_data='stats_activity'),
         InlineKeyboardButton("Economy", callback_data='stats_economy')],
        [InlineKeyboardButton("Back to Dashboard", callback_data='stats_dashboard')],
    ]
    return InlineKeyboardMarkup(keyboard)

def visual_menu_keyboard():
    """Visual commands menu."""
    keyboard = [
        [InlineKeyboardButton("Charts", callback_data='visual_charts'),
         InlineKeyboardButton("Animations", callback_data='visual_animations')],
        [InlineKeyboardButton("Cards", callback_data='visual_cards'),
         InlineKeyboardButton("Leaderboard", callback_data='visual_leaderboard')],
        [InlineKeyboardButton("Help", callback_data='visual_help')],
    ]
    return InlineKeyboardMarkup(keyboard)
        

"""
Start handler for Kingdom Conquest.
Handles /start command, onboarding wizard, and tutorial.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import random

from models.database import Database
from services.economy import EconomyService
from utils.keyboards import (
    welcome_keyboard, flag_selection_keyboard, trait_selection_keyboard,
    tutorial_step_keyboard, main_dashboard_keyboard
)
from utils.formatters import format_number
from utils.assets import get_scene_image
from config import MAP_SIZE, STARTER_GOLD, STARTER_FOOD

db = Database()


async def handler_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    
    db.create_user(
        telegram_id=telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    db.update_user_activity(telegram_id)
    
    kingdom = db.get_kingdom(telegram_id)
    
    if kingdom:
        from .dashboard import render_dashboard
        await render_dashboard(update, context)
        return
    
    welcome_text = """
⚔️ <b>WELCOME TO KINGDOM CONQUEST</b> ⚔️

👑 <b>Become a Great King!</b>
🏰 <b>Build Your Kingdom</b>
⚔️ <b>Attack Enemies</b>
🏆 <b>Become the Most Powerful!</b>

<i>A strategy game where you build your kingdom,
train armies, and attack enemies!</i>

🎮 <b>Press Start Game to begin!</b>
"""
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text=welcome_text,
            reply_markup=welcome_keyboard(),
            parse_mode='HTML'
        )
    else:
        welcome_img = get_scene_image('welcome')
        if welcome_img:
            await update.message.reply_photo(
                photo=open(welcome_img, 'rb'),
                caption=welcome_text,
                reply_markup=welcome_keyboard(),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                text=welcome_text,
                reply_markup=welcome_keyboard(),
                parse_mode='HTML'
            )


async def handle_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "start_game":
        await start_kingdom_creation(update, context)
    elif data == "how_to_play":
        await show_how_to_play(update, context, page=1)
    elif data.startswith("help_page:"):
        page = int(data.split(":")[1])
        await show_how_to_play(update, context, page=page)
    elif data == "back_welcome":
        await handler_start(update, context)


async def start_kingdom_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['creation_step'] = 'name'
    
    text = """
🏰 <b>KINGDOM CREATION</b>
━━━━━━━━━━━━━━

<b>Step 1/3:</b> Name your Kingdom!

<i>3-20 characters, alphanumeric + spaces</i>

<b>Examples:</b> Shadow Empire, Fire Kingdom, Thunder Realm

📝 <b>Type your kingdom name below:</b>
"""
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, parse_mode='HTML')
    else:
        await update.message.reply_text(text=text, parse_mode='HTML')


async def process_kingdom_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('creation_step') != 'name':
        return
    
    name = update.message.text.strip()
    
    if len(name) < 3 or len(name) > 20:
        await update.message.reply_text(
            "❌ <b>Invalid Name!</b>\n3-20 characters required.\nTry again:",
            parse_mode='HTML'
        )
        return
    
    if not all(c.isalnum() or c.isspace() for c in name):
        await update.message.reply_text(
            "❌ <b>Invalid Characters!</b>\nOnly letters, numbers, and spaces.\nTry again:",
            parse_mode='HTML'
        )
        return
    
    context.user_data['kingdom_name'] = name
    context.user_data['creation_step'] = 'flag'
    
    text = f"""
🏰 <b>KINGDOM CREATION</b>
━━━━━━━━━━━━━━

<b>Step 2/3:</b> Choose Your Flag!

Kingdom Name: <b>{name}</b>

<b>Select your kingdom's symbol:</b>
"""
    
    await update.message.reply_text(
        text=text,
        reply_markup=flag_selection_keyboard(),
        parse_mode='HTML'
    )


async def process_flag_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if context.user_data.get('creation_step') != 'flag':
        return
    
    flag = query.data.split(":")[1]
    context.user_data['kingdom_flag'] = flag
    context.user_data['creation_step'] = 'trait'
    
    name = context.user_data.get('kingdom_name', 'Unknown')
    
    text = f"""
🏰 <b>KINGDOM CREATION</b>
━━━━━━━━━━━━━━

<b>Step 3/3:</b> Choose Your Trait!

Kingdom: <b>{name}</b> {flag}

<b>Choose your kingdom's specialty:</b>

⚔️ <b>Aggressive</b> - +10% Attack power
🛡 <b>Defensive</b> - +15% Defense
💰 <b>Rich</b> - +20% Gold production
⚖️ <b>Balanced</b> - +5% All stats
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=trait_selection_keyboard(),
        parse_mode='HTML'
    )


async def process_trait_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    trait = query.data.split(":")[1]
    user_id = update.effective_user.id
    name = context.user_data.get('kingdom_name', 'My Kingdom')
    flag = context.user_data.get('kingdom_flag', '🔥')
    
    existing = db.get_all_kingdoms()
    occupied = set((k.get('map_x'), k.get('map_y')) for k in existing)
    
    map_x, map_y = 5, 5
    for _ in range(100):
        x = random.randint(1, MAP_SIZE)
        y = random.randint(1, MAP_SIZE)
        if (x, y) not in occupied:
            map_x, map_y = x, y
            break
    
    success = db.create_kingdom(
        user_id=user_id, name=name, flag=flag,
        map_x=map_x, map_y=map_y, trait=trait,
    )
    
    if not success:
        await query.edit_message_text(
            "❌ <b>Error!</b> Could not create kingdom.\nTry /start again.",
            parse_mode='HTML'
        )
        return
    
    init_daily_quests(user_id)
    context.user_data.pop('creation_step', None)
    
    victory_img = get_scene_image('victory')
    
    text = f"""
🎉 <b>KINGDOM CREATED!</b>
━━━━━━━━━━━━━━

👑 Kingdom: <b>{name}</b> {flag}
📍 Location: ({map_x}, {map_y})
⚡ Trait: <b>{trait.title()}</b>

💰 Gold: {format_number(STARTER_GOLD)}
🍖 Food: {format_number(STARTER_FOOD)}
⚡ Energy: 10/10
🗡 Infantry: 50

🛡 <b>Newbie Shield:</b> 24 hours

<i>Let's start the tutorial!</i>
"""
    
    await query.edit_message_text(
        text=text,
        reply_markup=tutorial_step_keyboard(step=1),
        parse_mode='HTML'
    )
    db.update_kingdom(user_id, tutorial_step=1)


async def show_how_to_play(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    pages = {
        1: """📖 <b>HOW TO PLAY</b> - Page 1/5
━━━━━━━━━━━━━━

<b>🎮 Core Loop:</b>
1️⃣ <b>Collect Resources</b> - From Gold Mine & Farm
2️⃣ <b>Build & Upgrade</b> - Level up buildings
3️⃣ <b>Train Army</b> - Barracks soldiers
4️⃣ <b>Attack Enemies</b> - Fight other players
5️⃣ <b>Win & Loot</b> - Gold and XP!

<b>⚡ Energy System:</b>
- Each attack costs 1 energy
- Energy regenerates every 30 minutes
- Max 10 energy storage""",
        2: """📖 <b>HOW TO PLAY</b> - Page 2/5
━━━━━━━━━━━━━━

<b>⚔️ Army Types:</b>

🗡 <b>Infantry</b> - Basic soldiers
   Attack: 10 | Defense: 8 | Speed: Slow
   Food: 2/hr | Unlock: Starter

🏹 <b>Archers</b> - Long range
   Attack: 12 | Defense: 5 | Speed: Medium
   Food: 3/hr | Unlock: Barracks Lv.2

🐎 <b>Cavalry</b> - Fast charge
   Attack: 18 | Defense: 12 | Speed: Fast
   Food: 5/hr | Unlock: Barracks Lv.4

<b>💡 Tip:</b> Balanced army is strongest!""",
        3: """📖 <b>HOW TO PLAY</b> - Page 3/5
━━━━━━━━━━━━━━

<b>🏗 Buildings:</b>

🏰 <b>Town Hall</b> - Kingdom level
⛏ <b>Gold Mine</b> - Gold production
🌾 <b>Farm</b> - Food production
🏹 <b>Barracks</b> - Army training
🛡 <b>Wall</b> - Defense boost

<b>⬆️ Tips:</b>
- Upgrade Gold Mine & Farm first
- Barracks Lv.2 unlocks Archers
- Keep Wall updated always""",
        4: """📖 <b>HOW TO PLAY</b> - Page 4/5
━━━━━━━━━━━━━━

<b>🛡 Energy & Shield:</b>

⚡ <b>Energy:</b>
- Attack/Raid costs 1 energy
- 30 min = 1 energy regen
- Max 10 energy

🛡 <b>Shield:</b>
- New players get 24h shield
- Can't be attacked with shield
- Shield breaks when YOU attack

<b>🏆 Leaderboard:</b>
- Power = Army + Buildings + Heroes + Level
- Season resets every 14 days
- Top 100 get rewards""",
        5: """📖 <b>HOW TO PLAY</b> - Page 5/5
━━━━━━━━━━━━━━

<b>🤝 Alliance:</b>
- 10,000 Gold to create
- Max 20 members
- Team wars with shared rewards

<b>🎯 Quests:</b>
- Daily quests reset every day
- Milestone quests one-time
- Rewards: Gold, XP, Gems

<b>💎 Gems (Premium):</b>
- Black Market purchases
- Speed ups, shields, energy refills

<b>🎉 Ready? Start playing!</b>""",
    }
    
    text = pages.get(page, pages[1])
    keyboard = [
        [
            InlineKeyboardButton("⬅️", callback_data=f"help_page:{page-1}" if page > 1 else "noop"),
            InlineKeyboardButton(f"{page}/5", callback_data="noop"),
            InlineKeyboardButton("➡️", callback_data=f"help_page:{page+1}" if page < 5 else "noop")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="back_welcome")],
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML'
        )


async def handle_tutorial_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "tutorial_build":
        await tutorial_step_1(update, context)
    elif data == "tutorial_upgrade":
        await tutorial_step_2(update, context)
    elif data == "tutorial_attack":
        await tutorial_step_3(update, context)
    elif data == "tutorial_done":
        await complete_tutorial(update, context)


async def tutorial_step_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = """
📚 <b>TUTORIAL - Step 1/3</b>
━━━━━━━━━━━━━━

💰 <b>Collect Resources from Gold Mine!</b>

1. Go to <b>Build Menu</b>
2. Click on Gold Mine
3. Press <b>📥 Collect</b>

<i>Resources produce every hour.
More wait = More resources!</i>

🎁 <b>Reward:</b> +100 Gold
"""
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏗 Open Build Menu", callback_data="menu_build")],
        ]),
        parse_mode='HTML'
    )
    db.update_kingdom(user_id, tutorial_step=1)


async def tutorial_step_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = """
📚 <b>TUTORIAL - Step 2/3</b>
━━━━━━━━━━━━━━

⬆️ <b>Upgrade Town Hall!</b>

1. Go to <b>Build Menu</b>
2. Select Town Hall
3. Press <b>⬆️ Upgrade</b>

<i>Upgrades increase capacity.
Town Hall level = Kingdom level!</i>

🎁 <b>Reward:</b> +200 Gold, +50 Food
"""
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏗 Open Build Menu", callback_data="menu_build")],
        ]),
        parse_mode='HTML'
    )
    db.update_kingdom(user_id, tutorial_step=2)


async def tutorial_step_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = """
📚 <b>TUTORIAL - Step 3/3</b>
━━━━━━━━━━━━━━

⚔️ <b>Make Your First Attack!</b>

1. Go to <b>Attack Menu</b>
2. Press <b>🎯 Find Opponent</b>
3. Attack the dummy player

<i>Each attack costs 1 energy.
Win to earn Gold and XP!</i>

🎁 <b>Reward:</b> +500 Gold, +50 XP
"""
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚔️ Open Attack Menu", callback_data="menu_attack")],
        ]),
        parse_mode='HTML'
    )
    db.update_kingdom(user_id, tutorial_step=3)


async def complete_tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    kingdom = db.get_kingdom(user_id)
    
    if kingdom:
        new_gold = kingdom.get('gold', 0) + 500
        new_food = kingdom.get('food', 0) + 200
        new_gems = kingdom.get('gems', 0) + 1
        db.update_kingdom(
            user_id, gold=new_gold, food=new_food, gems=new_gems,
            tutorial_completed=1, tutorial_step=999,
        )
    
    text = """
🎉 <b>TUTORIAL COMPLETE!</b>
━━━━━━━━━━━━━━

You are now ready!

🎁 <b>Rewards:</b>
💰 +500 Gold
🍖 +200 Food
💎 +1 Gem

<i>Explore your dashboard!
Try Attack, Build, Quests - everything!</i>

⚔️ <b>Let the conquest begin!</b>
"""
    
    await update.callback_query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Dashboard", callback_data="back_dashboard")],
        ]),
        parse_mode='HTML'
    )


def init_daily_quests(user_id: int):
    daily_quests = [
        ('Daily Battler', 'daily_battler', 2),
        ('Resource Collector', 'resource_collector', 5000),
        ('Builder', 'builder', 3),
        ('Army Trainer', 'army_trainer', 50),
        ('Spy Master', 'spy_master', 2),
    ]
    for qtype, qkey, target in daily_quests:
        db.create_quest(user_id, qtype, qkey, target, daily=True)


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('creation_step') == 'name':
        await process_kingdom_name(update, context)

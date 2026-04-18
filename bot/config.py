"""
Configuration module for Kingdom Conquest Bot.
All environment variables and bot settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_bot_token_here")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://yourdomain.com/webhook")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8443"))
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "kingdom_bot.db")

# Admin
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))

# Game Balance - Starting Resources
STARTER_GOLD = 1000
STARTER_FOOD = 500
STARTER_ENERGY = 10
STARTER_INFANTRY = 50
STARTER_ARCHERS = 0
STARTER_CAVALRY = 0

# Energy System
MAX_ENERGY = 10
ENERGY_COST_ATTACK = 1
ENERGY_REGEN_MINUTES = 30
ENERGY_REGEN_RATE = 30

# New Player Protection
NEWBIE_SHIELD_HOURS = 24
SHIELD_BREAK_ON_ATTACK = True

# Map
MAP_SIZE = 10
COORDINATE_MIN = 1
COORDINATE_MAX = 10

# Attack Timeout
BATTLE_REQUEST_TIMEOUT = 30

# Buildings
BUILDING_MAX_LEVEL = 25
BASE_UPGRADE_TIME_MINUTES = 5
UPGRADE_TIME_MULTIPLIER = 1.4
BASE_UPGRADE_COST_GOLD = 500
UPGRADE_COST_MULTIPLIER = 1.6

# Army Food Consumption
FOOD_PER_ARMY_PER_HOUR = 2
ARMY_STARVATION_THRESHOLD = 0

# Combat
RANDOM_FACTOR_RANGE = (0.85, 1.15)
WALL_DEFENSE_REDUCTION_PER_LEVEL = 0.03
HERO_BONUS_PERCENT_PER_LEVEL = 0.05
PROXIMITY_ATTACK_BONUS = 0.10

# Resources Production (per hour, Level 1 base)
GOLD_MINE_BASE_RATE = 100
FARM_BASE_RATE = 50
BARRACKS_TRAIN_RATE = 10

# Leaderboard
LEADERBOARD_RESET_DAYS = 14

# Mini-games cooldowns
DICE_COOLDOWN_HOURS = 4
SPIN_COOLDOWN_HOURS = 8
QUIZ_COOLDOWN_HOURS = 6

# Spy System
SPY_COST_GOLD = 300
SPY_SUCCESS_BASE_CHANCE = 0.75
SPY_TRAP_CHANCE = 0.15
SPY_COOLDOWN_MINUTES = 60

# Raid System
RAID_ENERGY_COST = 1
RAID_LOOT_PERCENT = 0.15
RAID_ARMY_LOSS_PERCENT = 0.05

# Black Market
BLACK_MARKET_REFRESH_HOURS = 6
BLACK_MARKET_SLOTS = 4

# Training
TRAINING_BATCH_SIZE = 5
TRAINING_TIME_MINUTES = 2
MAX_TRAINING_QUEUE = 5

# Alliance
ALLIANCE_CREATION_COST = 10000
ALLIANCE_MAX_MEMBERS = 20

# Battle
MAX_BATTLE_ROUNDS = 5
LOOT_PERCENTAGE = 0.20
PARTICIPATION_XP = 25
WIN_BASE_XP = 100

# Revenge
REVENGE_WINDOW_SECONDS = 3600
REVENGE_ATTACK_BONUS = 0.10

# Achievements
ACHIEVEMENTS_DATA = {
    'first_blood': {'name': 'First Blood', 'desc': 'First battle win', 'title': '⚔️ Warrior'},
    'war_lord': {'name': 'War Lord', 'desc': 'Win 50 battles', 'title': '👑 War Lord'},
    'rich_king': {'name': 'Rich King', 'desc': 'Have 100K gold', 'title': '💰 Rich King'},
    'master_builder': {'name': 'Master Builder', 'desc': 'Max all buildings Lv.10', 'title': '🏗 Architect'},
    'spy_master': {'name': 'Spy Master', 'desc': '100 successful spy missions', 'title': '🕵️ Shadow'},
    'survivor': {'name': 'Survivor', 'desc': 'Survive 10 revenge attacks', 'title': '🛡 Unbreakable'},
    'diplomat': {'name': 'Diplomat', 'desc': 'Create top 10 alliance', 'title': '🤝 Diplomat'},
    'treasure_hunter': {'name': 'Treasure Hunter', 'desc': 'Find 10 hidden treasures', 'title': '🗺 Explorer'},
}

# Kingdom Traits
KINGDOM_TRAITS = {
    'aggressive': {
        'name': '⚔️ Aakramak',
        'description': 'Yuddh ke liye bane! +10% attack power',
        'attack_bonus': 0.10,
        'defense_penalty': -0.05,
        'economy_penalty': -0.05,
    },
    'defensive': {
        'name': '🛡 Surakshit',
        'description': 'Abhedya qila! +15% defense, +10% wall strength',
        'attack_penalty': -0.05,
        'defense_bonus': 0.15,
        'wall_bonus': 0.10,
    },
    'rich': {
        'name': '💰 Dhanwan',
        'description': 'Sona nadiyon ki tarah! +20% gold production',
        'gold_bonus': 0.20,
        'attack_penalty': -0.05,
    },
    'balanced': {
        'name': '⚖️ Santulit',
        'description': 'Sab mein mahir! +5% sabhi stats',
        'attack_bonus': 0.05,
        'defense_bonus': 0.05,
        'gold_bonus': 0.05,
    }
}

# Heroes Data
HEROES_DATA = {
    'sir_aldric': {
        'name': 'Sir Aldric',
        'emoji': '⚔️',
        'type': 'Warrior',
        'skill': '+15% Infantry attack',
        'attack_bonus': 0.15,
        'defense_bonus': 0.05,
        'unlock_building': 'barracks',
        'unlock_level': 3,
        'premium': False,
        'cost_gold': 2000,
    },
    'lyra': {
        'name': 'Lyra',
        'emoji': '🏹',
        'type': 'Archer',
        'skill': '+20% Archer range damage',
        'attack_bonus': 0.20,
        'defense_bonus': 0.0,
        'unlock_building': 'barracks',
        'unlock_level': 5,
        'premium': False,
        'cost_gold': 5000,
    },
    'kael': {
        'name': 'Kael',
        'emoji': '🐎',
        'type': 'Cavalry',
        'skill': '+25% Cavalry charge',
        'attack_bonus': 0.25,
        'defense_bonus': 0.0,
        'unlock_building': 'barracks',
        'unlock_level': 7,
        'premium': False,
        'cost_gold': 10000,
    },
    'morgana': {
        'name': 'Morgana',
        'emoji': '🧙',
        'type': 'Mage',
        'skill': 'Fireball: 10% AoE damage',
        'attack_bonus': 0.10,
        'defense_bonus': 0.0,
        'unlock_building': None,
        'unlock_level': 0,
        'premium': True,
        'cost_gems': 50,
    },
    'shadow': {
        'name': 'Shadow',
        'emoji': '🗡',
        'type': 'Assassin',
        'skill': 'First strike: +30% round 1',
        'attack_bonus': 0.30,
        'defense_bonus': 0.0,
        'unlock_building': None,
        'unlock_level': 0,
        'premium': True,
        'cost_gems': 75,
    },
}

# Skill Tree
SKILL_TREE = {
    'attack': {
        'tier_1': {'name': 'Tez Blade', 'effect': 0.05, 'cost': 1, 'desc': '+5% sabhi damage'},
        'tier_2': {'name': 'Cavalry Mastery', 'effect': 0.10, 'cost': 2, 'desc': '+10% cavalry', 'requires': 'tier_1'},
        'tier_3': {'name': 'Yuddh Cry', 'effect': 0.15, 'cost': 3, 'desc': '+15% attack sabhi', 'requires': 'tier_2'},
    },
    'defense': {
        'tier_1': {'name': 'Mazboot Deewar', 'effect': 0.05, 'cost': 1, 'desc': '+5% wall defense'},
        'tier_2': {'name': 'Archer Towers', 'effect': 0.10, 'cost': 2, 'desc': '+10% archer defense', 'requires': 'tier_1'},
        'tier_3': {'name': 'Qila', 'effect': 0.15, 'cost': 3, 'desc': '+15% sabhi defense', 'requires': 'tier_2'},
    },
    'economy': {
        'tier_1': {'name': 'Efficient Mining', 'effect': 0.10, 'cost': 1, 'desc': '+10% gold production'},
        'tier_2': {'name': 'Bountiful Harvest', 'effect': 0.15, 'cost': 2, 'desc': '+15% food production', 'requires': 'tier_1'},
        'tier_3': {'name': 'Trade Routes', 'effect': 0.20, 'cost': 3, 'desc': '+20% sabhi production', 'requires': 'tier_2'},
    }
}

# Black Market Items
BLACK_MARKET_ITEMS = [
    {'name': '🔥 Instant Build', 'effect': 'skip_build_time', 'price_gems': 10, 'stock': 3},
    {'name': '⚡ Energy Refill', 'effect': 'refill_energy', 'price_gems': 5, 'stock': 5},
    {'name': '🛡 24h Shield', 'effect': 'extend_shield', 'price_gems': 15, 'stock': 2},
    {'name': '📜 Spy Intel Pack', 'effect': 'full_spy_report', 'price_gems': 8, 'stock': 3},
    {'name': '💰 Gold Bag (10K)', 'effect': 'add_gold', 'price_gems': 20, 'stock': 2},
    {'name': '🎲 Lucky Dice', 'effect': 'extra_dice_roll', 'price_gems': 3, 'stock': 10},
]

# Survival Waves
SURVIVAL_WAVES = [
    {'wave': 1, 'enemies': 50, 'type': '🧟 Skeletons', 'reward_gold': 500},
    {'wave': 2, 'enemies': 100, 'type': '👹 Goblins', 'reward_gold': 1000},
    {'wave': 3, 'enemies': 200, 'type': '🐺 Werewolves', 'reward_gold': 2000},
    {'wave': 4, 'enemies': 350, 'type': '🐉 Dragons', 'reward_gold': 5000},
    {'wave': 5, 'enemies': 500, 'type': '💀 Demon Lord', 'reward_gold': 10000},
]

# Decision Events
DECISION_EVENTS = [
    {
        'id': 'merchant_offer',
        'message': '''
🧙 Ek mysterious merchant aaya hai!

💰 Option A: 1000 Gold do, 2000 Gold return guarantee
⚔️ Option B: 500 Gold aur 50 Army do, secret weapon milega
🚪 Option C: Ignore karo, kuch nahi hoga
        ''',
        'outcomes': {
            'A': {'gold': 1000, 'message': 'Merchant ne double return diya! +1000 Gold! 🎉'},
            'B': {'item': 'secret_weapon', 'message': 'Aapko Dragon Sword mila! +20% attack! 🔥'},
            'C': {'nothing': True, 'message': 'Merchant chala gaya...'}
        }
    },
    {
        'id': 'wandering_soldier',
        'message': '''
🗡 Ek bhatakta soldier mila hai!

⚔️ Option A: Apni army mein shamil karo (50 soldiers free)
💰 Option B: Bech do slave market mein (300 Gold)
🛡 Option C: Apne base ka guard banao (+defense)
        ''',
        'outcomes': {
            'A': {'infantry': 50, 'message': '50 Infantry join kiye! ⚔️'},
            'B': {'gold': 300, 'message': '300 Gold mila! 💰'},
            'C': {'defense_bonus': 0.05, 'message': 'Base defense +5%! 🛡'}
        }
    },
]

# Limited Events
LIMITED_EVENTS = {
    'double_gold_weekend': {
        'name': '💰 Double Gold Weekend',
        'description': 'Sab gold production 2x!',
        'duration_hours': 48,
        'effect': {'gold_multiplier': 2.0},
    },
    'no_defense_day': {
        'name': '🚫 No Walls Day',
        'description': 'Wall defense zero! Pure army vs army!',
        'duration_hours': 24,
        'effect': {'wall_defense_zero': True},
    },
    'sudden_war': {
        'name': '⚔️ Sudden War',
        'description': '2x XP, 2x loot from battles!',
        'duration_hours': 6,
        'effect': {'xp_multiplier': 2.0, 'loot_multiplier': 2.0},
    },
}

# World Events
WORLD_EVENTS = [
    {'type': 'treasure', 'message': '💎 Khazana mila! Sab players +500 Gold!', 'effect': {'gold': 500}},
    {'type': 'plague', 'message': '😷 Plague! Food production -50% for 6 hours!', 'effect': {'food_multiplier': 0.5, 'duration': 6}},
    {'type': 'festival', 'message': '🎉 Mahotsav! Training speed 2x for 12 hours!', 'effect': {'training_multiplier': 2.0, 'duration': 12}},
    {'type': 'invasion', 'message': '🐉 Dragon sighted! Survival event active!', 'effect': {'survival_active': True}},
]

# NPC Names for AI Bot
NPC_NAMES = [
    "Shadow King", "Dark Emperor", "Crimson Lord",
    "Ice Queen", "Fire Tyrant", "Storm Chieftain"
]

# Battle Emotes
BATTLE_EMOTES = {
    'attack': ['😈', '🔥', '💀', '⚔️', '👊'],
    'defense': ['🛡', '💪', '😤', '🧱', '✋'],
    'taunt': ['😂', '🤣', '😜', '🙃', '😏'],
    'respect': ['🫡', '👏', '💯', '🔥', '👑'],
}

# Anti-cheat
ANTI_CHEAT_RULES = {
    'spam': {'trigger': '>20 messages/minute to bot', 'action': 'warning_1'},
    'rapid_clicks': {'trigger': '>10 button clicks/5seconds', 'action': 'warning_1'},
    'resource_anomaly': {'trigger': 'Gold increase >500% in 1 hour without battles', 'action': 'flag_for_review'},
}

# Season Rewards
SEASON_REWARDS = {
    1: {'gold': 50000, 'gems': 100, 'title': 'Season Champion'},
    2: {'gold': 30000, 'gems': 50, 'title': 'Runner Up'},
    3: {'gold': 20000, 'gems': 30, 'title': 'Bronze Warrior'},
    'top_10': {'gold': 10000, 'gems': 15},
    'top_50': {'gold': 5000, 'gems': 5},
    'top_100': {'gold': 2000, 'gems': 2},
}

# Quiz Questions
QUIZ_QUESTIONS = [
    {
        'question': 'Kaunsi army sabse tez hoti hai?',
        'options': ['Infantry', 'Archers', 'Cavalry', 'Mages'],
        'correct': 2,  # Cavalry
        'reward_gold': 200,
        'reward_xp': 50,
    },
    {
        'question': 'Gold Mine ka kaam kya hai?',
        'options': ['Army train karna', 'Gold produce karna', 'Food banana', 'Defense badhana'],
        'correct': 1,
        'reward_gold': 200,
        'reward_xp': 50,
    },
    {
        'question': 'Wall se kya fayda hota hai?',
        'options': ['Attack power badhe', 'Defense damage kam ho', 'Gold jyada mile', 'Food kam kharch ho'],
        'correct': 1,
        'reward_gold': 200,
        'reward_xp': 50,
    },
    {
        'question': 'Spy mission ka cost kitna hai?',
        'options': ['100 Gold', '300 Gold', '500 Gold', '1000 Gold'],
        'correct': 1,
        'reward_gold': 200,
        'reward_xp': 50,
    },
    {
        'question': 'Energy kitne time mein regenerate hoti hai?',
        'options': ['15 min', '30 min', '1 hour', '2 hour'],
        'correct': 1,
        'reward_gold': 200,
        'reward_xp': 50,
    },
    {
        'question': 'Cavalry ka unlock condition kya hai?',
        'options': ['Barracks Lv.2', 'Barracks Lv.4', 'Barracks Lv.6', 'Town Hall Lv.5'],
        'correct': 1,
        'reward_gold': 200,
        'reward_xp': 50,
    },
    {
        'question': 'Newbie shield kitne ghante ka hota hai?',
        'options': ['12 hours', '24 hours', '48 hours', '72 hours'],
        'correct': 1,
        'reward_gold': 200,
        'reward_xp': 50,
    },
    {
        'question': 'Alliance banane mein kitna Gold lagta hai?',
        'options': ['5000', '10000', '15000', '20000'],
        'correct': 1,
        'reward_gold': 200,
        'reward_xp': 50,
    },
]

# Power calculation weights
POWER_WEIGHTS = {
    'army_multiplier': 10,
    'building_multiplier': 100,
    'level_multiplier': 500,
    'hero_multiplier': 200,
    'battle_multiplier': 50,
}

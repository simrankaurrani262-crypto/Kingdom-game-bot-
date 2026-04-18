"""
Game constants and building definitions.
"""

# Building definitions
BUILDINGS = {
    'town_hall': {
        'emoji': '🏰',
        'name': 'Town Hall',
        'hindi_name': 'Raj Mahal',
        'purpose': 'Unlocks buildings, sets kingdom level',
        'produces': None,
        'base_rate': 0,
    },
    'gold_mine': {
        'emoji': '⛏',
        'name': 'Gold Mine',
        'hindi_name': 'Sona Ki Khan',
        'purpose': 'Generates Gold/hour',
        'produces': 'gold',
        'base_rate': 100,
    },
    'farm': {
        'emoji': '🌾',
        'name': 'Farm',
        'hindi_name': 'Khet',
        'purpose': 'Generates Food/hour',
        'produces': 'food',
        'base_rate': 50,
    },
    'barracks': {
        'emoji': '🏹',
        'name': 'Barracks',
        'hindi_name': 'Senalay',
        'purpose': 'Trains Army/hour',
        'produces': 'army',
        'base_rate': 10,
    },
    'wall': {
        'emoji': '🛡',
        'name': 'Wall',
        'hindi_name': 'Deewar',
        'purpose': 'Reduces incoming damage',
        'produces': None,
        'base_rate': 0,
    },
}

# Army unit types
ARMY_UNITS = {
    'infantry': {
        'emoji': '🗡',
        'name': 'Infantry',
        'hindi_name': 'Paidal Sena',
        'attack': 10,
        'defense': 8,
        'speed': 'Slow',
        'food_per_hour': 2,
        'cost_gold': 50,
        'cost_food': 20,
        'unlock_building': None,
        'unlock_level': 1,
    },
    'archers': {
        'emoji': '🏹',
        'name': 'Archers',
        'hindi_name': 'Teerandaz',
        'attack': 12,
        'defense': 5,
        'speed': 'Medium',
        'food_per_hour': 3,
        'cost_gold': 80,
        'cost_food': 30,
        'unlock_building': 'barracks',
        'unlock_level': 2,
    },
    'cavalry': {
        'emoji': '🐎',
        'name': 'Cavalry',
        'hindi_name': 'Ghudsawar',
        'attack': 18,
        'defense': 12,
        'speed': 'Fast',
        'food_per_hour': 5,
        'cost_gold': 150,
        'cost_food': 50,
        'unlock_building': 'barracks',
        'unlock_level': 4,
    },
}

# XP required per level (exponential)
def xp_for_level(level: int) -> int:
    return int(100 * (1.5 ** (level - 1)))

# Max building level per town hall level
def max_building_level_for_town_hall(town_hall_level: int) -> int:
    return town_hall_level * 2 + 3

# Emoji flags for kingdom selection
FLAGS = [
    '🔥', '⚡', '🌊', '🌪', '🌑', '☀️', '❄️', '🍃',
    '💀', '👑', '🦁', '🐉', '🦅', '🐺', '🦊', '🐻',
    '🌹', '🍁', '🌵', '💎', '⚜️', '🏴', '🏳', '🎯',
]

# Defense rating thresholds
DEFENSE_RATINGS = [
    (0, 100, "Weak 🟡", "Kamzor"),
    (100, 300, "Moderate 🟠", "Madhyam"),
    (300, 600, "Strong 🔴", "Mazboot"),
    (600, 999999, "Unbreakable ⚫", "Abhedya"),
]

# Resource emojis
RESOURCE_EMOJIS = {
    'gold': '💰',
    'food': '🍖',
    'gems': '💎',
    'energy': '⚡',
}

# Building emojis
BUILDING_EMOJIS = {
    'town_hall': '🏰',
    'gold_mine': '⛏',
    'farm': '🌾',
    'barracks': '🏹',
    'wall': '🛡',
}

# Status indicators
STATUS_ONLINE = '🟢 Online'
STATUS_AWAY = '🟡 Idle'
STATUS_OFFLINE = '🔴 Offline'

# Map emojis
MAP_EMPTY = '⬜'
MAP_YOU = '🟩'
MAP_ALLY = '🟦'
MAP_ENEMY = '🟥'

# Time formatting
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

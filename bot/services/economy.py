"""
Economy service for Kingdom Conquest.
Handles resource production, costs, and calculations.
"""
import math
from typing import Dict, Optional
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    BASE_UPGRADE_COST_GOLD, UPGRADE_COST_MULTIPLIER,
    BASE_UPGRADE_TIME_MINUTES, UPGRADE_TIME_MULTIPLIER,
    GOLD_MINE_BASE_RATE, FARM_BASE_RATE, BARRACKS_TRAIN_RATE,
    BUILDING_MAX_LEVEL, FOOD_PER_ARMY_PER_HOUR,
    TRAINING_BATCH_SIZE, TRAINING_TIME_MINUTES, MAX_TRAINING_QUEUE
)


class EconomyService:
    """Handles all economy-related calculations."""
    
    @staticmethod
    def calculate_upgrade_cost(building_type: str, current_level: int) -> dict:
        """Calculate upgrade cost for a building."""
        base = BASE_UPGRADE_COST_GOLD
        multiplier = UPGRADE_COST_MULTIPLIER ** current_level
        
        costs = {
            'town_hall': {
                'gold': int(base * multiplier * 1.5),
                'food': int(base * multiplier * 0.5),
                'time': int(10 * (UPGRADE_TIME_MULTIPLIER ** current_level))
            },
            'gold_mine': {
                'gold': int(base * multiplier),
                'food': 0,
                'time': int(5 * (UPGRADE_TIME_MULTIPLIER ** current_level))
            },
            'farm': {
                'gold': int(base * multiplier * 0.8),
                'food': 0,
                'time': int(5 * (UPGRADE_TIME_MULTIPLIER ** current_level))
            },
            'barracks': {
                'gold': int(base * multiplier),
                'food': int(base * multiplier * 0.3),
                'time': int(8 * (UPGRADE_TIME_MULTIPLIER ** current_level))
            },
            'wall': {
                'gold': int(base * multiplier * 1.2),
                'food': int(base * multiplier * 0.4),
                'time': int(7 * (UPGRADE_TIME_MULTIPLIER ** current_level))
            },
        }
        return costs.get(building_type, {'gold': 0, 'food': 0, 'time': 0})
    
    @staticmethod
    def calculate_production_rate(building_type: str, level: int) -> int:
        """Calculate production rate per hour for a building."""
        bases = {
            'gold_mine': GOLD_MINE_BASE_RATE,
            'farm': FARM_BASE_RATE,
            'barracks': BARRACKS_TRAIN_RATE,
        }
        base = bases.get(building_type, 0)
        if base == 0:
            return 0
        return int(base * (level ** 1.2))
    
    @staticmethod
    def calculate_collectible_resources(building_type: str, level: int,
                                        last_collected: datetime) -> int:
        """Calculate resources that can be collected."""
        now = datetime.now()
        elapsed = (now - last_collected).total_seconds() / 3600  # hours
        
        rate = EconomyService.calculate_production_rate(building_type, level)
        max_storage = rate * 24  # 24 hours max storage
        
        produced = min(rate * elapsed, max_storage)
        return max(0, int(produced))
    
    @staticmethod
    def calculate_army_food_consumption(infantry: int, archers: int, cavalry: int) -> int:
        """Calculate hourly food consumption for army."""
        total = (infantry * 2) + (archers * 3) + (cavalry * 5)
        return total
    
    @staticmethod
    def calculate_training_cost(unit_type: str) -> dict:
        """Calculate cost to train a batch of units."""
        costs = {
            'infantry': {'gold': 50, 'food': 20},
            'archers': {'gold': 80, 'food': 30},
            'cavalry': {'gold': 150, 'food': 50},
        }
        return costs.get(unit_type, {'gold': 0, 'food': 0})
    
    @staticmethod
    def calculate_wall_defense_reduction(wall_level: int) -> float:
        """Calculate damage reduction from wall level."""
        reduction = wall_level * 0.03
        return min(reduction, 0.75)
    
    @staticmethod
    def calculate_kingdom_power(kingdom: dict, army: dict, buildings: list,
                                 heroes: list, battles_won: int = 0) -> int:
        """Calculate total kingdom power score."""
        army_total = army.get('infantry', 0) + army.get('archers', 0) + army.get('cavalry', 0)
        building_total = sum(b.get('level', 1) for b in buildings)
        kingdom_level = kingdom.get('level', 1)
        heroes_total = sum(h.get('level', 1) for h in heroes)
        
        power = (
            army_total * 10 +
            building_total * 100 +
            kingdom_level * 500 +
            heroes_total * 200 +
            battles_won * 50
        )
        return power
    
    @staticmethod
    def calculate_xp_for_level(level: int) -> int:
        """Calculate XP needed for next level."""
        return int(100 * (1.5 ** (level - 1)))
    
    @staticmethod
    def calculate_spy_cost() -> int:
        """Get spy mission cost."""
        from config import SPY_COST_GOLD
        return SPY_COST_GOLD
    
    @staticmethod
    def calculate_raid_cost() -> dict:
        """Get raid cost and parameters."""
        from config import RAID_ENERGY_COST, RAID_LOOT_PERCENT, RAID_ARMY_LOSS_PERCENT
        return {
            'energy': RAID_ENERGY_COST,
            'loot_percent': RAID_LOOT_PERCENT,
            'army_loss_percent': RAID_ARMY_LOSS_PERCENT,
        }
    
    @staticmethod
    def calculate_alliance_creation_cost() -> int:
        """Get alliance creation cost."""
        from config import ALLIANCE_CREATION_COST
        return ALLIANCE_CREATION_COST


class ResourceValidator:
    """Validates resource transactions."""
    
    @staticmethod
    def can_afford(gold: int, food: int, gems: int,
                   cost_gold: int = 0, cost_food: int = 0, cost_gems: int = 0) -> bool:
        """Check if player can afford a cost."""
        return gold >= cost_gold and food >= cost_food and gems >= cost_gems
    
    @staticmethod
    def has_energy(current: int, cost: int = 1) -> bool:
        """Check if player has enough energy."""
        return current >= cost
    
    @staticmethod
    def has_army_capacity(current_infantry: int, current_archers: int,
                          current_cavalry: int, max_capacity: int) -> bool:
        """Check if army has training capacity."""
        total = current_infantry + current_archers + current_cavalry
        return total < max_capacity

"""
Matchmaking service for Kingdom Conquest.
Finds fair opponents for PvP battles.
"""
import random
from typing import List, Optional, Dict

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import Database


class MatchmakingService:
    """Finds suitable PvP opponents."""
    
    def __init__(self, database: Database = None):
        self.db = database or Database()
    
    def find_opponents(self, attacker_id: int, count: int = 3) -> List[Dict]:
        """Find suitable opponents for the attacker."""
        attacker = self.db.get_kingdom(attacker_id)
        if not attacker:
            return []
        
        attacker_level = attacker.get('level', 1)
        attacker_power = attacker.get('power', 0)
        attacker_alliance = self.db.get_alliance_by_member(attacker_id)
        
        # Get all kingdoms
        all_kingdoms = self.db.get_all_kingdoms()
        
        candidates = []
        for k in all_kingdoms:
            if k['user_id'] == attacker_id:
                continue
            
            # Level check: ±2 levels
            level_diff = abs(k.get('level', 1) - attacker_level)
            if level_diff > 2:
                continue
            
            # Power check: 0.5x to 1.5x
            power = k.get('power', 0)
            if power < attacker_power * 0.3 or power > attacker_power * 1.8:
                continue
            
            # Check alliance
            if attacker_alliance:
                target_alliance = self.db.get_alliance_by_member(k['user_id'])
                if target_alliance and target_alliance['id'] == attacker_alliance['id']:
                    continue
            
            # Check newbie shield
            shield = k.get('shield_expires')
            if shield:
                from datetime import datetime
                if isinstance(shield, str):
                    shield = datetime.fromisoformat(shield.replace('Z', '+00:00'))
                if shield > datetime.now():
                    continue
            
            # Calculate distance
            distance = abs(k.get('map_x', 0) - attacker.get('map_x', 0)) + \
                      abs(k.get('map_y', 0) - attacker.get('map_y', 0))
            
            candidates.append({
                'user_id': k['user_id'],
                'kingdom_name': k.get('kingdom_name', 'Unknown'),
                'flag': k.get('flag', ''),
                'level': k.get('level', 1),
                'power': power,
                'distance': distance,
                'defense_rating': self._get_defense_rating(power),
            })
        
        # Sort by power similarity
        candidates.sort(key=lambda x: abs(x['power'] - attacker_power))
        
        return candidates[:count]
    
    def _get_defense_rating(self, power: int) -> str:
        """Get defense rating label based on power."""
        if power < 100:
            return "Weak 🟡"
        elif power < 300:
            return "Moderate 🟠"
        elif power < 600:
            return "Strong 🔴"
        else:
            return "Unbreakable ⚫"
    
    def get_dummy_opponent(self) -> Dict:
        """Generate a dummy opponent for tutorial."""
        return {
            'user_id': 0,
            'kingdom_name': 'Training Dummy',
            'flag': '🎯',
            'level': 1,
            'power': 50,
            'distance': 1,
            'defense_rating': 'Weak 🟡',
            'is_dummy': True,
        }

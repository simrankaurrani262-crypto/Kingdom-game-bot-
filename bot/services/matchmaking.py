"""
Matchmaking service for Kingdom Conquest.
Finds opponents near the player's power level.
"""
import random
from typing import Optional, Dict

from models.database import Database


class Matchmaker:
    """Finds fair opponents for PvP battles."""

    def __init__(self):
        self.db = Database()

    def get_opponent(self, user_id: int, power: int) -> Optional[Dict]:
        """Find a suitable opponent near the given power level."""
        all_kingdoms = self.db.get_all_kingdoms()
        candidates = [k for k in all_kingdoms
                      if k['user_id'] != user_id
                      and abs(k.get('power', 0) - power) < power * 0.5]
        if not candidates:
            # Fallback: pick any other kingdom
            candidates = [k for k in all_kingdoms if k['user_id'] != user_id]
        return random.choice(candidates) if candidates else None

    def get_ranked_opponents(self, user_id: int, power: int, count: int = 5) -> list:
        """Get a list of opponents sorted by power difference."""
        all_kingdoms = self.db.get_all_kingdoms()
        others = [k for k in all_kingdoms if k['user_id'] != user_id]
        others.sort(key=lambda k: abs(k.get('power', 0) - power))
        return others[:count]

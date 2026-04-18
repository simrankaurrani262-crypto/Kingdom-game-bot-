"""
Energy service for Kingdom Conquest.
Handles energy regeneration and scheduling.
"""
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MAX_ENERGY, ENERGY_REGEN_MINUTES


class EnergyService:
    """Handles energy regeneration calculations."""
    
    @staticmethod
    def calculate_current_energy(current_energy: int, last_regen: datetime) -> int:
        """Calculate current energy based on time passed."""
        if current_energy >= MAX_ENERGY:
            return MAX_ENERGY
        
        now = datetime.now()
        if isinstance(last_regen, str):
            last_regen = datetime.fromisoformat(last_regen.replace('Z', '+00:00'))
        
        minutes_passed = (now - last_regen).total_seconds() / 60
        energy_gained = int(minutes_passed / ENERGY_REGEN_MINUTES)
        
        new_energy = min(MAX_ENERGY, current_energy + energy_gained)
        return new_energy
    
    @staticmethod
    def get_energy_display(current_energy: int, last_regen: datetime) -> str:
        """Get formatted energy display string."""
        energy = EnergyService.calculate_current_energy(current_energy, last_regen)
        
        if energy >= MAX_ENERGY:
            return f"{energy}/{MAX_ENERGY} ✅ Full"
        
        now = datetime.now()
        if isinstance(last_regen, str):
            last_regen = datetime.fromisoformat(last_regen.replace('Z', '+00:00'))
        
        minutes_passed = (now - last_regen).total_seconds() / 60
        minutes_until_next = ENERGY_REGEN_MINUTES - (minutes_passed % ENERGY_REGEN_MINUTES)
        
        return f"{energy}/{MAX_ENERGY} ⏳ {int(minutes_until_next)}m"
    
    @staticmethod
    def get_next_regen_time(current_energy: int, last_regen: datetime) -> datetime:
        """Calculate when next energy point will regenerate."""
        if current_energy >= MAX_ENERGY:
            return None
        
        if isinstance(last_regen, str):
            last_regen = datetime.fromisoformat(last_regen.replace('Z', '+00:00'))
        
        now = datetime.now()
        minutes_passed = (now - last_regen).total_seconds() / 60
        minutes_until_next = ENERGY_REGEN_MINUTES - (minutes_passed % ENERGY_REGEN_MINUTES)
        
        return now + timedelta(minutes=minutes_until_next)
    
    @staticmethod
    def consume_energy(current_energy: int) -> int:
        """Consume one energy point."""
        return max(0, current_energy - 1)
    
    @staticmethod
    def refill_energy() -> int:
        """Refill energy to max (premium)."""
        return MAX_ENERGY

"""
AI Bot service for Kingdom Conquest.
Handles NPC attacks, world events, and decision events.
"""
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NPC_NAMES, WORLD_EVENTS, DECISION_EVENTS, LIMITED_EVENTS


class AIBotService:
    """AI-powered game events and NPC interactions."""
    
    NPC_NAMES = NPC_NAMES
    WORLD_EVENTS = WORLD_EVENTS
    DECISION_EVENTS = DECISION_EVENTS
    LIMITED_EVENTS = LIMITED_EVENTS
    
    @staticmethod
    def generate_npc(level: int) -> Dict:
        """Generate an NPC enemy scaled to target level."""
        name = random.choice(AIBotService.NPC_NAMES)
        army_size = int(30 + (level * 15) * random.uniform(0.8, 1.2))
        
        return {
            'name': name,
            'level': max(1, level + random.randint(-1, 2)),
            'army_size': army_size,
            'infantry': int(army_size * 0.6),
            'archers': int(army_size * 0.3),
            'cavalry': int(army_size * 0.1),
            'power': army_size * 8,
        }
    
    @staticmethod
    def generate_world_event() -> Optional[Dict]:
        """Generate a random world event."""
        if random.random() < 0.3:  # 30% chance
            event = random.choice(AIBotService.WORLD_EVENTS)
            return {
                'type': event['type'],
                'message': event['message'],
                'effect': event.get('effect', {}),
                'duration_hours': event.get('effect', {}).get('duration', 6),
            }
        return None
    
    @staticmethod
    def generate_decision_event() -> Optional[Dict]:
        """Generate a random decision event for a player."""
        if random.random() < 0.1:  # 10% chance on login
            event = random.choice(AIBotService.DECISION_EVENTS)
            return event
        return None
    
    @staticmethod
    def generate_limited_event() -> Optional[Dict]:
        """Generate a time-limited event."""
        if random.random() < 0.05:  # 5% chance
            event_key = random.choice(list(AIBotService.LIMITED_EVENTS.keys()))
            event = AIBotService.LIMITED_EVENTS[event_key]
            return {
                'key': event_key,
                'name': event['name'],
                'description': event['description'],
                'duration_hours': event['duration_hours'],
                'effect': event['effect'],
            }
        return None
    
    @staticmethod
    def get_npc_battle_result(npc: Dict, kingdom_power: int) -> Dict:
        """Simulate NPC battle and return result."""
        npc_power = npc.get('power', 100)
        
        # NPCs are slightly weaker
        effective_npc_power = npc_power * 0.8
        
        if kingdom_power > effective_npc_power * 1.2:
            # Player wins decisively
            return {
                'won': True,
                'gold_lost': 0,
                'message': f"Aapne {npc['name']} ko hara diya! 🎉",
                'damage_percent': random.uniform(0.05, 0.15),
            }
        elif kingdom_power > effective_npc_power * 0.8:
            # Close battle, player wins
            return {
                'won': True,
                'gold_lost': int(npc.get('level', 1) * 50),
                'message': f"Mushkil se jeet mile! {npc['name']} bhaga! ⚔️",
                'damage_percent': random.uniform(0.15, 0.30),
            }
        else:
            # Player loses
            return {
                'won': False,
                'gold_lost': int(npc.get('level', 1) * 100),
                'message': f"{npc['name']} ne aapko hara diya! 💀",
                'damage_percent': random.uniform(0.25, 0.40),
            }
    
    @staticmethod
    def generate_taunt() -> str:
        """Generate a random NPC taunt."""
        taunts = [
            "Tumhari army kamzor hai! 😈",
            "Main tumhara rajya loot lunga! 🔥",
            "Bach ke rehna! ⚔️",
            "Tumse na ho payega! 😂",
            "Rajkumar, taiyar ho? 👑",
        ]
        return random.choice(taunts)
    
    @staticmethod
    def generate_npc_attack_message(npc: Dict, result: Dict) -> str:
        """Generate NPC attack notification message."""
        return f"""
🤖 <b>AI ATTACK!</b>
━━━━━━━━━━━━━━
{npc['name']} ne hamla kiya!

⚔️ Army Size: {npc['army_size']}
💀 Level: {npc['level']}

{result['message']}
💰 Gold Lost: {result['gold_lost']}
━━━━━━━━━━━━━━
"""

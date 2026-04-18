"""
Battle engine for Kingdom Conquest.
Handles all combat calculations, round simulation, and report generation.
"""
import random
from typing import Dict, List, Optional
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    RANDOM_FACTOR_RANGE, WALL_DEFENSE_REDUCTION_PER_LEVEL,
    HERO_BONUS_PERCENT_PER_LEVEL, PROXIMITY_ATTACK_BONUS,
    LOOT_PERCENTAGE, WIN_BASE_XP, PARTICIPATION_XP, MAX_BATTLE_ROUNDS
)
from utils.formatters import format_number


class BattleEngine:
    """Handles battle simulation between two kingdoms."""
    
    def __init__(self, attacker_kingdom: dict, defender_kingdom: dict,
                 attacker_army: dict, defender_army: dict,
                 attacker_heroes: list = None, defender_heroes: list = None,
                 revenge_bonus: float = 0.0):
        self.attacker = attacker_kingdom
        self.defender = defender_kingdom
        self.attacker_army = attacker_army
        self.defender_army = defender_army
        self.attacker_heroes = attacker_heroes or []
        self.defender_heroes = defender_heroes or []
        self.revenge_bonus = revenge_bonus
        self.rounds = []
        self.winner = None
        self.attacker_losses = {'infantry': 0, 'archers': 0, 'cavalry': 0}
        self.defender_losses = {'infantry': 0, 'archers': 0, 'cavalry': 0}
    
    def calculate_distance(self) -> int:
        """Calculate Manhattan distance between kingdoms."""
        return abs(self.attacker.get('map_x', 0) - self.defender.get('map_x', 0)) + \
               abs(self.attacker.get('map_y', 0) - self.defender.get('map_y', 0))
    
    def calculate_hero_bonus(self, heroes: list, bonus_type: str = 'attack') -> float:
        """Calculate total hero bonus."""
        total = 0.0
        for hero in heroes:
            level = hero.get('level', 1)
            if bonus_type == 'attack':
                base = 0.15  # Base attack bonus
            elif bonus_type == 'defense':
                base = 0.05
            else:
                base = 0.10
            total += base * (1 + (level - 1) * 0.1)
        return total
    
    def calculate_army_power(self, kingdom: dict, army: dict, heroes: list,
                            is_attacker: bool = True) -> int:
        """Calculate total army power with all modifiers."""
        infantry = army.get('infantry', 0)
        archers = army.get('archers', 0)
        cavalry = army.get('cavalry', 0)
        
        infantry_power = infantry * 10
        archer_power = archers * 12 * 1.1  # Range bonus
        cavalry_power = cavalry * 18 * 1.2  # Charge bonus
        
        base_power = infantry_power + archer_power + cavalry_power
        
        if base_power <= 0:
            return 0
        
        # Hero bonuses
        hero_bonus = self.calculate_hero_bonus(heroes, 'attack')
        base_power *= (1 + hero_bonus)
        
        # Kingdom trait bonus
        trait = kingdom.get('trait', 'balanced')
        if trait == 'aggressive' and is_attacker:
            base_power *= 1.10
        elif trait == 'defensive' and not is_attacker:
            base_power *= 1.15
        
        # Proximity bonus
        distance = self.calculate_distance()
        if distance <= 2:
            base_power *= 1.10
        elif distance <= 4:
            base_power *= 1.05
        
        # Revenge bonus
        if is_attacker and self.revenge_bonus > 0:
            base_power *= (1 + self.revenge_bonus)
        
        # RNG factor
        rng = random.uniform(*RANDOM_FACTOR_RANGE)
        base_power *= rng
        
        return max(1, int(base_power))
    
    def calculate_defense_power(self) -> dict:
        """Calculate defender's effective defense."""
        wall_level = self.defender.get('wall_level', 1)
        wall_reduction = wall_level * WALL_DEFENSE_REDUCTION_PER_LEVEL
        wall_multiplier = 1 + (wall_level * 0.05)
        
        infantry = self.defender_army.get('infantry', 0)
        archers = self.defender_army.get('archers', 0)
        cavalry = self.defender_army.get('cavalry', 0)
        
        army_defense = (infantry * 8 + archers * 5 + cavalry * 12)
        
        total_defense = army_defense * wall_multiplier
        
        # Apply wall damage reduction
        damage_reduction = min(wall_reduction, 0.75)
        
        # Defender trait
        if self.defender.get('trait') == 'defensive':
            damage_reduction += 0.05
        
        # Hero defense bonuses
        hero_defense = self.calculate_hero_bonus(self.defender_heroes, 'defense')
        total_defense *= (1 + hero_defense)
        
        return {
            'total_defense': max(1, int(total_defense)),
            'damage_reduction': min(damage_reduction, 0.80),
            'wall_level': wall_level,
        }
    
    def generate_attack_action(self, round_num: int) -> str:
        """Generate flavor text for attack actions."""
        actions = [
            f"🗡 Infantry charges! ⚔️",
            f"🏹 Archers unleash volley! 🎯",
            f"🐎 Cavalry charge! 💨",
            f"⚔️ Combined assault! 🔥",
            f"🗡 Hero leads the charge! 👑",
        ]
        return f"Round {round_num} → {actions[round_num % len(actions)]}"
    
    def generate_defense_action(self, round_num: int) -> str:
        """Generate flavor text for defense actions."""
        actions = [
            f"🛡 Wall holds strong! 🧱",
            f"🏹 Defenders counter-attack! ⚔️",
            f"🐎 Cavalry intercepts! 🛡",
            f"⚔️ Desperate stand! 🔥",
            f"🛡 Shield wall formation! 🧱",
        ]
        return f"Round {round_num} → {actions[round_num % len(actions)]}"
    
    def calculate_losses(self, army: dict, remaining_hp: float, total_hp: float) -> dict:
        """Calculate army losses based on HP remaining."""
        if total_hp <= 0:
            return {'infantry': 0, 'archers': 0, 'cavalry': 0}
        
        loss_ratio = max(0, min(1, 1 - (remaining_hp / total_hp)))
        
        return {
            'infantry': int(army.get('infantry', 0) * loss_ratio * random.uniform(0.8, 1.0)),
            'archers': int(army.get('archers', 0) * loss_ratio * random.uniform(0.8, 1.0)),
            'cavalry': int(army.get('cavalry', 0) * loss_ratio * random.uniform(0.8, 1.0)),
        }
    
    def simulate_battle(self) -> dict:
        """Run full battle simulation and return report."""
        attack_power = self.calculate_army_power(
            self.attacker, self.attacker_army, self.attacker_heroes, True
        )
        defense_data = self.calculate_defense_power()
        defense_power = defense_data['total_defense']
        damage_reduction = defense_data['damage_reduction']
        
        effective_attack = int(attack_power * (1 - damage_reduction))
        
        # HP pools
        attack_hp = (self.attacker_army.get('infantry', 0) * 10 +
                     self.attacker_army.get('archers', 0) * 8 +
                     self.attacker_army.get('cavalry', 0) * 15)
        defense_hp = (self.defender_army.get('infantry', 0) * 10 +
                      self.defender_army.get('archers', 0) * 8 +
                      self.defender_army.get('cavalry', 0) * 15)
        
        initial_attack_hp = max(1, attack_hp)
        initial_defense_hp = max(1, defense_hp)
        
        round_count = min(random.randint(3, 5), MAX_BATTLE_ROUNDS)
        
        for round_num in range(1, round_count + 1):
            if defense_hp <= 0 or attack_hp <= 0:
                break
            
            # Attacker strikes
            atk_damage = int(effective_attack / round_count * random.uniform(0.8, 1.2))
            atk_damage = max(1, atk_damage)
            defense_hp -= atk_damage
            
            self.rounds.append({
                'round': round_num,
                'action': self.generate_attack_action(round_num),
                'damage': atk_damage,
                'attacker_remaining': max(0, attack_hp),
                'defender_remaining': max(0, defense_hp),
            })
            
            if defense_hp <= 0:
                break
            
            # Defender counter-strikes
            def_damage = int(defense_power / round_count * random.uniform(0.7, 1.1))
            def_damage = max(1, def_damage)
            attack_hp -= def_damage
            
            self.rounds.append({
                'round': round_num,
                'action': self.generate_defense_action(round_num),
                'damage': def_damage,
                'attacker_remaining': max(0, attack_hp),
                'defender_remaining': max(0, defense_hp),
            })
            
            if attack_hp <= 0:
                break
        
        # Determine winner
        self.winner = 'attacker' if defense_hp <= 0 or attack_hp > defense_hp else 'defender'
        
        # Calculate losses
        self.attacker_losses = self.calculate_losses(
            self.attacker_army, max(0, attack_hp), initial_attack_hp
        )
        self.defender_losses = self.calculate_losses(
            self.defender_army, max(0, defense_hp), initial_defense_hp
        )
        
        return self.generate_battle_report()
    
    def generate_battle_report(self) -> dict:
        """Format final battle report."""
        if self.winner == 'attacker':
            result_emoji = "🏆 VICTORY!"
            defender_gold = self.defender.get('gold', 0)
            gold_loot = int(defender_gold * LOOT_PERCENTAGE)
            xp_gain = WIN_BASE_XP + (self.defender.get('level', 1) * 20)
        else:
            result_emoji = "💀 DEFEAT!"
            gold_loot = 0
            xp_gain = PARTICIPATION_XP
        
        # Format rounds text
        rounds_text = ""
        for r in self.rounds:
            rounds_text += f"\n{r['action']}"
            rounds_text += f"\n   💥 Damage: {r['damage']}"
            rounds_text += f"\n   ⚔️ ATK HP: {r['attacker_remaining']} | 🛡 DEF HP: {r['defender_remaining']}"
        
        report = f"""⚔️ BATTLE REPORT
━━━━━━━━━━━━━━
{result_emoji}

⚔️ ATTACKER: {self.attacker.get('kingdom_name', 'Unknown')} {self.attacker.get('flag', '')}
🛡 DEFENDER: {self.defender.get('kingdom_name', 'Unknown')} {self.defender.get('flag', '')}

⚔️ Rounds:{rounds_text}

💀 Losses:
Attacker: 🗡-{self.attacker_losses['infantry']} 🏹-{self.attacker_losses['archers']} 🐎-{self.attacker_losses['cavalry']}
Defender: 🗡-{self.defender_losses['infantry']} 🏹-{self.defender_losses['archers']} 🐎-{self.defender_losses['cavalry']}

🏆 Rewards:
💰 +{format_number(gold_loot)} Gold
⭐ +{xp_gain} XP
━━━━━━━━━━━━━━"""
        
        return {
            'message': report,
            'winner': self.winner,
            'gold_loot': gold_loot,
            'xp_gain': xp_gain,
            'rounds': self.rounds,
            'attacker_losses': self.attacker_losses,
            'defender_losses': self.defender_losses,
        }

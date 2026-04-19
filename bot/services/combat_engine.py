"""
Combat engine for Kingdom Conquest.
Handles battle resolution, damage calculation, and loot.
"""
import random
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class CombatEngine:
    """Handles all combat calculations."""

    @staticmethod
    def calculate_battle_result(attacker_army: Dict, defender_army: Dict,
                                attacker_bonus: float = 0, defender_bonus: float = 0) -> Dict:
        """
        Calculate battle result between two armies.
        attacker_bonus/defender_bonus: percentage bonuses from heroes/skills (0.0 - 1.0)
        """
        # Calculate total forces
        attacker_total = attacker_army.get('infantry', 0) + attacker_army.get('archers', 0) + attacker_army.get('cavalry', 0)
        defender_total = defender_army.get('infantry', 0) + defender_army.get('archers', 0) + defender_army.get('cavalry', 0)

        if attacker_total <= 0 or defender_total <= 0:
            return {
                'won': attacker_total > 0,
                'attacker_losses': 0,
                'defender_losses': 0,
                'gold_stolen': 0,
                'loot_factor': 0,
                'message': 'No battle - empty army!'
            }

        # Apply bonuses
        attacker_power = attacker_total * (1 + attacker_bonus)
        defender_power = defender_total * (1 + defender_bonus)

        # Determine winner
        win_probability = attacker_power / (attacker_power + defender_power)
        won = random.random() < win_probability

        if won:
            # Attacker wins - calculate losses
            base_loss_rate = random.uniform(0.05, 0.20)
            defender_loss_rate = random.uniform(0.30, 0.60)

            attacker_losses = int(attacker_total * base_loss_rate)
            defender_losses = int(defender_total * defender_loss_rate)

            # Loot calculation
            loot_factor = random.uniform(0.10, 0.30)

            return {
                'won': True,
                'attacker_losses': attacker_losses,
                'defender_losses': defender_losses,
                'gold_stolen': 0,  # Will be calculated based on defender's gold
                'loot_factor': loot_factor,
                'message': f'Attack successful! {defender_losses} enemy troops defeated!'
            }
        else:
            # Defender wins
            base_loss_rate = random.uniform(0.20, 0.40)
            defender_loss_rate = random.uniform(0.10, 0.25)

            attacker_losses = int(attacker_total * base_loss_rate)
            defender_losses = int(defender_total * defender_loss_rate)

            return {
                'won': False,
                'attacker_losses': attacker_losses,
                'defender_losses': defender_losses,
                'gold_stolen': 0,
                'loot_factor': 0,
                'message': f'Attack failed! Lost {attacker_losses} troops!'
            }

    @staticmethod
    def calculate_loot(defender_gold: int, loot_factor: float) -> int:
        """Calculate gold stolen from defender."""
        return int(defender_gold * loot_factor)

    @staticmethod
    def calculate_wall_defense(wall_level: int) -> float:
        """Calculate defense bonus from wall level."""
        return min(0.50, wall_level * 0.05)  # Max 50% defense

    @staticmethod
    def apply_accuracy_roll(base_chance: float) -> bool:
        """Apply accuracy roll for spy/training."""
        accuracy = min(0.95, base_chance)
        return random.random() <= accuracy


def calculate_battle_result(attacker_army: Dict, defender_army: Dict,
                            attacker_bonus: float = 0, defender_bonus: float = 0) -> Dict:
    """
    Standalone function wrapper for calculate_battle_result.
    This allows both module-level and class-method usage.
    """
    return CombatEngine.calculate_battle_result(attacker_army, defender_army, attacker_bonus, defender_bonus)


def calculate_loot(defender_gold: int, loot_factor: float) -> int:
    """Standalone function for calculate_loot."""
    return CombatEngine.calculate_loot(defender_gold, loot_factor)

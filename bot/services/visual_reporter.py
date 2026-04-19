"""
Visual Report Generator for Kingdom Conquest Bot.
Integrates analytics engine with visualization and animation engines
to produce comprehensive visual reports and graphics.

Dependencies: visualizations.py, animations.py, image_renderer.py, analytics.py
"""
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from services.analytics import PlayerAnalytics, get_analytics

# Import visualization engine
try:
    from utils.visualizations import (
        generate_army_chart, generate_resource_chart, generate_battle_analytics,
        generate_building_progress, generate_leaderboard_chart, generate_power_radar,
        generate_economy_chart, generate_activity_heatmap, generate_comparison_chart,
        generate_achievement_progress, generate_quick_status, cleanup_old_charts
    )
    VISUALIZATIONS_AVAILABLE = True
except ImportError:
    VISUALIZATIONS_AVAILABLE = False

# Import animation engine
try:
    from utils.animations import (
        generate_battle_animation, generate_levelup_animation, generate_reward_animation,
        generate_spin_animation, generate_training_animation, generate_achievement_animation,
        generate_attack_alert_animation, generate_login_streak_animation, cleanup_old_animations
    )
    ANIMATIONS_AVAILABLE = True
except ImportError:
    ANIMATIONS_AVAILABLE = False

# Import image renderer
try:
    from utils.image_renderer import (
        render_hero_card, render_battle_report, render_kingdom_banner,
        render_spy_report, render_notification_card, render_leaderboard_podium
    )
    IMAGE_RENDERER_AVAILABLE = True
except ImportError:
    IMAGE_RENDERER_AVAILABLE = False


class VisualReporter:
    """
    High-level service that generates visual reports by combining
    analytics data with visualization and animation engines.
    """

    def __init__(self, db_path: str = "kingdom_bot.db"):
        self.db_path = db_path
        self.analytics = get_analytics(db_path)

    # ========================================================================
    # CHART REPORTS (Matplotlib-based)
    # ========================================================================

    def generate_army_report(self, user_id: int, infantry: int, archers: int,
                             cavalry: int, kingdom_name: str = "Your Kingdom") -> Optional[str]:
        """Generate army composition chart report."""
        if not VISUALIZATIONS_AVAILABLE:
            return None
        try:
            return generate_army_chart(infantry, archers, cavalry, kingdom_name)
        except Exception as e:
            print(f"Army report error: {e}")
            return None

    def generate_resource_report(self, user_id: int, kingdom_name: str = "Your Kingdom") -> Optional[str]:
        """Generate resource trend chart."""
        if not VISUALIZATIONS_AVAILABLE:
            return None
        try:
            trends = self.analytics.get_resource_trends(user_id, days=14)
            if len(trends) < 2:
                # Generate sample data if not enough history
                return None
            gold_history = [t['gold'] for t in trends]
            food_history = [t['food'] for t in trends]
            labels = [t['timestamp'][:10] for t in trends]
            return generate_resource_chart(gold_history, food_history, labels, kingdom_name)
        except Exception as e:
            print(f"Resource report error: {e}")
            return None

    def generate_battle_report_chart(self, user_id: int, kingdom_name: str = "Your Kingdom") -> Optional[str]:
        """Generate battle analytics chart."""
        if not VISUALIZATIONS_AVAILABLE:
            return None
        try:
            stats = self.analytics.get_battle_stats(user_id)
            return generate_battle_analytics(
                wins=stats['wins'],
                losses=stats['losses'],
                raids_won=stats['as_attacker']['wins'],
                raids_lost=stats['as_attacker']['losses'],
                total_damage_dealt=stats['total_damage_dealt'],
                total_damage_taken=stats['total_damage_taken'],
                kingdom_name=kingdom_name
            )
        except Exception as e:
            print(f"Battle report error: {e}")
            return None

    def generate_building_report(self, user_id: int, building_levels: Dict[str, int],
                                  kingdom_name: str = "Your Kingdom") -> Optional[str]:
        """Generate building progress chart."""
        if not VISUALIZATIONS_AVAILABLE:
            return None
        try:
            return generate_building_progress(building_levels, max_level=25, kingdom_name=kingdom_name)
        except Exception as e:
            print(f"Building report error: {e}")
            return None

    def generate_leaderboard_visual(self, players: List[Dict], chart_type: str = 'power',
                                     title: str = "Kingdom Leaderboard") -> Optional[str]:
        """Generate visual leaderboard chart."""
        if not VISUALIZATIONS_AVAILABLE:
            return None
        try:
            return generate_leaderboard_chart(players, chart_type, title)
        except Exception as e:
            print(f"Leaderboard visual error: {e}")
            return None

    def generate_power_profile(self, user_id: int, army: Dict, buildings: Dict,
                               heroes: List, wall_level: int,
                               kingdom_name: str = "Your Kingdom") -> Optional[str]:
        """Generate power radar chart."""
        if not VISUALIZATIONS_AVAILABLE:
            return None
        try:
            breakdown = self.analytics.calculate_power_breakdown(
                user_id, army, buildings, heroes, wall_level
            )
            return generate_power_radar(
                attack=breakdown['attack'],
                defense=breakdown['defense'],
                economy=breakdown['economy'],
                strategy=breakdown['strategy'],
                speed=breakdown['speed'],
                kingdom_name=kingdom_name
            )
        except Exception as e:
            print(f"Power profile error: {e}")
            return None

    def generate_economy_report(self, user_id: int, kingdom_name: str = "Your Kingdom") -> Optional[str]:
        """Generate economy trend chart."""
        if not VISUALIZATIONS_AVAILABLE:
            return None
        try:
            trends = self.analytics.get_resource_trends(user_id, days=14)
            if len(trends) < 2:
                return None
            production = [t['gold_production'] for t in trends]
            consumption = [max(0, t['gold_production'] - 50) for t in trends]  # Estimated
            net = [p - c for p, c in zip(production, consumption)]
            labels = [t['timestamp'][:10] for t in trends]
            return generate_economy_chart(production, consumption, net, labels, kingdom_name)
        except Exception as e:
            print(f"Economy report error: {e}")
            return None

    def generate_activity_report(self, user_id: int, kingdom_name: str = "Your Kingdom") -> Optional[str]:
        """Generate activity heatmap."""
        if not VISUALIZATIONS_AVAILABLE:
            return None
        try:
            heatmap = self.analytics.get_activity_heatmap(user_id)
            return generate_activity_heatmap(heatmap, kingdom_name)
        except Exception as e:
            print(f"Activity report error: {e}")
            return None

    def generate_comparison_report(self, player1_name: str, player1_id: int,
                                    player2_name: str, player2_id: int) -> Optional[str]:
        """Generate player comparison chart."""
        if not VISUALIZATIONS_AVAILABLE:
            return None
        try:
            comparison = self.analytics.get_comparative_stats(player1_id, player2_id)
            p1 = comparison['player1']
            p2 = comparison['player2']
            return generate_comparison_chart(
                player1_name,
                {'power': p1['power'], 'wins': p1['battles_won'],
                 'damage': p1['damage_dealt'], 'win_rate': p1['win_rate']},
                player2_name,
                {'power': p2['power'], 'wins': p2['battles_won'],
                 'damage': p2['damage_dealt'], 'win_rate': p2['win_rate']}
            )
        except Exception as e:
            print(f"Comparison report error: {e}")
            return None

    def generate_achievement_report(self, user_id: int, achievements_config: List[Dict],
                                     kingdom_name: str = "Your Kingdom") -> Optional[str]:
        """Generate achievement progress chart."""
        if not VISUALIZATIONS_AVAILABLE:
            return None
        try:
            progress = self.analytics.get_achievement_progress(user_id, achievements_config)
            return generate_achievement_progress(progress, kingdom_name)
        except Exception as e:
            print(f"Achievement report error: {e}")
            return None

    def generate_status_card(self, user_id: int, gold: int, food: int, energy: int,
                             army: int, power: int, kingdom_name: str = "Your Kingdom") -> Optional[str]:
        """Generate quick status card."""
        if not VISUALIZATIONS_AVAILABLE:
            return None
        try:
            return generate_quick_status(gold, food, energy, army, power, kingdom_name)
        except Exception as e:
            print(f"Status card error: {e}")
            return None

    # ========================================================================
    # ANIMATION REPORTS (GIF-based)
    # ========================================================================

    def generate_battle_animation(self, attacker_name: str, defender_name: str,
                                   attacker_army: int, defender_army: int,
                                   result: str = "victory") -> Optional[str]:
        """Generate battle animation GIF."""
        if not ANIMATIONS_AVAILABLE:
            return None
        try:
            return generate_battle_animation(attacker_name, defender_name,
                                             attacker_army, defender_army, result)
        except Exception as e:
            print(f"Battle animation error: {e}")
            return None

    def generate_levelup_animation(self, entity_name: str, entity_type: str = "building",
                                    old_level: int = 1, new_level: int = 2) -> Optional[str]:
        """Generate level-up animation."""
        if not ANIMATIONS_AVAILABLE:
            return None
        try:
            return generate_levelup_animation(entity_name, entity_type, old_level, new_level)
        except Exception as e:
            print(f"Levelup animation error: {e}")
            return None

    def generate_reward_animation(self, reward_type: str, amount: int,
                                   bonus_text: str = "") -> Optional[str]:
        """Generate reward collection animation."""
        if not ANIMATIONS_AVAILABLE:
            return None
        try:
            return generate_reward_animation(reward_type, amount, bonus_text)
        except Exception as e:
            print(f"Reward animation error: {e}")
            return None

    def generate_spin_animation(self, items: List[str], win_index: int) -> Optional[str]:
        """Generate spin wheel animation."""
        if not ANIMATIONS_AVAILABLE:
            return None
        try:
            return generate_spin_animation(items, win_index)
        except Exception as e:
            print(f"Spin animation error: {e}")
            return None

    def generate_training_animation(self, unit_type: str, count: int) -> Optional[str]:
        """Generate training animation."""
        if not ANIMATIONS_AVAILABLE:
            return None
        try:
            return generate_training_animation(unit_type, count)
        except Exception as e:
            print(f"Training animation error: {e}")
            return None

    def generate_achievement_unlock_animation(self, achievement_name: str,
                                               rarity: str = "common") -> Optional[str]:
        """Generate achievement unlock animation."""
        if not ANIMATIONS_AVAILABLE:
            return None
        try:
            return generate_achievement_animation(achievement_name, rarity)
        except Exception as e:
            print(f"Achievement animation error: {e}")
            return None

    def generate_attack_alert(self, attacker_name: str, attack_power: int) -> Optional[str]:
        """Generate attack alert animation."""
        if not ANIMATIONS_AVAILABLE:
            return None
        try:
            return generate_attack_alert_animation(attacker_name, attack_power)
        except Exception as e:
            print(f"Attack alert error: {e}")
            return None

    def generate_login_streak_animation(self, streak_days: int, bonus_reward: int = 0) -> Optional[str]:
        """Generate login streak animation."""
        if not ANIMATIONS_AVAILABLE:
            return None
        try:
            return generate_login_streak_animation(streak_days, bonus_reward)
        except Exception as e:
            print(f"Login streak animation error: {e}")
            return None

    # ========================================================================
    # IMAGE CARD REPORTS (PIL-based)
    # ========================================================================

    def generate_hero_card(self, hero_name: str, hero_title: str, level: int,
                           rarity: str, stats: Dict[str, int], skill_tree: Dict,
                           experience: int, exp_to_next: int,
                           image_path: Optional[str] = None,
                           theme_name: str = 'dark_kingdom') -> Optional[str]:
        """Generate hero stat card image."""
        if not IMAGE_RENDERER_AVAILABLE:
            return None
        try:
            return render_hero_card(hero_name, hero_title, level, rarity, stats,
                                    skill_tree, experience, exp_to_next, image_path, theme_name)
        except Exception as e:
            print(f"Hero card error: {e}")
            return None

    def generate_battle_report_card(self, attacker_name: str, defender_name: str,
                                     attacker_losses: Dict, defender_losses: Dict,
                                     loot_gold: int, loot_food: int, result: str,
                                     battle_rounds: int, total_damage: int) -> Optional[str]:
        """Generate battle report card image."""
        if not IMAGE_RENDERER_AVAILABLE:
            return None
        try:
            return render_battle_report(attacker_name, defender_name, attacker_losses,
                                        defender_losses, loot_gold, loot_food, result,
                                        battle_rounds, total_damage)
        except Exception as e:
            print(f"Battle report card error: {e}")
            return None

    def generate_kingdom_banner(self, kingdom_name: str, king_name: str, flag_emoji: str,
                                 power: int, gold: int, food: int, army: int,
                                 buildings: int, wins: int, rank: int) -> Optional[str]:
        """Generate kingdom banner image."""
        if not IMAGE_RENDERER_AVAILABLE:
            return None
        try:
            return render_kingdom_banner(kingdom_name, king_name, flag_emoji, power,
                                         gold, food, army, buildings, wins, rank)
        except Exception as e:
            print(f"Kingdom banner error: {e}")
            return None

    def generate_spy_report_card(self, target_name: str, intel_level: str,
                                  resources: Dict, army: Dict, buildings: Dict,
                                  defense_rating: int, risk_level: str) -> Optional[str]:
        """Generate spy report card image."""
        if not IMAGE_RENDERER_AVAILABLE:
            return None
        try:
            return render_spy_report(target_name, intel_level, resources, army,
                                     buildings, defense_rating, risk_level)
        except Exception as e:
            print(f"Spy report card error: {e}")
            return None

    def generate_notification_card(self, title: str, message: str,
                                    notif_type: str = "info",
                                    action_text: str = "") -> Optional[str]:
        """Generate notification card image."""
        if not IMAGE_RENDERER_AVAILABLE:
            return None
        try:
            return render_notification_card(title, message, notif_type, action_text)
        except Exception as e:
            print(f"Notification card error: {e}")
            return None

    def generate_leaderboard_podium_card(self, top_players: List[Dict],
                                          category: str = "power") -> Optional[str]:
        """Generate leaderboard podium image."""
        if not IMAGE_RENDERER_AVAILABLE:
            return None
        try:
            return render_leaderboard_podium(top_players, category)
        except Exception as e:
            print(f"Leaderboard podium error: {e}")
            return None

    # ========================================================================
    # COMPOSITE REPORTS (Multiple visualizations combined)
    # ========================================================================

    def generate_full_dashboard(self, user_id: int, kingdom_name: str, **kwargs) -> Dict[str, Optional[str]]:
        """
        Generate a complete visual dashboard with all available charts.
        Returns dict of report type -> filepath.
        """
        reports = {}

        # Army chart
        if 'infantry' in kwargs and 'archers' in kwargs and 'cavalry' in kwargs:
            reports['army'] = self.generate_army_report(
                user_id, kwargs['infantry'], kwargs['archers'], kwargs['cavalry'], kingdom_name
            )

        # Resource chart
        reports['resources'] = self.generate_resource_report(user_id, kingdom_name)

        # Battle analytics
        reports['battles'] = self.generate_battle_report_chart(user_id, kingdom_name)

        # Building progress
        if 'building_levels' in kwargs:
            reports['buildings'] = self.generate_building_report(
                user_id, kwargs['building_levels'], kingdom_name
            )

        # Power radar
        if all(k in kwargs for k in ['army', 'buildings', 'heroes', 'wall_level']):
            reports['power'] = self.generate_power_profile(
                user_id, kwargs['army'], kwargs['buildings'],
                kwargs['heroes'], kwargs['wall_level'], kingdom_name
            )

        # Status card
        if all(k in kwargs for k in ['gold', 'food', 'energy', 'total_army', 'power']):
            reports['status'] = self.generate_status_card(
                user_id, kwargs['gold'], kwargs['food'], kwargs['energy'],
                kwargs['total_army'], kwargs['power'], kingdom_name
            )

        return reports

    # ========================================================================
    # CLEANUP
    # ========================================================================

    @staticmethod
    def cleanup_all(max_age_hours: int = 24):
        """Clean up all generated visual files."""
        if VISUALIZATIONS_AVAILABLE:
            cleanup_old_charts(max_age_hours)
        if ANIMATIONS_AVAILABLE:
            cleanup_old_animations(max_age_hours)


# Global instance
_reporter_instance = None

def get_visual_reporter(db_path: str = "kingdom_bot.db") -> VisualReporter:
    """Get or create global visual reporter instance."""
    global _reporter_instance
    if _reporter_instance is None:
        _reporter_instance = VisualReporter(db_path)
    return _reporter_instance

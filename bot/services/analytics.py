"""
Player Analytics Engine for Kingdom Conquest Bot.
Tracks player activity, calculates statistics, generates trends and comparisons.
Provides data for visualization engine.

Dependencies: sqlite3 (built-in), datetime, collections
"""
import sqlite3
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter


class PlayerAnalytics:
    """
    Comprehensive analytics engine for tracking player behavior,
    battle patterns, resource management, and progression.
    """

    def __init__(self, db_path: str = "kingdom_bot.db"):
        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self):
        """Create analytics tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Player activity log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                details TEXT,
                gold_change INTEGER DEFAULT 0,
                food_change INTEGER DEFAULT 0,
                energy_change INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Battle history analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics_battles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attacker_id INTEGER NOT NULL,
                defender_id INTEGER NOT NULL,
                result TEXT NOT NULL,
                attacker_losses TEXT,
                defender_losses TEXT,
                gold_looted INTEGER DEFAULT 0,
                food_looted INTEGER DEFAULT 0,
                damage_dealt INTEGER DEFAULT 0,
                damage_taken INTEGER DEFAULT 0,
                rounds INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Resource history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                gold INTEGER NOT NULL,
                food INTEGER NOT NULL,
                gold_production INTEGER DEFAULT 0,
                food_production INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Daily snapshots for trend analysis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics_daily_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                snapshot_date DATE NOT NULL,
                power INTEGER DEFAULT 0,
                total_gold_earned INTEGER DEFAULT 0,
                total_food_earned INTEGER DEFAULT 0,
                battles_won INTEGER DEFAULT 0,
                battles_lost INTEGER DEFAULT 0,
                buildings_upgraded INTEGER DEFAULT 0,
                army_trained INTEGER DEFAULT 0,
                UNIQUE(user_id, snapshot_date)
            )
        ''')

        # Login streak tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics_login_streaks (
                user_id INTEGER PRIMARY KEY,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_login_date DATE,
                total_logins INTEGER DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()

    # ====================================================================
    # ACTIVITY TRACKING
    # ====================================================================

    def log_activity(self, user_id: int, activity_type: str, details: str = "",
                     gold_change: int = 0, food_change: int = 0, energy_change: int = 0):
        """Log a player activity."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analytics_activity
            (user_id, activity_type, details, gold_change, food_change, energy_change)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, activity_type, details, gold_change, food_change, energy_change))
        conn.commit()
        conn.close()

    def log_battle(self, attacker_id: int, defender_id: int, result: str,
                   attacker_losses: Dict, defender_losses: Dict,
                   gold_looted: int, food_looted: int,
                   damage_dealt: int, damage_taken: int, rounds: int):
        """Log battle analytics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analytics_battles
            (attacker_id, defender_id, result, attacker_losses, defender_losses,
             gold_looted, food_looted, damage_dealt, damage_taken, rounds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (attacker_id, defender_id, result,
              json.dumps(attacker_losses), json.dumps(defender_losses),
              gold_looted, food_looted, damage_dealt, damage_taken, rounds))
        conn.commit()
        conn.close()

    def log_resources(self, user_id: int, gold: int, food: int,
                      gold_production: int = 0, food_production: int = 0):
        """Log resource snapshot."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analytics_resources
            (user_id, gold, food, gold_production, food_production)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, gold, food, gold_production, food_production))
        conn.commit()
        conn.close()

    def log_daily_snapshot(self, user_id: int, power: int, gold_earned: int,
                           food_earned: int, battles_won: int, battles_lost: int,
                           buildings_upgraded: int, army_trained: int):
        """Log daily player snapshot for trend analysis."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT OR REPLACE INTO analytics_daily_snapshots
            (user_id, snapshot_date, power, total_gold_earned, total_food_earned,
             battles_won, battles_lost, buildings_upgraded, army_trained)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, today, power, gold_earned, food_earned,
              battles_won, battles_lost, buildings_upgraded, army_trained))
        conn.commit()
        conn.close()

    # ====================================================================
    # LOGIN STREAK MANAGEMENT
    # ====================================================================

    def record_login(self, user_id: int) -> Dict:
        """
        Record a login and update streak.
        Returns: {'streak': current_streak, 'bonus': bonus_amount, 'is_new_day': bool}
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        cursor.execute('SELECT * FROM analytics_login_streaks WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()

        if row is None:
            # First login
            cursor.execute('''
                INSERT INTO analytics_login_streaks
                (user_id, current_streak, longest_streak, last_login_date, total_logins)
                VALUES (?, 1, 1, ?, 1)
            ''', (user_id, today))
            streak = 1
            longest = 1
            is_new_day = True
        else:
            _, current_streak, longest_streak, last_login, total_logins = row

            if last_login == today:
                is_new_day = False
                streak = current_streak
            elif last_login == yesterday:
                streak = current_streak + 1
                longest = max(streak, longest_streak)
                cursor.execute('''
                    UPDATE analytics_login_streaks
                    SET current_streak = ?, longest_streak = ?,
                        last_login_date = ?, total_logins = total_logins + 1
                    WHERE user_id = ?
                ''', (streak, longest, today, user_id))
                is_new_day = True
            else:
                streak = 1
                cursor.execute('''
                    UPDATE analytics_login_streaks
                    SET current_streak = 1, last_login_date = ?,
                        total_logins = total_logins + 1
                    WHERE user_id = ?
                ''', (today, user_id))
                is_new_day = True

        conn.commit()
        conn.close()

        # Calculate bonus
        bonus = self._calculate_login_bonus(streak) if is_new_day else 0

        return {
            'streak': streak,
            'bonus': bonus,
            'is_new_day': is_new_day
        }

    def _calculate_login_bonus(self, streak: int) -> int:
        """Calculate daily login bonus based on streak."""
        base_bonus = 100
        streak_multiplier = min(streak, 7)  # Cap at 7x
        return base_bonus * streak_multiplier

    def get_login_streak(self, user_id: int) -> Dict:
        """Get current login streak info."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM analytics_login_streaks WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return {'streak': 0, 'longest': 0, 'total_logins': 0}

        return {
            'streak': row[1],
            'longest': row[2],
            'total_logins': row[4]
        }

    # ====================================================================
    # BATTLE ANALYTICS
    # ====================================================================

    def get_battle_stats(self, user_id: int, days: int = 30) -> Dict:
        """Get comprehensive battle statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        since = (datetime.now() - timedelta(days=days)).isoformat()

        # As attacker
        cursor.execute('''
            SELECT result, COUNT(*) FROM analytics_battles
            WHERE attacker_id = ? AND timestamp > ?
            GROUP BY result
        ''', (user_id, since))
        attack_results = dict(cursor.fetchall())

        # As defender
        cursor.execute('''
            SELECT result, COUNT(*) FROM analytics_battles
            WHERE defender_id = ? AND timestamp > ?
            GROUP BY result
        ''', (user_id, since))
        defense_results_raw = cursor.fetchall()
        # Invert results for defender perspective
        defense_results = {}
        for result, count in defense_results_raw:
            if result == 'victory':
                defense_results['defeat'] = count
            elif result == 'defeat':
                defense_results['victory'] = count
            else:
                defense_results['draw'] = count

        # Total damage
        cursor.execute('''
            SELECT SUM(damage_dealt), SUM(damage_taken), SUM(gold_looted), SUM(food_looted)
            FROM analytics_battles
            WHERE attacker_id = ? AND timestamp > ?
        ''', (user_id, since))
        damage_row = cursor.fetchone()

        # Favorite targets
        cursor.execute('''
            SELECT defender_id, COUNT(*) as count FROM analytics_battles
            WHERE attacker_id = ? AND timestamp > ?
            GROUP BY defender_id ORDER BY count DESC LIMIT 5
        ''', (user_id, since))
        favorite_targets = cursor.fetchall()

        # Win rate by army composition (would need army data linkage)
        # Average loot per attack
        cursor.execute('''
            SELECT AVG(gold_looted), AVG(food_looted) FROM analytics_battles
            WHERE attacker_id = ? AND result = 'victory' AND timestamp > ?
        ''', (user_id, since))
        avg_loot = cursor.fetchone()

        conn.close()

        wins = attack_results.get('victory', 0) + defense_results.get('victory', 0)
        losses = attack_results.get('defeat', 0) + defense_results.get('defeat', 0)
        draws = attack_results.get('draw', 0) + defense_results.get('draw', 0)
        total = wins + losses + draws

        return {
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'win_rate': (wins / total * 100) if total > 0 else 0,
            'total_battles': total,
            'as_attacker': {
                'wins': attack_results.get('victory', 0),
                'losses': attack_results.get('defeat', 0),
                'draws': attack_results.get('draw', 0)
            },
            'as_defender': {
                'wins': defense_results.get('victory', 0),
                'losses': defense_results.get('defeat', 0),
                'draws': defense_results.get('draw', 0)
            },
            'total_damage_dealt': damage_row[0] or 0,
            'total_damage_taken': damage_row[1] or 0,
            'total_gold_looted': damage_row[2] or 0,
            'total_food_looted': damage_row[3] or 0,
            'avg_gold_per_win': int(avg_loot[0] or 0),
            'avg_food_per_win': int(avg_loot[1] or 0),
            'favorite_targets': favorite_targets
        }

    def get_battle_trends(self, user_id: int, days: int = 14) -> List[Dict]:
        """Get daily battle win/loss trends."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT date(timestamp) as day,
                   SUM(CASE WHEN result = 'victory' THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN result = 'defeat' THEN 1 ELSE 0 END) as losses,
                   SUM(damage_dealt) as damage
            FROM analytics_battles
            WHERE attacker_id = ? AND date(timestamp) > ?
            GROUP BY date(timestamp)
            ORDER BY day
        ''', (user_id, since))

        rows = cursor.fetchall()
        conn.close()

        return [{'date': row[0], 'wins': row[1], 'losses': row[2], 'damage': row[3] or 0}
                for row in rows]

    # ====================================================================
    # RESOURCE ANALYTICS
    # ====================================================================

    def get_resource_trends(self, user_id: int, days: int = 14) -> List[Dict]:
        """Get resource history for charting."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
            SELECT timestamp, gold, food, gold_production, food_production
            FROM analytics_resources
            WHERE user_id = ? AND timestamp > ?
            ORDER BY timestamp
        ''', (user_id, since))

        rows = cursor.fetchall()
        conn.close()

        return [{
            'timestamp': row[0],
            'gold': row[1],
            'food': row[2],
            'gold_production': row[3],
            'food_production': row[4]
        } for row in rows]

    def get_resource_efficiency(self, user_id: int) -> Dict:
        """Calculate resource production efficiency."""
        trends = self.get_resource_trends(user_id, days=7)
        if len(trends) < 2:
            return {'efficiency': 0, 'gold_trend': 'stable', 'food_trend': 'stable'}

        # Calculate growth rates
        gold_first = trends[0]['gold']
        gold_last = trends[-1]['gold']
        food_first = trends[0]['food']
        food_last = trends[-1]['food']

        gold_growth = ((gold_last - gold_first) / max(gold_first, 1)) * 100
        food_growth = ((food_last - food_first) / max(food_first, 1)) * 100

        def get_trend(growth):
            if growth > 20: return 'rapid_growth'
            if growth > 5: return 'growing'
            if growth > -5: return 'stable'
            if growth > -20: return 'declining'
            return 'critical'

        avg_production = sum(t['gold_production'] for t in trends) / len(trends)

        return {
            'efficiency': min(100, int(avg_production / 1000 * 100)),
            'gold_trend': get_trend(gold_growth),
            'food_trend': get_trend(food_growth),
            'gold_growth_pct': round(gold_growth, 1),
            'food_growth_pct': round(food_growth, 1)
        }

    # ====================================================================
    # POWER & PROGRESSION ANALYTICS
    # ====================================================================

    def get_power_progression(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get power progression over time."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT snapshot_date, power,
                   total_gold_earned, total_food_earned,
                   battles_won, battles_lost,
                   buildings_upgraded, army_trained
            FROM analytics_daily_snapshots
            WHERE user_id = ? AND snapshot_date > ?
            ORDER BY snapshot_date
        ''', (user_id, since))

        rows = cursor.fetchall()
        conn.close()

        return [{
            'date': row[0],
            'power': row[1],
            'gold_earned': row[2],
            'food_earned': row[3],
            'battles_won': row[4],
            'battles_lost': row[5],
            'buildings_upgraded': row[6],
            'army_trained': row[7]
        } for row in rows]

    def calculate_power_breakdown(self, user_id: int, army: Dict, buildings: Dict,
                                   heroes: List, wall_level: int) -> Dict:
        """
        Calculate power breakdown by category.
        Returns normalized scores (0-100) for radar chart.
        """
        # Army power (0-100)
        total_army = army.get('infantry', 0) + army.get('archers', 0) + army.get('cavalry', 0)
        army_power = min(100, int(total_army / 50))

        # Defense power (0-100)
        defense_power = min(100, wall_level * 4 + int(total_army / 100))

        # Economy power (0-100) - based on building levels
        total_building_levels = sum(b.get('level', 0) for b in buildings)
        economy_power = min(100, int(total_building_levels * 2))

        # Strategy power - based on hero levels and diversity
        hero_count = len(heroes)
        avg_hero_level = sum(h.get('level', 1) for h in heroes) / max(len(heroes), 1)
        strategy_power = min(100, int(hero_count * 15 + avg_hero_level * 3))

        # Speed/aggression - based on battle history
        battle_stats = self.get_battle_stats(user_id, days=30)
        battle_rate = battle_stats['total_battles']
        speed_power = min(100, int(battle_rate * 5))

        # Normalize all to 0-100
        total_score = army_power + defense_power + economy_power + strategy_power + speed_power

        return {
            'attack': army_power,
            'defense': defense_power,
            'economy': economy_power,
            'strategy': strategy_power,
            'speed': speed_power,
            'total_score': total_score,
            'breakdown': {
                'army_contribution': f"{army.get('infantry', 0)} Infantry, {army.get('archers', 0)} Archers, {army.get('cavalry', 0)} Cavalry",
                'wall_bonus': f"Level {wall_level} Wall",
                'hero_count': f"{hero_count} Heroes (Avg Lv.{avg_hero_level:.0f})"
            }
        }

    # ====================================================================
    # ACTIVITY HEATMAP DATA
    # ====================================================================

    def get_activity_heatmap(self, user_id: int, weeks: int = 1) -> List[List[int]]:
        """
        Get 7x24 activity heatmap data.
        Returns: 7 rows (Mon-Sun) x 24 columns (hours)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        since = (datetime.now() - timedelta(weeks=weeks)).isoformat()

        cursor.execute('''
            SELECT strftime('%w', timestamp) as day_of_week,
                   strftime('%H', timestamp) as hour,
                   COUNT(*) as count
            FROM analytics_activity
            WHERE user_id = ? AND timestamp > ?
            GROUP BY day_of_week, hour
        ''', (user_id, since))

        rows = cursor.fetchall()
        conn.close()

        # Initialize 7x24 matrix (0=Sunday in SQLite, adjust to 0=Monday)
        heatmap = [[0] * 24 for _ in range(7)]
        for day_of_week, hour, count in rows:
            day_idx = (int(day_of_week) - 1) % 7  # Convert Sun=0 to Mon=0
            hour_idx = int(hour)
            heatmap[day_idx][hour_idx] = count

        return heatmap

    # ====================================================================
    # COMPARATIVE ANALYTICS
    # ====================================================================

    def get_comparative_stats(self, user_id: int, compare_with: int) -> Dict:
        """Compare stats between two players."""
        user_stats = self.get_battle_stats(user_id)
        compare_stats = self.get_battle_stats(compare_with)

        user_power = self.get_latest_power(user_id)
        compare_power = self.get_latest_power(compare_with)

        return {
            'player1': {
                'user_id': user_id,
                'battles_won': user_stats['wins'],
                'battles_lost': user_stats['losses'],
                'win_rate': user_stats['win_rate'],
                'power': user_power,
                'damage_dealt': user_stats['total_damage_dealt'],
            },
            'player2': {
                'user_id': compare_with,
                'battles_won': compare_stats['wins'],
                'battles_lost': compare_stats['losses'],
                'win_rate': compare_stats['win_rate'],
                'power': compare_power,
                'damage_dealt': compare_stats['total_damage_dealt'],
            }
        }

    def get_latest_power(self, user_id: int) -> int:
        """Get latest recorded power."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT power FROM analytics_daily_snapshots
            WHERE user_id = ? ORDER BY snapshot_date DESC LIMIT 1
        ''', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    # ====================================================================
    # ACHIEVEMENT PROGRESS
    # ====================================================================

    def get_achievement_progress(self, user_id: int, achievements_config: List[Dict]) -> List[Dict]:
        """
        Calculate achievement progress.
        achievements_config: [{'name': 'First Blood', 'type': 'kills', 'target': 10}, ...]
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get aggregated stats
        cursor.execute('''
            SELECT COUNT(*) FROM analytics_battles
            WHERE attacker_id = ? AND result = 'victory'
        ''', (user_id,))
        total_kills = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT SUM(gold_looted) FROM analytics_battles WHERE attacker_id = ?
        ''', (user_id,))
        total_loot = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT COUNT(DISTINCT defender_id) FROM analytics_battles WHERE attacker_id = ?
        ''', (user_id,))
        unique_targets = cursor.fetchone()[0] or 0

        conn.close()

        progress = []
        for ach in achievements_config:
            ach_type = ach.get('type', '')
            target = ach.get('target', 1)

            if ach_type == 'kills':
                current = total_kills
            elif ach_type == 'loot':
                current = total_loot
            elif ach_type == 'unique_targets':
                current = unique_targets
            elif ach_type == 'streak':
                streak_info = self.get_login_streak(user_id)
                current = streak_info['streak']
            else:
                current = 0

            progress.append({
                'name': ach['name'],
                'current': min(current, target),
                'target': target,
                'completed': current >= target,
                'percentage': min(100, int((current / target) * 100))
            })

        return progress

    # ====================================================================
    # CLEANUP
    # ====================================================================

    def cleanup_old_data(self, days: int = 90):
        """Remove analytics data older than specified days."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute('DELETE FROM analytics_activity WHERE timestamp < ?', (cutoff,))
        cursor.execute('DELETE FROM analytics_battles WHERE timestamp < ?', (cutoff,))
        cursor.execute('DELETE FROM analytics_resources WHERE timestamp < ?', (cutoff,))

        conn.commit()
        conn.close()


# Global instance for easy access
_analytics_instance = None

def get_analytics(db_path: str = "kingdom_bot.db") -> PlayerAnalytics:
    """Get or create global analytics instance."""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = PlayerAnalytics(db_path)
    return _analytics_instance

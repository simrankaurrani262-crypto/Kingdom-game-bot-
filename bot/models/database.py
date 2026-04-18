"""
Database module for Kingdom Conquest Bot.
Uses SQLite for simplicity (can be swapped to PostgreSQL).
"""
import sqlite3
import json
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from contextlib import contextmanager

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH


class Database:
    """Thread-safe SQLite database manager."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.local = threading.local()
        self._init_database()
    
    @property
    def conn(self):
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            self.local.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn
    
    def _init_database(self):
        """Create all tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language_code TEXT DEFAULT 'hi',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned INTEGER DEFAULT 0,
                ban_reason TEXT,
                ban_until TIMESTAMP,
                warning_count INTEGER DEFAULT 0
            )
        ''')
        
        # Kingdoms table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kingdoms (
                user_id INTEGER PRIMARY KEY,
                kingdom_name TEXT NOT NULL,
                flag TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                xp_needed INTEGER DEFAULT 100,
                gold INTEGER DEFAULT 1000,
                food INTEGER DEFAULT 500,
                gems INTEGER DEFAULT 0,
                energy INTEGER DEFAULT 10,
                max_energy INTEGER DEFAULT 10,
                last_energy_regen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                map_x INTEGER,
                map_y INTEGER,
                trait TEXT DEFAULT 'balanced',
                title TEXT,
                shield_expires TIMESTAMP,
                battles_won INTEGER DEFAULT 0,
                battles_lost INTEGER DEFAULT 0,
                battles_fought INTEGER DEFAULT 0,
                power INTEGER DEFAULT 0,
                status TEXT DEFAULT '🟢 Online',
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tutorial_step INTEGER DEFAULT 0,
                tutorial_completed INTEGER DEFAULT 0,
                skill_points INTEGER DEFAULT 0,
                skill_tree TEXT DEFAULT '{}',
                notifications_enabled INTEGER DEFAULT 1,
                active_hero TEXT,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        ''')
        
        # Buildings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS buildings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                building_type TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                max_level INTEGER DEFAULT 25,
                last_collected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                upgrade_started TIMESTAMP,
                upgrade_completes TIMESTAMP,
                is_upgrading INTEGER DEFAULT 0,
                UNIQUE(user_id, building_type),
                FOREIGN KEY (user_id) REFERENCES kingdoms(user_id)
            )
        ''')
        
        # Armies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS armies (
                user_id INTEGER PRIMARY KEY,
                infantry INTEGER DEFAULT 50,
                archers INTEGER DEFAULT 0,
                cavalry INTEGER DEFAULT 0,
                training_queue TEXT DEFAULT '[]',
                training_started TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES kingdoms(user_id)
            )
        ''')
        
        # Heroes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS heroes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                hero_key TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                is_unlocked INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 0,
                UNIQUE(user_id, hero_key),
                FOREIGN KEY (user_id) REFERENCES kingdoms(user_id)
            )
        ''')
        
        # Battles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS battles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attacker_id INTEGER NOT NULL,
                defender_id INTEGER NOT NULL,
                winner TEXT,
                gold_loot INTEGER DEFAULT 0,
                xp_gain INTEGER DEFAULT 0,
                attacker_losses TEXT,
                defender_losses TEXT,
                rounds TEXT,
                battle_report TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (attacker_id) REFERENCES kingdoms(user_id),
                FOREIGN KEY (defender_id) REFERENCES kingdoms(user_id)
            )
        ''')
        
        # Alliances table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alliances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                leader_id INTEGER NOT NULL,
                description TEXT,
                member_count INTEGER DEFAULT 1,
                max_members INTEGER DEFAULT 20,
                treasury_gold INTEGER DEFAULT 0,
                power INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (leader_id) REFERENCES kingdoms(user_id)
            )
        ''')
        
        # Alliance members table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alliance_members (
                alliance_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (alliance_id, user_id),
                FOREIGN KEY (alliance_id) REFERENCES alliances(id),
                FOREIGN KEY (user_id) REFERENCES kingdoms(user_id)
            )
        ''')
        
        # Quests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                quest_type TEXT NOT NULL,
                quest_key TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                target INTEGER NOT NULL,
                completed INTEGER DEFAULT 0,
                claimed INTEGER DEFAULT 0,
                daily INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reset_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES kingdoms(user_id)
            )
        ''')
        
        # Spy reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spy_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spy_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                report TEXT,
                intel_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (spy_id) REFERENCES kingdoms(user_id),
                FOREIGN KEY (target_id) REFERENCES kingdoms(user_id)
            )
        ''')
        
        # Bounties table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bounties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                placer_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                reward_gold INTEGER NOT NULL,
                claimed_by INTEGER,
                placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                claimed_at TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (placer_id) REFERENCES kingdoms(user_id),
                FOREIGN KEY (target_id) REFERENCES kingdoms(user_id)
            )
        ''')
        
        # Cooldowns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cooldowns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                UNIQUE(user_id, action)
            )
        ''')
        
        # Achievements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_key TEXT NOT NULL,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, achievement_key),
                FOREIGN KEY (user_id) REFERENCES kingdoms(user_id)
            )
        ''')
        
        # Leaderboard snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rank INTEGER NOT NULL,
                power INTEGER NOT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES kingdoms(user_id)
            )
        ''')
        
        # Revenge opportunities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS revenge_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                victim_id INTEGER NOT NULL,
                attacker_id INTEGER NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (victim_id) REFERENCES kingdoms(user_id),
                FOREIGN KEY (attacker_id) REFERENCES kingdoms(user_id)
            )
        ''')
        
        # Black market purchases table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS black_market_purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                price_gems INTEGER NOT NULL,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES kingdoms(user_id)
            )
        ''')
        
        # Decision events log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decision_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_id TEXT NOT NULL,
                choice TEXT NOT NULL,
                outcome TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES kingdoms(user_id)
            )
        ''')
        
        # World events log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS world_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                effect TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        # Activity log for anti-cheat
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    # User methods
    def create_user(self, telegram_id: int, username: str = None, first_name: str = None,
                    last_name: str = None, language_code: str = 'hi') -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name, language_code)
                VALUES (?, ?, ?, ?, ?)
            ''', (telegram_id, username, first_name, last_name, language_code))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_user_activity(self, telegram_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE telegram_id = ?
        ''', (telegram_id,))
        self.conn.commit()
    
    # Kingdom methods
    def create_kingdom(self, user_id: int, name: str, flag: str, map_x: int, map_y: int,
                       trait: str = 'balanced') -> bool:
        cursor = self.conn.cursor()
        try:
            shield_expires = datetime.now() + timedelta(hours=24)
            cursor.execute('''
                INSERT INTO kingdoms (user_id, kingdom_name, flag, map_x, map_y, trait, shield_expires)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, flag, map_x, map_y, trait, shield_expires))
            
            # Create default buildings
            buildings = [
                ('town_hall', 1),
                ('gold_mine', 1),
                ('farm', 1),
                ('barracks', 1),
                ('wall', 1),
            ]
            for btype, level in buildings:
                cursor.execute('''
                    INSERT INTO buildings (user_id, building_type, level)
                    VALUES (?, ?, ?)
                ''', (user_id, btype, level))
            
            # Create default army
            cursor.execute('''
                INSERT INTO armies (user_id, infantry, archers, cavalry)
                VALUES (?, ?, ?, ?)
            ''', (user_id, 50, 0, 0))
            
            # Create default heroes (only Sir Aldric unlockable)
            cursor.execute('''
                INSERT INTO heroes (user_id, hero_key, level, is_unlocked)
                VALUES (?, 'sir_aldric', 1, 1)
            ''', (user_id,))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error creating kingdom: {e}")
            return False
    
    def get_kingdom(self, user_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM kingdoms WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_kingdom(self, user_id: int, **kwargs) -> bool:
        cursor = self.conn.cursor()
        try:
            fields = []
            values = []
            for key, value in kwargs.items():
                fields.append(f"{key} = ?")
                values.append(value)
            values.append(user_id)
            cursor.execute(f'''
                UPDATE kingdoms SET {', '.join(fields)} WHERE user_id = ?
            ''', values)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating kingdom: {e}")
            return False
    
    def get_all_kingdoms(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM kingdoms')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_kingdoms_count(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM kingdoms')
        row = cursor.fetchone()
        return row['count'] if row else 0
    
    # Building methods
    def get_buildings(self, user_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM buildings WHERE user_id = ?', (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_building(self, user_id: int, building_type: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM buildings WHERE user_id = ? AND building_type = ?
        ''', (user_id, building_type))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_building(self, user_id: int, building_type: str, **kwargs) -> bool:
        cursor = self.conn.cursor()
        try:
            fields = []
            values = []
            for key, value in kwargs.items():
                fields.append(f"{key} = ?")
                values.append(value)
            values.extend([user_id, building_type])
            cursor.execute(f'''
                UPDATE buildings SET {', '.join(fields)} WHERE user_id = ? AND building_type = ?
            ''', values)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating building: {e}")
            return False
    
    # Army methods
    def get_army(self, user_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM armies WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_army(self, user_id: int, **kwargs) -> bool:
        cursor = self.conn.cursor()
        try:
            fields = []
            values = []
            for key, value in kwargs.items():
                fields.append(f"{key} = ?")
                values.append(value)
            values.append(user_id)
            cursor.execute(f'''
                UPDATE armies SET {', '.join(fields)} WHERE user_id = ?
            ''', values)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating army: {e}")
            return False
    
    # Hero methods
    def get_heroes(self, user_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM heroes WHERE user_id = ?', (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_hero(self, user_id: int, hero_key: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM heroes WHERE user_id = ? AND hero_key = ?
        ''', (user_id, hero_key))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_hero(self, user_id: int, hero_key: str, **kwargs) -> bool:
        cursor = self.conn.cursor()
        try:
            fields = []
            values = []
            for key, value in kwargs.items():
                fields.append(f"{key} = ?")
                values.append(value)
            values.extend([user_id, hero_key])
            cursor.execute(f'''
                UPDATE heroes SET {', '.join(fields)} WHERE user_id = ? AND hero_key = ?
            ''', values)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating hero: {e}")
            return False
    
    # Battle methods
    def save_battle(self, attacker_id: int, defender_id: int, winner: str,
                    gold_loot: int, xp_gain: int, attacker_losses: dict,
                    defender_losses: dict, rounds: list, report: str) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO battles (attacker_id, defender_id, winner, gold_loot, xp_gain,
                    attacker_losses, defender_losses, rounds, battle_report)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (attacker_id, defender_id, winner, gold_loot, xp_gain,
                  json.dumps(attacker_losses), json.dumps(defender_losses),
                  json.dumps(rounds), report))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving battle: {e}")
            return False
    
    def get_battle_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM battles 
            WHERE attacker_id = ? OR defender_id = ?
            ORDER BY created_at DESC LIMIT ?
        ''', (user_id, user_id, limit))
        return [dict(row) for row in cursor.fetchall()]
    
    # Alliance methods
    def create_alliance(self, name: str, leader_id: int, description: str = "") -> Optional[int]:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO alliances (name, leader_id, description)
                VALUES (?, ?, ?)
            ''', (name, leader_id, description))
            alliance_id = cursor.lastrowid
            cursor.execute('''
                INSERT INTO alliance_members (alliance_id, user_id, role)
                VALUES (?, ?, 'leader')
            ''', (alliance_id, leader_id))
            self.conn.commit()
            return alliance_id
        except Exception as e:
            print(f"Error creating alliance: {e}")
            return None
    
    def get_alliance(self, alliance_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM alliances WHERE id = ?', (alliance_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_alliance_by_member(self, user_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT a.* FROM alliances a
            JOIN alliance_members am ON a.id = am.alliance_id
            WHERE am.user_id = ?
        ''', (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_alliance_members(self, alliance_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT k.user_id, k.kingdom_name, k.flag, k.power, am.role
            FROM alliance_members am
            JOIN kingdoms k ON am.user_id = k.user_id
            WHERE am.alliance_id = ?
        ''', (alliance_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def join_alliance(self, alliance_id: int, user_id: int) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO alliance_members (alliance_id, user_id, role)
                VALUES (?, ?, 'member')
            ''', (alliance_id, user_id))
            cursor.execute('''
                UPDATE alliances SET member_count = member_count + 1 WHERE id = ?
            ''', (alliance_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error joining alliance: {e}")
            return False
    
    def leave_alliance(self, alliance_id: int, user_id: int) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                DELETE FROM alliance_members WHERE alliance_id = ? AND user_id = ?
            ''', (alliance_id, user_id))
            cursor.execute('''
                UPDATE alliances SET member_count = member_count - 1 WHERE id = ?
            ''', (alliance_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error leaving alliance: {e}")
            return False
    
    # Quest methods
    def get_quests(self, user_id: int, daily: bool = True) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM quests WHERE user_id = ? AND daily = ?
        ''', (user_id, 1 if daily else 0))
        return [dict(row) for row in cursor.fetchall()]
    
    def create_quest(self, user_id: int, quest_type: str, quest_key: str,
                     target: int, daily: bool = True) -> bool:
        cursor = self.conn.cursor()
        try:
            reset_at = None
            if daily:
                reset_at = datetime.now() + timedelta(days=1)
                reset_at = reset_at.replace(hour=0, minute=0, second=0, microsecond=0)
            cursor.execute('''
                INSERT OR IGNORE INTO quests (user_id, quest_type, quest_key, target, daily, reset_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, quest_type, quest_key, target, 1 if daily else 0, reset_at))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error creating quest: {e}")
            return False
    
    def update_quest_progress(self, quest_id: int, progress: int) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                UPDATE quests SET progress = ?, completed = CASE WHEN progress >= target THEN 1 ELSE 0 END
                WHERE id = ?
            ''', (progress, quest_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating quest: {e}")
            return False
    
    # Cooldown methods
    def set_cooldown(self, user_id: int, action: str, expires_at: datetime) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO cooldowns (user_id, action, expires_at)
                VALUES (?, ?, ?)
            ''', (user_id, action, expires_at))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error setting cooldown: {e}")
            return False
    
    def get_cooldown(self, user_id: int, action: str) -> Optional[datetime]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT expires_at FROM cooldowns WHERE user_id = ? AND action = ?
        ''', (user_id, action))
        row = cursor.fetchone()
        if row:
            expires = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00')) if isinstance(row['expires_at'], str) else row['expires_at']
            if expires > datetime.now():
                return expires
        return None
    
    def is_on_cooldown(self, user_id: int, action: str) -> bool:
        expires = self.get_cooldown(user_id, action)
        return expires is not None
    
    def get_cooldown_remaining(self, user_id: int, action: str) -> int:
        expires = self.get_cooldown(user_id, action)
        if expires:
            return max(0, int((expires - datetime.now()).total_seconds()))
        return 0
    
    # Achievement methods
    def get_achievements(self, user_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM achievements WHERE user_id = ?', (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def unlock_achievement(self, user_id: int, achievement_key: str) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO achievements (user_id, achievement_key)
                VALUES (?, ?)
            ''', (user_id, achievement_key))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error unlocking achievement: {e}")
            return False
    
    # Revenge methods
    def create_revenge_opportunity(self, victim_id: int, attacker_id: int,
                                   expires_at: datetime) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO revenge_opportunities (victim_id, attacker_id, expires_at)
                VALUES (?, ?, ?)
            ''', (victim_id, attacker_id, expires_at))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error creating revenge: {e}")
            return False
    
    def get_revenge_opportunities(self, victim_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM revenge_opportunities 
            WHERE victim_id = ? AND used = 0 AND expires_at > datetime('now')
        ''', (victim_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def use_revenge(self, revenge_id: int) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                UPDATE revenge_opportunities SET used = 1 WHERE id = ?
            ''', (revenge_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error using revenge: {e}")
            return False
    
    # Bounty methods
    def create_bounty(self, placer_id: int, target_id: int, reward_gold: int) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO bounties (placer_id, target_id, reward_gold)
                VALUES (?, ?, ?)
            ''', (placer_id, target_id, reward_gold))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error creating bounty: {e}")
            return False
    
    def get_active_bounties(self, target_id: int = None) -> List[Dict]:
        cursor = self.conn.cursor()
        if target_id:
            cursor.execute('''
                SELECT * FROM bounties WHERE target_id = ? AND is_active = 1
            ''', (target_id,))
        else:
            cursor.execute('SELECT * FROM bounties WHERE is_active = 1')
        return [dict(row) for row in cursor.fetchall()]
    
    def claim_bounty(self, bounty_id: int, claimer_id: int) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                UPDATE bounties SET claimed_by = ?, claimed_at = datetime('now'), is_active = 0
                WHERE id = ?
            ''', (claimer_id, bounty_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error claiming bounty: {e}")
            return False
    
    # Spy methods
    def save_spy_report(self, spy_id: int, target_id: int, report: str, intel_level: str) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO spy_reports (spy_id, target_id, report, intel_level)
                VALUES (?, ?, ?, ?)
            ''', (spy_id, target_id, report, intel_level))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving spy report: {e}")
            return False
    
    # World event methods
    def create_world_event(self, event_type: str, message: str, effect: dict,
                           duration_hours: int = 6) -> bool:
        cursor = self.conn.cursor()
        try:
            expires = datetime.now() + timedelta(hours=duration_hours)
            cursor.execute('''
                INSERT INTO world_events (event_type, message, effect, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (event_type, message, json.dumps(effect), expires))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error creating world event: {e}")
            return False
    
    def get_active_world_events(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM world_events WHERE expires_at > datetime('now')
            ORDER BY started_at DESC
        ''')
        return [dict(row) for row in cursor.fetchall()]
    
    # Leaderboard methods
    def update_leaderboard(self, user_id: int, power: int) -> bool:
        cursor = self.conn.cursor()
        try:
            # Get current season
            cursor.execute('SELECT MAX(season) as season FROM leaderboard_snapshots')
            row = cursor.fetchone()
            season = row['season'] if row and row['season'] else 1
            
            cursor.execute('''
                INSERT OR REPLACE INTO leaderboard_snapshots (season, user_id, rank, power, recorded_at)
                VALUES (?, ?, 
                    (SELECT COUNT(*) + 1 FROM leaderboard_snapshots WHERE season = ? AND power > ?),
                    ?, datetime('now'))
            ''', (season, user_id, season, power, power))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating leaderboard: {e}")
            return False
    
    def get_leaderboard(self, limit: int = 50) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT ls.*, k.kingdom_name, k.flag, k.battles_won
            FROM leaderboard_snapshots ls
            JOIN kingdoms k ON ls.user_id = k.user_id
            ORDER BY ls.power DESC
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    # Admin methods
    def ban_user(self, telegram_id: int, reason: str = None, days: int = None) -> bool:
        cursor = self.conn.cursor()
        try:
            ban_until = None
            if days:
                ban_until = datetime.now() + timedelta(days=days)
            cursor.execute('''
                UPDATE users SET is_banned = 1, ban_reason = ?, ban_until = ?
                WHERE telegram_id = ?
            ''', (reason, ban_until, telegram_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error banning user: {e}")
            return False
    
    def unban_user(self, telegram_id: int) -> bool:
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                UPDATE users SET is_banned = 0, ban_reason = NULL, ban_until = NULL
                WHERE telegram_id = ?
            ''', (telegram_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error unbanning user: {e}")
            return False
    
    def get_all_users(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        return [dict(row) for row in cursor.fetchall()]
    
    # Activity log for anti-cheat
    def log_activity(self, user_id: int, action: str, details: str = None):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO activity_log (user_id, action, details)
                VALUES (?, ?, ?)
            ''', (user_id, action, details))
            self.conn.commit()
        except Exception as e:
            print(f"Error logging activity: {e}")
    
    def get_recent_activity(self, user_id: int, minutes: int = 5) -> int:
        cursor = self.conn.cursor()
        since = datetime.now() - timedelta(minutes=minutes)
        cursor.execute('''
            SELECT COUNT(*) as count FROM activity_log 
            WHERE user_id = ? AND created_at > ?
        ''', (user_id, since))
        row = cursor.fetchone()
        return row['count'] if row else 0
    
    # Stats for admin
    def get_stats(self) -> Dict:
        cursor = self.conn.cursor()
        stats = {}
        cursor.execute('SELECT COUNT(*) as c FROM users')
        stats['total_users'] = cursor.fetchone()['c']
        cursor.execute('SELECT COUNT(*) as c FROM kingdoms')
        stats['total_kingdoms'] = cursor.fetchone()['c']
        cursor.execute('SELECT COUNT(*) as c FROM battles')
        stats['total_battles'] = cursor.fetchone()['c']
        cursor.execute('SELECT COUNT(*) as c FROM alliances')
        stats['total_alliances'] = cursor.fetchone()['c']
        cursor.execute('SELECT SUM(gold) as s FROM kingdoms')
        row = cursor.fetchone()
        stats['total_gold'] = row['s'] if row['s'] else 0
        return stats


# Global database instance
db = Database()


def get_db() -> Database:
    return db

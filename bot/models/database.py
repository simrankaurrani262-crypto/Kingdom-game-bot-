"""
Database layer for Kingdom Conquest.
SQLite with proper indexing, JSON storage for complex types,
and connection handling for async Telegram bot.
"""
import sqlite3
import json
import os
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'kingdom_data.db')


class Database:
    """Thread-safe SQLite database with Row factory."""

    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._ensure_tables()

    # ────────────────────── SCHEMA ──────────────────────

    def _ensure_tables(self):
        tables = [
            '''CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                banned INTEGER DEFAULT 0,
                warning_count INTEGER DEFAULT 0,
                is_ai INTEGER DEFAULT 0
            )''',
            '''CREATE TABLE IF NOT EXISTS kingdoms (
                user_id INTEGER PRIMARY KEY,
                kingdom_name TEXT NOT NULL,
                flag TEXT,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                gold INTEGER DEFAULT 500,
                food INTEGER DEFAULT 200,
                gems INTEGER DEFAULT 0,
                energy INTEGER DEFAULT 10,
                max_energy INTEGER DEFAULT 10,
                last_energy_regen TIMESTAMP,
                power INTEGER DEFAULT 0,
                map_x INTEGER,
                map_y INTEGER,
                status TEXT DEFAULT 'Online',
                shield_expires TEXT,
                active_hero TEXT,
                skill_points INTEGER DEFAULT 0,
                last_login TIMESTAMP,
                login_streak INTEGER DEFAULT 0,
                battles_won INTEGER DEFAULT 0,
                battles_lost INTEGER DEFAULT 0,
                battles_fought INTEGER DEFAULT 0,
                notifications_enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS buildings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                building_type TEXT,
                level INTEGER DEFAULT 1,
                is_upgrading INTEGER DEFAULT 0,
                upgrade_started TIMESTAMP,
                upgrade_completes TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS army (
                user_id INTEGER PRIMARY KEY,
                infantry INTEGER DEFAULT 0,
                archers INTEGER DEFAULT 0,
                cavalry INTEGER DEFAULT 0,
                training_infantry INTEGER DEFAULT 0,
                training_archers INTEGER DEFAULT 0,
                training_cavalry INTEGER DEFAULT 0
            )''',
            '''CREATE TABLE IF NOT EXISTS heroes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                hero_key TEXT,
                level INTEGER DEFAULT 1,
                is_unlocked INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 0
            )''',
            '''CREATE TABLE IF NOT EXISTS battles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attacker_id INTEGER,
                defender_id INTEGER,
                result TEXT,
                gold_stolen INTEGER DEFAULT 0,
                attacker_losses INTEGER DEFAULT 0,
                defender_losses INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS spy_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spy_id INTEGER,
                target_id INTEGER,
                report_text TEXT,
                intel_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS alliances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                leader_id INTEGER,
                max_members INTEGER DEFAULT 20,
                power INTEGER DEFAULT 0,
                treasury_gold INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS alliance_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alliance_id INTEGER,
                user_id INTEGER,
                role TEXT DEFAULT 'member'
            )''',
            '''CREATE TABLE IF NOT EXISTS cooldowns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action_type TEXT,
                expires_at TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                achievement_key TEXT,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS leaderboard (
                user_id INTEGER PRIMARY KEY,
                kingdom_name TEXT,
                power INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS decision_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_id TEXT,
                choice TEXT,
                outcome TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS world_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                message TEXT,
                effect TEXT,
                duration_hours INTEGER,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                quest_type TEXT,
                quest_key TEXT,
                target INTEGER DEFAULT 1,
                progress INTEGER DEFAULT 0,
                completed INTEGER DEFAULT 0,
                claimed INTEGER DEFAULT 0,
                daily INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS bounties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER,
                target_id INTEGER,
                reward_gold INTEGER,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
        ]
        for t in tables:
            self.conn.execute(t)
        # Create indexes for performance
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_buildings_user ON buildings(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_battles_attacker ON battles(attacker_id)',
            'CREATE INDEX IF NOT EXISTS idx_battles_defender ON battles(defender_id)',
            'CREATE INDEX IF NOT EXISTS idx_cooldowns_user ON cooldowns(user_id_id, action_type)',
            'CREATE INDEX IF NOT EXISTS idx_alliance_members ON alliance_members(alliance_id)',
            'CREATE INDEX IF NOT EXISTS idx_achievements_user ON achievements(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_quests_user ON quests(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_spy_reports ON spy_reports(spy_id)',
            'CREATE INDEX IF NOT EXISTS idx_bounties ON bounties(target_id)',
        ]
        for idx in indexes:
            try:
                self.conn.execute(idx)
            except sqlite3.OperationalError:
                pass
        self.conn.commit()

    # ────────────────────── USERS ──────────────────────

    def register_user(self, telegram_id: int, username: str, first_name: str, last_name: str):
        c = self.conn.cursor()
        c.execute(
            'INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
            (telegram_id, username, first_name, last_name)
        )
        self.conn.commit()

    def get_user(self, telegram_id: int) -> Optional[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        r = c.fetchone()
        return dict(r) if r else None

    def get_all_users(self) -> List[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM users')
        return [dict(r) for r in c.fetchall()]

    # ────────────────────── KINGDOMS ──────────────────────

    def create_kingdom(self, user_id: int, name: str, flag: str, map_x: int, map_y: int):
        c = self.conn.cursor()
        c.execute(
            'INSERT OR REPLACE INTO kingdoms (user_id, kingdom_name, flag, map_x, map_y, last_login, last_energy_regen) VALUES (?, ?, ?, ?, ?, datetime("now"), datetime("now"))',
            (user_id, name, flag, map_x, map_y)
        )
        self.conn.commit()

    def get_kingdom(self, user_id: int) -> Optional[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM kingdoms WHERE user_id = ?', (user_id,))
        r = c.fetchone()
        return dict(r) if r else None

    def get_kingdom_by_name(self, name: str) -> Optional[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM kingdoms WHERE kingdom_name = ?', (name,))
        r = c.fetchone()
        return dict(r) if r else None

    def get_all_kingdoms(self) -> List[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM kingdoms')
        return [dict(r) for r in c.fetchall()]

    def update_kingdom(self, user_id: int, **kwargs):
        """Update kingdom fields. Only allowed columns can be updated."""
        ALLOWED_COLUMNS = {
            'kingdom_name', 'flag', 'level', 'xp', 'gold', 'food', 'gems',
            'energy', 'max_energy', 'last_energy_regen', 'power', 'map_x',
            'map_y', 'status', 'shield_expires', 'active_hero', 'skill_points',
            'last_login', 'login_streak', 'battles_won', 'battles_lost',
            'battles_fought', 'notifications_enabled'
        }
        # Handle datetime fields - convert to ISO format string for SQLite
        datetime_fields = {'last_energy_regen', 'shield_expires', 'last_login'}
        
        columns = []
        values = []
        for k, v in kwargs.items():
            if k in ALLOWED_COLUMNS:
                if k in datetime_fields and isinstance(v, datetime):
                    v = v.isoformat()
                columns.append(f"{k} = ?")
                values.append(v)
        if not columns:
            return
        values.append(user_id)
        c = self.conn.cursor()
        c.execute(f"UPDATE kingdoms SET {', '.join(columns)} WHERE user_id = ?", values)
        self.conn.commit()

    def delete_kingdom(self, user_id: int):
        c = self.conn.cursor()
        c.execute('DELETE FROM kingdoms WHERE user_id = ?', (user_id,))
        self.conn.commit()

    # ────────────────────── BUILDINGS ──────────────────────

    def add_building(self, user_id: int, building_type: str):
        c = self.conn.cursor()
        c.execute(
            'INSERT OR IGNORE INTO buildings (user_id, building_type, level, is_upgrading) VALUES (?, ?, 1, 0)',
            (user_id, building_type)
        )
        self.conn.commit()

    def get_buildings(self, user_id: int) -> List[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM buildings WHERE user_id = ?', (user_id,))
        return [dict(r) for r in c.fetchall()]

    def get_building(self, user_id: int, building_type: str) -> Optional[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM buildings WHERE user_id = ? AND building_type = ?', (user_id, building_type))
        r = c.fetchone()
        return dict(r) if r else None

    def update_building(self, user_id: int, building_type: str, **kwargs):
        ALLOWED = {'level', 'is_upgrading', 'upgrade_started', 'upgrade_completes'}
        columns = []
        values = []
        for k, v in kwargs.items():
            if k in ALLOWED:
                if k in {'upgrade_started', 'upgrade_completes'} and isinstance(v, datetime):
                    v = v.isoformat()
                columns.append(f"{k} = ?")
                values.append(v)
        if not columns:
            return
        values.extend([user_id, building_type])
        c = self.conn.cursor()
        c.execute(f"UPDATE buildings SET {', '.join(columns)} WHERE user_id = ? AND building_type = ?", values)
        self.conn.commit()

    # ────────────────────── ARMY ──────────────────────

    def create_army(self, user_id: int):
        c = self.conn.cursor()
        c.execute('INSERT OR IGNORE INTO army (user_id) VALUES (?)', (user_id,))
        self.conn.commit()

    def get_army(self, user_id: int) -> Optional[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM army WHERE user_id = ?', (user_id,))
        r = c.fetchone()
        return dict(r) if r else None

    def update_army(self, user_id: int, **kwargs):
        ALLOWED = {'infantry', 'archers', 'cavalry', 'training_infantry', 'training_archers', 'training_cavalry'}
        columns = []
        values = []
        for k, v in kwargs.items():
            if k in ALLOWED:
                columns.append(f"{k} = ?")
                values.append(v)
        if not columns:
            return
        values.append(user_id)
        c = self.conn.cursor()
        c.execute(f"UPDATE army SET {', '.join(columns)} WHERE user_id = ?", values)
        self.conn.commit()

    # ────────────────────── COOLDOWNS ──────────────────────

    def get_cooldown_remaining(self, user_id: int, action: str) -> int:
        c = self.conn.cursor()
        c.execute('SELECT expires_at FROM cooldowns WHERE user_id = ? AND action_type = ?', (user_id, action))
        r = c.fetchone()
        if not r:
            return 0
        expires_at = r['expires_at']
        if isinstance(expires_at, str):
            try:
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return 0
        remaining = int((expires_at - datetime.now()).total_seconds())
        return max(0, remaining)

    def set_cooldown(self, user_id: int, action: str, expires_at):
        """Set cooldown expiry. expires_at can be datetime or string."""
        if isinstance(expires_at, datetime):
            expires_str = expires_at.isoformat()
        else:
            expires_str = str(expires_at)
        c = self.conn.cursor()
        c.execute(
            'INSERT OR REPLACE INTO cooldowns (user_id, action_type, expires_at) VALUES (?, ?, ?)',
            (user_id, action, expires_str)
        )
        self.conn.commit()

    # ────────────────────── BATTLES ──────────────────────

    def log_battle(self, attacker_id: int, defender_id: int, result: str,
                   gold_stolen: int = 0, attacker_losses: int = 0, defender_losses: int = 0):
        c = self.conn.cursor()
        c.execute(
            'INSERT INTO battles (attacker_id, defender_id, result, gold_stolen, attacker_losses, defender_losses) VALUES (?, ?, ?, ?, ?, ?)',
            (attacker_id, defender_id, result, gold_stolen, attacker_losses, defender_losses)
        )
        self.conn.commit()

    # ────────────────────── HEROES ──────────────────────

    def get_heroes(self, user_id: int) -> List[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM heroes WHERE user_id = ?', (user_id,))
        return [dict(r) for r in c.fetchall()]

    def get_hero(self, user_id: int, hero_key: str) -> Optional[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM heroes WHERE user_id = ? AND hero_key = ?', (user_id, hero_key))
        r = c.fetchone()
        return dict(r) if r else None

    def update_hero(self, user_id: int, hero_key: str, **kwargs):
        ALLOWED = {'level', 'is_unlocked', 'is_active'}
        columns = []
        values = []
        for k, v in kwargs.items():
            if k in ALLOWED:
                columns.append(f"{k} = ?")
                values.append(v)
        if not columns:
            return
        values.extend([user_id, hero_key])
        c = self.conn.cursor()
        c.execute(f"UPDATE heroes SET {', '.join(columns)} WHERE user_id = ? AND hero_key = ?", values)
        self.conn.commit()

    # ────────────────────── ALLIANCES ──────────────────────

    def create_alliance(self, name: str, leader_id: int) -> int:
        c = self.conn.cursor()
        c.execute('INSERT INTO alliances (name, leader_id) VALUES (?, ?)', (name, leader_id))
        alliance_id = c.lastrowid
        c.execute('INSERT INTO alliance_members (alliance_id, user_id, role) VALUES (?, ?, "leader")', (alliance_id, leader_id))
        self.conn.commit()
        return alliance_id

    def get_alliance(self, alliance_id: int) -> Optional[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM alliances WHERE id = ?', (alliance_id,))
        r = c.fetchone()
        if not r:
            return None
        alliance = dict(r)
        # Get member count
        c.execute('SELECT COUNT(*) as count FROM alliance_members WHERE alliance_id = ?', (alliance_id,))
        count = c.fetchone()
        alliance['member_count'] = count['count'] if count else 0
        return alliance

    def get_alliance_by_member(self, user_id: int) -> Optional[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT alliance_id FROM alliance_members WHERE user_id = ?', (user_id,))
        r = c.fetchone()
        if r:
            return self.get_alliance(r['alliance_id'])
        return None

    def join_alliance(self, alliance_id: int, user_id: int) -> bool:
        c = self.conn.cursor()
        c.execute('SELECT COUNT(*) as count FROM alliance_members WHERE alliance_id = ?', (alliance_id,))
        count = c.fetchone()['count']
        c.execute('SELECT max_members FROM alliances WHERE id = ?', (alliance_id,))
        max_m = c.fetchone()
        if not max_m or count >= max_m['max_members']:
            return False
        c.execute('INSERT OR IGNORE INTO alliance_members (alliance_id, user_id) VALUES (?, ?)', (alliance_id, user_id))
        self.conn.commit()
        return True

    def leave_alliance(self, alliance_id: int, user_id: int):
        c = self.conn.cursor()
        c.execute('DELETE FROM alliance_members WHERE alliance_id = ? AND user_id = ?', (alliance_id, user_id))
        self.conn.commit()

    def get_alliance_members(self, alliance_id: int) -> List[Dict]:
        c = self.conn.cursor()
        c.execute('''
            SELECT a.*, k.kingdom_name, k.flag, k.power 
            FROM alliance_members a 
            LEFT JOIN kingdoms k ON a.user_id = k.user_id 
            WHERE a.alliance_id = ?
        ''', (alliance_id,))
        return [dict(r) for r in c.fetchall()]

    # ────────────────────── ACHIEVEMENTS ──────────────────────

    def unlock_achievement(self, user_id: int, key: str):
        c = self.conn.cursor()
        c.execute('INSERT OR IGNORE INTO achievements (user_id, achievement_key) VALUES (?, ?)', (user_id, key))
        self.conn.commit()

    def get_achievements(self, user_id: int) -> List[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM achievements WHERE user_id = ?', (user_id,))
        return [dict(r) for r in c.fetchall()]

    # ────────────────────── LEADERBOARD ──────────────────────

    def update_leaderboard(self, user_id: int, power: int):
        c = self.conn.cursor()
        c.execute(
            'INSERT OR REPLACE INTO leaderboard (user_id, power, updated_at) VALUES (?, ?, datetime("now"))',
            (user_id, power)
        )
        self.conn.commit()

    # ────────────────────── WORLD EVENTS ──────────────────────

    def create_world_event(self, event_type: str, message: str, effect: dict, duration_hours: int):
        """Create a world event. effect should be a dict (will be JSON-serialized)."""
        c = self.conn.cursor()
        expires = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
        c.execute(
            'INSERT INTO world_events (event_type, message, effect, duration_hours, expires_at) VALUES (?, ?, ?, ?, ?)',
            (event_type, message, json.dumps(effect), duration_hours, expires)
        )
        self.conn.commit()

    def get_active_world_events(self) -> List[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM world_events WHERE expires_at > datetime("now") ORDER BY started_at DESC')
        events = []
        for r in c.fetchall():
            evt = dict(r)
            # Parse JSON effect back to dict
            if evt.get('effect'):
                try:
                    evt['effect'] = json.loads(evt['effect'])
                except (json.JSONDecodeError, TypeError):
                    evt['effect'] = {}
            events.append(evt)
        return events

    # ────────────────────── QUESTS ──────────────────────

    def create_quest(self, user_id: int, quest_type: str, quest_key: str, target: int, daily: bool = True):
        c = self.conn.cursor()
        c.execute(
            'INSERT INTO quests (user_id, quest_type, quest_key, target, daily) VALUES (?, ?, ?, ?, ?)',
            (user_id, quest_type, quest_key, target, 1 if daily else 0)
        )
        self.conn.commit()

    def get_quests(self, user_id: int, daily: bool = True) -> List[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM quests WHERE user_id = ? AND daily = ?', (user_id, 1 if daily else 0))
        return [dict(r) for r in c.fetchall()]

    def update_quest_progress(self, quest_id: int, progress: int):
        """Update quest progress and auto-mark as completed if target reached."""
        c = self.conn.cursor()
        # Get current quest data
        c.execute('SELECT target, completed FROM quests WHERE id = ?', (quest_id,))
        r = c.fetchone()
        if not r:
            return
        target = r['target']
        completed = 1 if progress >= target else r['completed']
        c.execute(
            'UPDATE quests SET progress = ?, completed = ? WHERE id = ?',
            (progress, completed, quest_id)
        )
        self.conn.commit()

    def mark_quest_claimed(self, quest_id: int):
        """Mark a quest as claimed."""
        c = self.conn.cursor()
        c.execute('UPDATE quests SET claimed = 1 WHERE id = ?', (quest_id,))
        self.conn.commit()

    # ────────────────────── SPY REPORTS ──────────────────────

    def save_spy_report(self, user_id: int, target_id: int, report_text: str, intel_level: str = 'basic'):
        """Save a spy report to the database."""
        c = self.conn.cursor()
        c.execute(
            'INSERT INTO spy_reports (spy_id, target_id, report_text, intel_level) VALUES (?, ?, ?, ?)',
            (user_id, target_id, report_text, intel_level)
        )
        self.conn.commit()

    # ────────────────────── BOUNTIES ──────────────────────

    def create_bounty(self, creator_id: int, target_id: int, reward_gold: int):
        c = self.conn.cursor()
        c.execute(
            'INSERT INTO bounties (creator_id, target_id, reward_gold) VALUES (?, ?, ?)',
            (creator_id, target_id, reward_gold)
        )
        self.conn.commit()

    def get_active_bounties(self) -> List[Dict]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM bounties WHERE active = 1 ORDER BY created_at DESC')
        return [dict(r) for r in c.fetchall()]

    # ────────────────────── ADMIN ──────────────────────

    def ban_user(self, user_id: int, reason: str, days: int):
        c = self.conn.cursor()
        c.execute('UPDATE users SET banned = 1 WHERE telegram_id = ?', (user_id,))
        self.conn.commit()

    def unban_user(self, user_id: int):
        c = self.conn.cursor()
        c.execute('UPDATE users SET banned = 0 WHERE telegram_id = ?', (user_id,))
        self.conn.commit()

    def get_stats(self) -> Dict:
        c = self.conn.cursor()
        stats = {}
        c.execute('SELECT COUNT(*) as c FROM users')
        stats['total_users'] = c.fetchone()['c']
        c.execute('SELECT COUNT(*) as c FROM kingdoms')
        stats['total_kingdoms'] = c.fetchone()['c']
        c.execute('SELECT COUNT(*) as c FROM battles')
        stats['total_battles'] = c.fetchone()['c']
        c.execute('SELECT COUNT(*) as c FROM alliances')
        stats['total_alliances'] = c.fetchone()['c']
        c.execute('SELECT COALESCE(SUM(gold), 0) as s FROM kingdoms')
        stats['total_gold'] = c.fetchone()['s']
        return stats

    def close(self):
        self.conn.close()

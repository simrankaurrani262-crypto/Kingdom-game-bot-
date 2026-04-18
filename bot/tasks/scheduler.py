"""
Background task scheduler for Kingdom Conquest.
Handles energy regeneration, building completion, food consumption,
world events, and other time-based game mechanics.
"""
import asyncio
import logging
from datetime import datetime, timedelta
import random

from telegram import Bot

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import Database
from services.energy_service import EnergyService
from services.economy import EconomyService
from services.ai_bot import AIBotService
from config import (
    MAX_ENERGY, ENERGY_REGEN_MINUTES, FOOD_PER_ARMY_PER_HOUR,
    WORLD_EVENTS
)

logger = logging.getLogger(__name__)
db = Database()
energy_service = EnergyService()
economy = EconomyService()
ai_bot = AIBotService()


class GameScheduler:
    """Manages all background game tasks."""
    
    def __init__(self, bot: Bot = None):
        self.bot = bot
        self.running = False
        self.tasks = []
    
    def set_bot(self, bot: Bot):
        self.bot = bot
    
    async def start(self):
        """Start all background tasks."""
        if self.running:
            return
        self.running = True
        logger.info("Starting game scheduler...")
        
        self.tasks = [
            asyncio.create_task(self._energy_regen_loop()),
            asyncio.create_task(self._building_completion_loop()),
            asyncio.create_task(self._food_consumption_loop()),
            asyncio.create_task(self._world_event_loop()),
            asyncio.create_task(self._shield_expiry_loop()),
        ]
    
    async def stop(self):
        """Stop all background tasks."""
        self.running = False
        for task in self.tasks:
            task.cancel()
        logger.info("Game scheduler stopped.")
    
    async def _energy_regen_loop(self):
        """Regenerate energy for all kingdoms every minute."""
        while self.running:
            try:
                kingdoms = db.get_all_kingdoms()
                for kingdom in kingdoms:
                    user_id = kingdom['user_id']
                    current_energy = kingdom.get('energy', MAX_ENERGY)
                    
                    if current_energy >= MAX_ENERGY:
                        continue
                    
                    last_regen = kingdom.get('last_energy_regen')
                    if isinstance(last_regen, str):
                        last_regen = datetime.fromisoformat(last_regen.replace('Z', '+00:00'))
                    
                    minutes_passed = (datetime.now() - last_regen).total_seconds() / 60
                    
                    if minutes_passed >= ENERGY_REGEN_MINUTES:
                        new_energy = min(MAX_ENERGY, current_energy + 1)
                        db.update_kingdom(
                            user_id,
                            energy=new_energy,
                            last_energy_regen=datetime.now()
                        )
                        
                        # Notify if energy full
                        if new_energy == MAX_ENERGY and kingdom.get('notifications_enabled', 1):
                            await self._notify(user_id, 
                                "⚡ <b>Energy Full!</b>\n\n"
                                "Aapki energy poori ho gayi hai!\n"
                                "Attack karne ke liye taiyaar! ⚔️")
                
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Energy regen error: {e}")
                await asyncio.sleep(60)
    
    async def _building_completion_loop(self):
        """Check and complete building upgrades."""
        while self.running:
            try:
                cursor = db.conn.cursor()
                cursor.execute('''
                    SELECT * FROM buildings 
                    WHERE is_upgrading = 1 
                    AND upgrade_completes <= datetime('now')
                ''')
                completed = [dict(r) for r in cursor.fetchall()]
                
                for building in completed:
                    user_id = building['user_id']
                    btype = building['building_type']
                    new_level = building['level'] + 1
                    
                    db.update_building(
                        user_id, btype,
                        level=new_level,
                        is_upgrading=0,
                        upgrade_started=None,
                        upgrade_completes=None
                    )
                    
                    building_name = btype.replace('_', ' ').title()
                    kingdom = db.get_kingdom(user_id)
                    
                    if kingdom and kingdom.get('notifications_enabled', 1):
                        await self._notify(user_id,
                            f"✅ <b>Building Complete!</b>\n\n"
                            f"🏗 {building_name} is now <b>Level {new_level}</b>!\n\n"
                            f"Production upgraded! 🎉")
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Building completion error: {e}")
                await asyncio.sleep(30)
    
    async def _food_consumption_loop(self):
        """Process hourly food consumption and starvation."""
        while self.running:
            try:
                kingdoms = db.get_all_kingdoms()
                
                for kingdom in kingdoms:
                    user_id = kingdom['user_id']
                    army = db.get_army(user_id)
                    
                    if not army:
                        continue
                    
                    infantry = army.get('infantry', 0)
                    archers = army.get('archers', 0)
                    cavalry = army.get('cavalry', 0)
                    
                    # Calculate food consumption
                    consumption = economy.calculate_army_food_consumption(
                        infantry, archers, cavalry
                    )
                    
                    current_food = kingdom.get('food', 0)
                    
                    if consumption <= 0:
                        continue
                    
                    if current_food >= consumption:
                        # Normal consumption
                        db.update_kingdom(user_id, food=current_food - consumption)
                    else:
                        # Starvation - army deserts
                        food_deficit = consumption - current_food
                        desertion_rate = min(0.10, food_deficit / max(consumption, 1))
                        
                        new_infantry = max(0, int(infantry * (1 - desertion_rate)))
                        new_archers = max(0, int(archers * (1 - desertion_rate)))
                        new_cavalry = max(0, int(cavalry * (1 - desertion_rate)))
                        
                        db.update_army(user_id, 
                            infantry=new_infantry,
                            archers=new_archers,
                            cavalry=new_cavalry
                        )
                        db.update_kingdom(user_id, food=0)
                        
                        # Notify about starvation
                        if kingdom.get('notifications_enabled', 1):
                            await self._notify(user_id,
                                "⚠️ <b>ARMY STARVING!</b>\n\n"
                                f"🍖 Food khatam! {desertion_rate*100:.0f}% army bhaag gayi!\n"
                                f"🗡 -{infantry - new_infantry} Infantry\n"
                                f"🏹 -{archers - new_archers} Archers\n"
                                f"🐎 -{cavalry - new_cavalry} Cavalry\n\n"
                                f"Farm se food collect karo! 🌾")
                
                await asyncio.sleep(3600)  # Run every hour
            except Exception as e:
                logger.error(f"Food consumption error: {e}")
                await asyncio.sleep(3600)
    
    async def _world_event_loop(self):
        """Spawn random world events periodically."""
        while self.running:
            try:
                # 30% chance every 2 hours
                if random.random() < 0.3:
                    event_types = [
                        {'type': 'treasure', 'message': '💎 Khazana mila! Sab players +500 Gold!',
                         'effect': {'gold': 500}, 'duration': 2},
                        {'type': 'plague', 'message': '😷 Plague! Food production -50% for 6 hours!',
                         'effect': {'food_multiplier': 0.5}, 'duration': 6},
                        {'type': 'festival', 'message': '🎉 Mahotsav! Training speed 2x for 12 hours!',
                         'effect': {'training_multiplier': 2.0}, 'duration': 12},
                        {'type': 'invasion', 'message': '🐉 Dragon sighted! Survival event active!',
                         'effect': {'survival_active': True}, 'duration': 6},
                        {'type': 'merchant', 'message': '🧙 Mysterious merchant aaya hai! Black Market refresh!',
                         'effect': {'market_refresh': True}, 'duration': 4},
                    ]
                    
                    event = random.choice(event_types)
                    
                    db.create_world_event(
                        event['type'],
                        event['message'],
                        event['effect'],
                        event['duration']
                    )
                    
                    # Broadcast to all users
                    if self.bot:
                        users = db.get_all_users()
                        for u in users:
                            try:
                                await self.bot.send_message(
                                    chat_id=u['telegram_id'],
                                    text=f"🌍 <b>WORLD EVENT!</b>\n\n"
                                         f"{event['message']}\n\n"
                                         f"⏳ Duration: {event['duration']} hours\n\n"
                                         f"<i>Sab players ko affect karega!</i>",
                                    parse_mode='HTML'
                                )
                            except Exception:
                                pass
                
                await asyncio.sleep(7200)  # Check every 2 hours
            except Exception as e:
                logger.error(f"World event error: {e}")
                await asyncio.sleep(7200)
    
    async def _shield_expiry_loop(self):
        """Check for shield expiry and notify users."""
        while self.running:
            try:
                kingdoms = db.get_all_kingdoms()
                
                for kingdom in kingdoms:
                    shield = kingdom.get('shield_expires')
                    if not shield:
                        continue
                    
                    if isinstance(shield, str):
                        shield = datetime.fromisoformat(shield.replace('Z', '+00:00'))
                    
                    time_left = (shield - datetime.now()).total_seconds()
                    
                    # Notify 10 minutes before expiry
                    if 540 < time_left < 660:  # Around 10 minutes
                        if kingdom.get('notifications_enabled', 1):
                            await self._notify(kingdom['user_id'],
                                "🛡 <b>Shield Expiring Soon!</b>\n\n"
                                "Aapka shield 10 minutes mein khatam hoga!\n"
                                "Savdhaan rahein! ⚔️")
                
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Shield expiry error: {e}")
                await asyncio.sleep(300)
    
    async def _notify(self, user_id: int, message: str):
        """Send notification to a user."""
        if not self.bot:
            return
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
        except Exception:
            pass

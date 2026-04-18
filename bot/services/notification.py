"""
Notification service for Kingdom Conquest.
Sends in-game notifications to players.
"""
from typing import Optional
from telegram import Bot

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class NotificationService:
    """Handles player notifications via Telegram."""
    
    def __init__(self, bot: Bot = None):
        self.bot = bot
    
    def set_bot(self, bot: Bot):
        """Set the bot instance for sending messages."""
        self.bot = bot
    
    async def notify(self, user_id: int, message: str, parse_mode: str = 'HTML'):
        """Send a notification to a player."""
        if not self.bot:
            return
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=parse_mode
            )
        except Exception as e:
            print(f"Failed to notify user {user_id}: {e}")
    
    async def notify_attacked(self, user_id: int, attacker_name: str):
        """Notify player they are being attacked."""
        message = (
            f"⚔️ <b>WAR ALERT!</b>\n"
            f"{attacker_name} ne aap par hamla kiya!\n"
            f"Dashboard check karo!"
        )
        await self.notify(user_id, message)
    
    async def notify_energy_full(self, user_id: int):
        """Notify player energy is full."""
        message = (
            f"⚡ <b>Energy Full!</b>\n"
            f"Aapki energy poori ho gayi hai!\n"
            f"Attack karne ke liye taiyaar!"
        )
        await self.notify(user_id, message)
    
    async def notify_building_complete(self, user_id: int, building_name: str, level: int):
        """Notify player building upgrade completed."""
        message = (
            f"✅ <b>Building Complete!</b>\n"
            f"{building_name} ab Level {level} hai!\n"
            f"Dashboard check karo!"
        )
        await self.notify(user_id, message)
    
    async def notify_shield_expiring(self, user_id: int, minutes_left: int):
        """Notify player shield is expiring soon."""
        message = (
            f"🛡 <b>Shield Expiring!</b>\n"
            f"Aapka shield {minutes_left} minutes mein khatam hoga!\n"
            f"Savdhaan rahein!"
        )
        await self.notify(user_id, message)
    
    async def notify_quest_complete(self, user_id: int, quest_name: str):
        """Notify player quest completed."""
        message = (
            f"🎯 <b>Quest Complete!</b>\n"
            f"'{quest_name}' poora hua!\n"
            f"Reward claim karne ke liye Quests menu check karo!"
        )
        await self.notify(user_id, message)
    
    async def notify_alliance_war(self, user_id: int, alliance_name: str):
        """Notify player about alliance war."""
        message = (
            f"⚔️ <b>Alliance War Started!</b>\n"
            f"{alliance_name} mein yuddh shuru!\n"
            f"Apni army bhejo!"
        )
        await self.notify(user_id, message)
    
    async def notify_bounty_placed(self, user_id: int, amount: int):
        """Notify player about bounty on them."""
        message = (
            f"💰 <b>BOUNTY ALERT!</b>\n"
            f"Kisi ne aap par <b>{amount:,} Gold</b> ka inaam rakha hai!\n"
            f"Savdhaan rahein!"
        )
        await self.notify(user_id, message)
    
    async def notify_starvation(self, user_id: int):
        """Notify player about army starvation."""
        message = (
            f"⚠️ <b>ARMY STARVING!</b>\n"
            f"Food khatam ho gayi! Army bhaag rahi hai!\n"
            f"Jaldi Farm se food collect karo!"
        )
        await self.notify(user_id, message)
    
    async def notify_revenge_available(self, user_id: int, attacker_name: str):
        """Notify player about revenge opportunity."""
        message = (
            f"🔥 <b>REVENGE AVAILABLE!</b>\n"
            f"{attacker_name} ne aap par hamla kiya!\n"
            f"1 ghante mein badla lo!\n"
            f"Attack menu se revenge karo!"
        )
        await self.notify(user_id, message)
    
    async def notify_world_event(self, user_id: int, event_message: str):
        """Notify player about world event."""
        message = f"🌍 <b>World Event!</b>\n{event_message}"
        await self.notify(user_id, message)
    
    async def broadcast(self, message: str, user_ids: list):
        """Broadcast message to multiple users."""
        for uid in user_ids:
            await self.notify(uid, message)

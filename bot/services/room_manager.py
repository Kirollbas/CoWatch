"""Room manager service (stub implementation)"""
import logging
from typing import List
from bot.database.models import Slot, Room

logger = logging.getLogger(__name__)

class RoomManager:
    """Manager for creating and managing rooms (stub implementation)"""
    
    @staticmethod
    def should_create_room(slot: Slot) -> bool:
        """Check if room should be created for slot"""
        participants_count = len(slot.participants)
        return participants_count >= slot.min_participants and slot.status == "open"
    
    @staticmethod
    def create_room_for_slot(slot: Slot) -> Room:
        """
        Create room for slot (stub - logs instead of creating real Telegram group)
        In future: create Telegram group, topics, invite participants
        """
        logger.info(f"STUB: Would create Telegram group for slot {slot.id}")
        logger.info(f"STUB: Movie: {slot.movie.title}")
        logger.info(f"STUB: Participants: {[p.user_id for p in slot.participants]}")
        logger.info(f"STUB: Would create topics: 'Обсуждение', 'Оценки'")
        
        # In real implementation:
        # 1. Create Telegram group via Bot API
        # 2. Create topics
        # 3. Invite all participants
        # 4. Send notifications
        
        # For now, just return the room (created in repository)
        return slot.room if slot.room else None
    
    @staticmethod
    def notify_participants(room: Room, message: str):
        """Notify all participants (stub)"""
        logger.info(f"STUB: Would notify participants of room {room.id}: {message}")
        # In future: send messages to all participants


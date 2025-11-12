"""Room manager service for creating and managing rooms"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from bot.database.models import Slot, Room, User
from bot.database.repositories import UserRepository, RoomRepository
from bot.constants import SlotStatus, RoomStatus

logger = logging.getLogger(__name__)

class RoomManager:
    """Manager for creating and managing rooms"""
    
    @staticmethod
    def should_create_room(slot: Slot) -> bool:
        """Check if room should be created for slot"""
        participants_count = len(slot.participants)
        return (participants_count >= slot.min_participants and
                slot.status == SlotStatus.OPEN and
                not slot.room)
    
    @staticmethod
    def create_room_for_slot(db: Session, slot: Slot) -> Optional[Room]:
        """
        Create room for slot and handle all related logic
        """
        if not RoomManager.should_create_room(slot):
            return None
            
        try:
            # Create room in database
            room = RoomRepository.create(db, slot.id)
            
            # Update slot status
            slot.status = SlotStatus.FULL
            db.commit()
            
            logger.info(f"Created room {room.id} for slot {slot.id}")
            logger.info(f"Movie: {slot.movie.title}")
            logger.info(f"Participants: {[p.user_id for p in slot.participants]}")
            logger.info(f"Scheduled time: {slot.datetime}")
            
            # In real implementation, here we would:
            # 1. Create Telegram group via Bot API
            # 2. Create topics: 'Обсуждение', 'Оценки'
            # 3. Invite all participants
            # 4. Set up scheduled messages
            
            return room
            
        except Exception as e:
            logger.error(f"Error creating room for slot {slot.id}: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def notify_participants(context, room: Room, message: str):
        """Notify all participants about room creation"""
        slot = room.slot
        participants = slot.participants
        
        logger.info(f"Notifying {len(participants)} participants of room {room.id}")
        
        for participant in participants:
            try:
                # Send notification to each participant
                context.bot.send_message(
                    chat_id=participant.user_id,
                    text=message,
                    parse_mode="HTML"
                )
                logger.info(f"Notified user {participant.user_id}")
            except Exception as e:
                logger.error(f"Failed to notify user {participant.user_id}: {e}")
    
    @staticmethod
    def get_room_creation_message(room: Room) -> str:
        """Generate message for room creation notification"""
        slot = room.slot
        datetime_str = slot.datetime.strftime("%d.%m.%Y в %H:%M")
        
        message = f"🎉 <b>Комната создана!</b>\n\n"
        message += f"🎬 Фильм: <b>{slot.movie.title}</b>\n"
        message += f"📅 Время просмотра: {datetime_str}\n"
        message += f"👥 Участников: {len(slot.participants)}\n\n"
        message += f"Скоро вы получите приглашение в группу для обсуждения!\n\n"
        message += f"<i>Не забудьте быть активными в обсуждении - это влияет на ваш рейтинг!</i>"
        
        return message
    
    @staticmethod
    def schedule_movie_reminder(context, room: Room):
        """Schedule reminder before movie time (stub)"""
        slot = room.slot
        # In real implementation: schedule job to remind participants
        # 1 hour before the movie time
        logger.info(f"STUB: Would schedule reminder for room {room.id} at {slot.datetime}")
    
    @staticmethod
    def start_discussion_phase(context, room: Room):
        """Start discussion phase after movie time (stub)"""
        # In real implementation: send message to group to start discussion
        # and schedule rating phase
        logger.info(f"STUB: Would start discussion phase for room {room.id}")
    
    @staticmethod
    def start_rating_phase(context, room: Room):
        """Start rating phase after discussion (stub)"""
        # In real implementation: send rating requests to all participants
        logger.info(f"STUB: Would start rating phase for room {room.id}")


"""Matching service for finding compatible users and slots"""
import logging
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from bot.database.models import User, Slot, SlotParticipant
from bot.database.repositories import SlotRepository, UserRepository, SlotParticipantRepository

logger = logging.getLogger(__name__)

class MatchingService:
    """Service for matching users by rating and finding compatible slots"""
    
    @staticmethod
    def find_compatible_slots(db: Session, movie_id: int, user_id: int,
                            rating_tolerance: float = 1.0) -> List[Slot]:
        """
        Find slots for the movie that are compatible with user's rating
        """
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            return []
        
        # Get all open slots for this movie
        slots = SlotRepository.get_by_movie(db, movie_id)
        compatible_slots = []
        
        for slot in slots:
            # Skip if user is already participating
            if any(p.user_id == user_id for p in slot.participants):
                continue
                
            # Skip if slot is full
            if slot.max_participants and len(slot.participants) >= slot.max_participants:
                continue
                
            # Check rating compatibility with existing participants
            if MatchingService._is_rating_compatible(db, slot, user, rating_tolerance):
                compatible_slots.append(slot)
        
        # Sort by compatibility score (closer ratings first)
        compatible_slots.sort(
            key=lambda s: MatchingService._calculate_compatibility_score(db, s, user)
        )
        
        return compatible_slots
    
    @staticmethod
    def _is_rating_compatible(db: Session, slot: Slot, user: User,
                            tolerance: float = 1.0) -> bool:
        """Check if user's rating is compatible with slot participants"""
        if not slot.participants:
            return True
            
        participant_ratings = []
        for participant in slot.participants:
            participant_user = UserRepository.get_by_id(db, participant.user_id)
            if participant_user and participant_user.total_ratings > 0:
                participant_ratings.append(participant_user.rating)
        
        if not participant_ratings:
            return True
            
        avg_rating = sum(participant_ratings) / len(participant_ratings)
        return abs(user.rating - avg_rating) <= tolerance
    
    @staticmethod
    def _calculate_compatibility_score(db: Session, slot: Slot, user: User) -> float:
        """Calculate compatibility score (lower is better)"""
        if not slot.participants:
            return 0.0
            
        participant_ratings = []
        for participant in slot.participants:
            participant_user = UserRepository.get_by_id(db, participant.user_id)
            if participant_user and participant_user.total_ratings > 0:
                participant_ratings.append(participant_user.rating)
        
        if not participant_ratings:
            return 0.0
            
        avg_rating = sum(participant_ratings) / len(participant_ratings)
        return abs(user.rating - avg_rating)
    
    @staticmethod
    def should_auto_join_slot(db: Session, slot: Slot, user: User) -> bool:
        """
        Determine if user should be automatically joined to a slot
        Based on rating compatibility and slot urgency
        """
        # Don't auto-join if user has low rating and no ratings yet
        if user.total_ratings == 0:
            return False
            
        # Check if slot is close to being full
        participants_count = len(slot.participants)
        if participants_count >= slot.min_participants - 1:
            return True
            
        # Check rating compatibility
        return MatchingService._is_rating_compatible(db, slot, user, tolerance=0.5)
    
    @staticmethod
    def find_best_slot_for_auto_join(db: Session, movie_id: int, user_id: int) -> Optional[Slot]:
        """Find the best slot for automatic joining"""
        compatible_slots = MatchingService.find_compatible_slots(db, movie_id, user_id)
        
        for slot in compatible_slots:
            user = UserRepository.get_by_id(db, user_id)
            if user and MatchingService.should_auto_join_slot(db, slot, user):
                return slot
                
        return None


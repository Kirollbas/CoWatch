"""Rating service"""
from sqlalchemy.orm import Session
from bot.database.repositories import RatingRepository, UserRepository
from bot.utils.validators import validate_rating

class RatingService:
    """Service for managing ratings"""
    
    @staticmethod
    def create_rating(db: Session, room_id: int, rater_id: int, rated_id: int, score: int) -> bool:
        """Create a rating"""
        # Validate score
        if not validate_rating(score):
            return False
        
        # Check if user is trying to rate themselves
        if rater_id == rated_id:
            return False
        
        # Check if already rated
        if RatingRepository.has_rated(db, room_id, rater_id, rated_id):
            return False
        
        # Create rating
        RatingRepository.create(db, room_id, rater_id, rated_id, score)
        
        # Update rated user's rating
        UserRepository.update_rating(db, rated_id)
        
        return True
    
    @staticmethod
    def get_users_to_rate(db: Session, room_id: int, rater_id: int) -> list:
        """Get list of user IDs that need to be rated"""
        return RatingRepository.get_room_participants_to_rate(db, room_id, rater_id)


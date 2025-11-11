"""Repository pattern for database operations"""
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from bot.database.models import User, Movie, Slot, SlotParticipant, Room, Rating
from bot.constants import SlotStatus, RoomStatus


class UserRepository:
    """Repository for User operations"""
    
    @staticmethod
    def get_or_create(db: Session, user_id: int, username: Optional[str] = None, 
                     first_name: Optional[str] = None) -> User:
        """Get user or create if not exists"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                username=username,
                first_name=first_name or "Unknown"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update username and first_name if provided
            if username is not None:
                user.username = username
            if first_name is not None:
                user.first_name = first_name
            db.commit()
        return user
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def update_rating(db: Session, user_id: int):
        """Update user rating based on received ratings"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        
        ratings = db.query(Rating).filter(Rating.rated_id == user_id).all()
        if ratings:
            avg_rating = sum(r.score for r in ratings) / len(ratings)
            user.rating = avg_rating
            user.total_ratings = len(ratings)
            db.commit()


class MovieRepository:
    """Repository for Movie operations"""
    
    @staticmethod
    def create(db: Session, title: str, year: Optional[int] = None, 
              movie_type: str = "movie", kinopoisk_id: Optional[str] = None,
              imdb_id: Optional[str] = None, description: Optional[str] = None,
              poster_url: Optional[str] = None) -> Movie:
        """Create a new movie"""
        movie = Movie(
            title=title,
            year=year,
            type=movie_type,
            kinopoisk_id=kinopoisk_id,
            imdb_id=imdb_id,
            description=description,
            poster_url=poster_url
        )
        db.add(movie)
        db.commit()
        db.refresh(movie)
        return movie
    
    @staticmethod
    def get_by_id(db: Session, movie_id: int) -> Optional[Movie]:
        """Get movie by ID"""
        return db.query(Movie).filter(Movie.id == movie_id).first()
    
    @staticmethod
    def find_by_kinopoisk_id(db: Session, kinopoisk_id: str) -> Optional[Movie]:
        """Find movie by Kinopoisk ID"""
        return db.query(Movie).filter(Movie.kinopoisk_id == kinopoisk_id).first()
    
    @staticmethod
    def find_by_imdb_id(db: Session, imdb_id: str) -> Optional[Movie]:
        """Find movie by IMDb ID"""
        return db.query(Movie).filter(Movie.imdb_id == imdb_id).first()


class SlotRepository:
    """Repository for Slot operations"""
    
    @staticmethod
    def create(db: Session, movie_id: int, creator_id: int, datetime_obj: datetime,
              min_participants: int = 2, max_participants: Optional[int] = None) -> Slot:
        """Create a new slot"""
        slot = Slot(
            movie_id=movie_id,
            creator_id=creator_id,
            datetime=datetime_obj,
            min_participants=min_participants,
            max_participants=max_participants
        )
        db.add(slot)
        db.commit()
        db.refresh(slot)
        return slot
    
    @staticmethod
    def get_by_id(db: Session, slot_id: int) -> Optional[Slot]:
        """Get slot by ID"""
        return db.query(Slot).filter(Slot.id == slot_id).first()
    
    @staticmethod
    def get_by_movie(db: Session, movie_id: int) -> List[Slot]:
        """Get all slots for a movie"""
        return db.query(Slot).filter(
            Slot.movie_id == movie_id,
            Slot.status == SlotStatus.OPEN
        ).all()
    
    @staticmethod
    def get_by_creator(db: Session, creator_id: int) -> List[Slot]:
        """Get all slots created by user"""
        return db.query(Slot).filter(Slot.creator_id == creator_id).all()
    
    @staticmethod
    def get_user_participations(db: Session, user_id: int) -> List[Slot]:
        """Get all slots where user is a participant"""
        return db.query(Slot).join(SlotParticipant).filter(
            SlotParticipant.user_id == user_id,
            Slot.status == SlotStatus.OPEN
        ).all()


class SlotParticipantRepository:
    """Repository for SlotParticipant operations"""
    
    @staticmethod
    def add_participant(db: Session, slot_id: int, user_id: int) -> SlotParticipant:
        """Add participant to slot"""
        # Check if already participating
        existing = db.query(SlotParticipant).filter(
            SlotParticipant.slot_id == slot_id,
            SlotParticipant.user_id == user_id
        ).first()
        if existing:
            return existing
        
        participant = SlotParticipant(
            slot_id=slot_id,
            user_id=user_id
        )
        db.add(participant)
        db.commit()
        db.refresh(participant)
        return participant
    
    @staticmethod
    def remove_participant(db: Session, slot_id: int, user_id: int) -> bool:
        """Remove participant from slot"""
        participant = db.query(SlotParticipant).filter(
            SlotParticipant.slot_id == slot_id,
            SlotParticipant.user_id == user_id
        ).first()
        if participant:
            db.delete(participant)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_participants_count(db: Session, slot_id: int) -> int:
        """Get number of participants in slot"""
        return db.query(SlotParticipant).filter(SlotParticipant.slot_id == slot_id).count()


class RoomRepository:
    """Repository for Room operations"""
    
    @staticmethod
    def create(db: Session, slot_id: int) -> Room:
        """Create a new room"""
        room = Room(slot_id=slot_id)
        db.add(room)
        db.commit()
        db.refresh(room)
        return room
    
    @staticmethod
    def get_by_slot_id(db: Session, slot_id: int) -> Optional[Room]:
        """Get room by slot ID"""
        return db.query(Room).filter(Room.slot_id == slot_id).first()
    
    @staticmethod
    def get_user_rooms(db: Session, user_id: int) -> List[Room]:
        """Get all rooms where user is a participant"""
        return db.query(Room).join(Slot).join(SlotParticipant).filter(
            SlotParticipant.user_id == user_id,
            Room.status == RoomStatus.ACTIVE
        ).all()


class RatingRepository:
    """Repository for Rating operations"""
    
    @staticmethod
    def create(db: Session, room_id: int, rater_id: int, rated_id: int, score: int) -> Rating:
        """Create a new rating"""
        rating = Rating(
            room_id=room_id,
            rater_id=rater_id,
            rated_id=rated_id,
            score=score
        )
        db.add(rating)
        db.commit()
        db.refresh(rating)
        return rating
    
    @staticmethod
    def has_rated(db: Session, room_id: int, rater_id: int, rated_id: int) -> bool:
        """Check if rater has already rated rated user in this room"""
        return db.query(Rating).filter(
            Rating.room_id == room_id,
            Rating.rater_id == rater_id,
            Rating.rated_id == rated_id
        ).first() is not None
    
    @staticmethod
    def get_room_participants_to_rate(db: Session, room_id: int, rater_id: int) -> List[int]:
        """Get list of user IDs that rater needs to rate in this room"""
        # Get all participants in the room
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            return []
        
        slot = room.slot
        participants = [p.user_id for p in slot.participants]
        
        # Filter out rater and already rated users
        rated_users = {r.rated_id for r in db.query(Rating).filter(
            Rating.room_id == room_id,
            Rating.rater_id == rater_id
        ).all()}
        
        return [uid for uid in participants if uid != rater_id and uid not in rated_users]


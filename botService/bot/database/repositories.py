"""Repository pattern for database operations"""
from sqlalchemy.orm import Session
from typing import Optional, List, Tuple, Dict
from datetime import datetime

from bot.database.models import (
    User, Movie, Slot, SlotParticipant, Room, Rating,
    Episode, Comment, Like, WatchHistory
)
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
              poster_url: Optional[str] = None,
              name_original: Optional[str] = None,
              rating: Optional[float] = None,
              rating_kinopoisk: Optional[float] = None,
              rating_imdb: Optional[float] = None,
              rating_film_critics: Optional[float] = None,
              rating_await: Optional[float] = None,
              rating_rf_critics: Optional[float] = None,
              film_length: Optional[int] = None,
              age_rating: Optional[str] = None,
              slogan: Optional[str] = None,
              countries: Optional[str] = None,
              genres: Optional[str] = None) -> Movie:
        """Create a new movie"""
        movie = Movie(
            title=title,
            name_original=name_original,
            year=year,
            type=movie_type,
            kinopoisk_id=kinopoisk_id,
            imdb_id=imdb_id,
            description=description,
            poster_url=poster_url,
            rating=rating,
            rating_kinopoisk=rating_kinopoisk,
            rating_imdb=rating_imdb,
            rating_film_critics=rating_film_critics,
            rating_await=rating_await,
            rating_rf_critics=rating_rf_critics,
            film_length=film_length,
            age_rating=age_rating,
            slogan=slogan,
            countries=countries,
            genres=genres
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
    
    @staticmethod
    def update_from_api(db: Session, movie: Movie, api_data: Dict) -> Movie:
        """Update movie data from Kinopoisk API response"""
        from datetime import datetime
        
        # Update basic fields
        if api_data.get("nameRu"):
            movie.title = api_data["nameRu"]
        if api_data.get("nameOriginal"):
            movie.name_original = api_data["nameOriginal"]
        if api_data.get("year"):
            movie.year = api_data["year"]
        if api_data.get("description") or api_data.get("shortDescription"):
            movie.description = api_data.get("description") or api_data.get("shortDescription")
        if api_data.get("posterUrl"):
            movie.poster_url = api_data["posterUrl"]
        
        # Update ratings
        rating_data = api_data.get("rating", {})
        if isinstance(rating_data, dict):
            movie.rating = rating_data.get("kp") or rating_data.get("rating")
            movie.rating_kinopoisk = rating_data.get("kp")
            movie.rating_imdb = rating_data.get("imdb")
            movie.rating_film_critics = rating_data.get("filmCritics")
            movie.rating_await = rating_data.get("await")
            movie.rating_rf_critics = rating_data.get("russianFilmCritics")
        
        # Update additional metadata
        if api_data.get("filmLength"):
            movie.film_length = api_data["filmLength"]
        if api_data.get("ageRating"):
            movie.age_rating = api_data["ageRating"]
        if api_data.get("slogan"):
            movie.slogan = api_data["slogan"]
        
        # Store countries and genres as JSON strings
        if api_data.get("countries"):
            import json
            movie.countries = json.dumps([c.get("country", "") for c in api_data["countries"]], ensure_ascii=False)
        if api_data.get("genres"):
            import json
            movie.genres = json.dumps([g.get("genre", "") for g in api_data["genres"]], ensure_ascii=False)
        
        # Update timestamp
        movie.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(movie)
        return movie


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
            Slot.status.in_([SlotStatus.OPEN, SlotStatus.FULL])
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


class EpisodeRepository:
    """Repository for Episode operations"""
    
    @staticmethod
    def create(db: Session, series_id: int, season_number: int, episode_number: int,
              title: Optional[str] = None, description: Optional[str] = None,
              air_date: Optional[datetime] = None, runtime_minutes: Optional[int] = None) -> Episode:
        """Create a new episode"""
        episode = Episode(
            series_id=series_id,
            season_number=season_number,
            episode_number=episode_number,
            title=title,
            description=description,
            air_date=air_date,
            runtime_minutes=runtime_minutes
        )
        db.add(episode)
        db.commit()
        db.refresh(episode)
        return episode
    
    @staticmethod
    def get_by_id(db: Session, episode_id: int) -> Optional[Episode]:
        """Get episode by ID"""
        return db.query(Episode).filter(Episode.id == episode_id).first()
    
    @staticmethod
    def get_by_series(db: Session, series_id: int) -> List[Episode]:
        """Get all episodes for a series"""
        return db.query(Episode).filter(
            Episode.series_id == series_id
        ).order_by(Episode.season_number, Episode.episode_number).all()
    
    @staticmethod
    def get_by_series_season(db: Session, series_id: int, season_number: int) -> List[Episode]:
        """Get all episodes for a specific season"""
        return db.query(Episode).filter(
            Episode.series_id == series_id,
            Episode.season_number == season_number
        ).order_by(Episode.episode_number).all()
    
    @staticmethod
    def find_by_series_season_episode(db: Session, series_id: int, 
                                      season_number: int, episode_number: int) -> Optional[Episode]:
        """Find specific episode by series, season, and episode number"""
        return db.query(Episode).filter(
            Episode.series_id == series_id,
            Episode.season_number == season_number,
            Episode.episode_number == episode_number
        ).first()


class CommentRepository:
    """Repository for Comment operations"""
    
    @staticmethod
    def create(db: Session, room_id: int, user_id: int, content: str,
              episode_id: Optional[int] = None, reply_to_id: Optional[int] = None) -> Comment:
        """Create a new comment"""
        comment = Comment(
            room_id=room_id,
            user_id=user_id,
            episode_id=episode_id,
            content=content,
            reply_to_id=reply_to_id
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment
    
    @staticmethod
    def get_by_id(db: Session, comment_id: int) -> Optional[Comment]:
        """Get comment by ID"""
        return db.query(Comment).filter(Comment.id == comment_id).first()
    
    @staticmethod
    def get_by_room(db: Session, room_id: int, limit: Optional[int] = None) -> List[Comment]:
        """Get all comments for a room, ordered by creation time"""
        query = db.query(Comment).filter(Comment.room_id == room_id).order_by(Comment.created_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def get_by_episode(db: Session, episode_id: int) -> List[Comment]:
        """Get all comments for an episode"""
        return db.query(Comment).filter(
            Comment.episode_id == episode_id
        ).order_by(Comment.created_at.desc()).all()
    
    @staticmethod
    def get_replies(db: Session, comment_id: int) -> List[Comment]:
        """Get all replies to a comment"""
        return db.query(Comment).filter(
            Comment.reply_to_id == comment_id
        ).order_by(Comment.created_at).all()
    
    @staticmethod
    def delete(db: Session, comment_id: int) -> bool:
        """Delete a comment"""
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if comment:
            db.delete(comment)
            db.commit()
            return True
        return False


class LikeRepository:
    """Repository for Like operations"""
    
    @staticmethod
    def toggle_like(db: Session, comment_id: int, user_id: int) -> Tuple[bool, bool]:
        """Toggle like on a comment. Returns (was_created, is_liked_now)"""
        existing = db.query(Like).filter(
            Like.comment_id == comment_id,
            Like.user_id == user_id
        ).first()
        
        if existing:
            # Unlike
            db.delete(existing)
            db.commit()
            return (False, False)
        else:
            # Like
            like = Like(comment_id=comment_id, user_id=user_id)
            db.add(like)
            db.commit()
            return (True, True)
    
    @staticmethod
    def has_liked(db: Session, comment_id: int, user_id: int) -> bool:
        """Check if user has liked a comment"""
        return db.query(Like).filter(
            Like.comment_id == comment_id,
            Like.user_id == user_id
        ).first() is not None
    
    @staticmethod
    def get_likes_count(db: Session, comment_id: int) -> int:
        """Get number of likes for a comment"""
        return db.query(Like).filter(Like.comment_id == comment_id).count()
    
    @staticmethod
    def get_likes_for_comment(db: Session, comment_id: int) -> List[Like]:
        """Get all likes for a comment"""
        return db.query(Like).filter(Like.comment_id == comment_id).all()


class WatchHistoryRepository:
    """Repository for WatchHistory operations"""
    
    @staticmethod
    def create_or_update(db: Session, user_id: int, movie_id: int,
                        episode_id: Optional[int] = None, room_id: Optional[int] = None,
                        progress_seconds: Optional[int] = None, completed: int = 0) -> WatchHistory:
        """Create or update watch history entry"""
        # Try to find existing entry
        query = db.query(WatchHistory).filter(
            WatchHistory.user_id == user_id,
            WatchHistory.movie_id == movie_id
        )
        if episode_id:
            query = query.filter(WatchHistory.episode_id == episode_id)
        else:
            query = query.filter(WatchHistory.episode_id.is_(None))
        
        watch = query.first()
        
        if watch:
            # Update existing
            if progress_seconds is not None:
                watch.progress_seconds = progress_seconds
            if completed is not None:
                watch.completed = completed
            if room_id is not None:
                watch.room_id = room_id
            watch.watched_at = datetime.utcnow()
        else:
            # Create new
            watch = WatchHistory(
                user_id=user_id,
                movie_id=movie_id,
                episode_id=episode_id,
                room_id=room_id,
                progress_seconds=progress_seconds,
                completed=completed
            )
            db.add(watch)
        
        db.commit()
        db.refresh(watch)
        return watch
    
    @staticmethod
    def get_user_history(db: Session, user_id: int, limit: Optional[int] = None) -> List[WatchHistory]:
        """Get watch history for a user"""
        query = db.query(WatchHistory).filter(
            WatchHistory.user_id == user_id
        ).order_by(WatchHistory.watched_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    @staticmethod
    def get_by_movie(db: Session, user_id: int, movie_id: int) -> Optional[WatchHistory]:
        """Get watch history for a specific movie (non-episode)"""
        return db.query(WatchHistory).filter(
            WatchHistory.user_id == user_id,
            WatchHistory.movie_id == movie_id,
            WatchHistory.episode_id.is_(None)
        ).first()
    
    @staticmethod
    def get_by_episode(db: Session, user_id: int, episode_id: int) -> Optional[WatchHistory]:
        """Get watch history for a specific episode"""
        return db.query(WatchHistory).filter(
            WatchHistory.user_id == user_id,
            WatchHistory.episode_id == episode_id
        ).first()
    
    @staticmethod
    def get_completed_count(db: Session, user_id: int) -> int:
        """Get count of completed watches for a user"""
        return db.query(WatchHistory).filter(
            WatchHistory.user_id == user_id,
            WatchHistory.completed == 1
        ).count()


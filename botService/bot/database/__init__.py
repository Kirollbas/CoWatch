"""Database package"""
from bot.database.session import SessionLocal, get_db, get_db_session, Base, engine
from bot.database.models import (
    User, Movie, Slot, SlotParticipant, Room, Rating,
    Episode, Comment, Like, WatchHistory
)
from bot.database.repositories import (
    UserRepository,
    MovieRepository,
    SlotRepository,
    SlotParticipantRepository,
    RoomRepository,
    RatingRepository,
    EpisodeRepository,
    CommentRepository,
    LikeRepository,
    WatchHistoryRepository,
)

__all__ = [
    # Session management
    "SessionLocal",
    "get_db",
    "get_db_session",
    "Base",
    "engine",
    # Models
    "User",
    "Movie",
    "Slot",
    "SlotParticipant",
    "Room",
    "Rating",
    "Episode",
    "Comment",
    "Like",
    "WatchHistory",
    # Repositories
    "UserRepository",
    "MovieRepository",
    "SlotRepository",
    "SlotParticipantRepository",
    "RoomRepository",
    "RatingRepository",
    "EpisodeRepository",
    "CommentRepository",
    "LikeRepository",
    "WatchHistoryRepository",
]


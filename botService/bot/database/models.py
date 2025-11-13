"""SQLAlchemy models"""
from sqlalchemy import Column, Integer, BigInteger, String, Float, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint
from datetime import datetime
import enum

from bot.database.session import Base
from bot.constants import SlotStatus, RoomStatus, MovieType


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)  # Telegram user_id
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=False)
    rating = Column(Float, default=0.0)
    total_ratings = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    # Relationships
    created_slots = relationship("Slot", back_populates="creator", foreign_keys="Slot.creator_id")
    slot_participations = relationship("SlotParticipant", back_populates="user")
    ratings_given = relationship("Rating", back_populates="rater", foreign_keys="Rating.rater_id")
    ratings_received = relationship("Rating", back_populates="rated", foreign_keys="Rating.rated_id")
    comments = relationship("Comment", back_populates="user")
    likes = relationship("Like", back_populates="user")
    watch_history = relationship("WatchHistory", back_populates="user")

class UserKinopoisk(Base):
    """Mapping of Telegram user to Kinopoisk user id"""
    __tablename__ = "user_kinopoisk"
    
    user_id = Column(BigInteger, ForeignKey("users.id"), primary_key=True)
    kp_user_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    # Relationship
    user = relationship("User")

class UserVote(Base):
    """User's Kinopoisk votes/preferences"""
    __tablename__ = "user_votes"
    __table_args__ = (
        UniqueConstraint("user_id", "kinopoisk_id", name="uq_user_movie_vote"),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    kinopoisk_id = Column(String, nullable=False)  # KP movie id
    title = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    type = Column(String, nullable=True)  # FILM / TV_SERIES
    user_rating = Column(Integer, nullable=False)  # 1-10 scale on KP
    poster_url = Column(String, nullable=True)
    genres = Column(String, nullable=True)  # comma-separated genres
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    # Relationship
    user = relationship("User")


class Movie(Base):
    """Movie model"""
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    name_original = Column(String, nullable=True)  # Оригинальное название
    year = Column(Integer, nullable=True)
    type = Column(SQLEnum(MovieType.MOVIE, MovieType.SERIES, name="movie_type"), nullable=False)
    kinopoisk_id = Column(String, nullable=True)
    imdb_id = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    poster_url = Column(String, nullable=True)
    
    # Kinopoisk API ratings
    rating = Column(Float, nullable=True)               # Общий рейтинг
    rating_kinopoisk = Column(Float, nullable=True)     # Рейтинг Кинопоиска
    rating_imdb = Column(Float, nullable=True)          # Рейтинг IMDb
    rating_film_critics = Column(Float, nullable=True)  # Рейтинг кинокритиков
    rating_await = Column(Float, nullable=True)         # Ожидаемый рейтинг
    rating_rf_critics = Column(Float, nullable=True)    # Рейтинг российских кинокритиков
    
    # Additional metadata from Kinopoisk API
    film_length = Column(Integer, nullable=True)        # Длительность в минутах
    age_rating = Column(String, nullable=True)          # Возрастной рейтинг (например, "18+")
    slogan = Column(String, nullable=True)              # Слоган фильма
    countries = Column(String, nullable=True)           # JSON строка со странами
    genres = Column(String, nullable=True)              # comma-separated genres (compatible with main)
    
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, nullable=True, onupdate=lambda: datetime.utcnow())  # Время последнего обновления из API
    
    # Relationships
    slots = relationship("Slot", back_populates="movie")
    episodes = relationship("Episode", back_populates="series")


class Slot(Base):
    """Slot model"""
    __tablename__ = "slots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    creator_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    datetime = Column(DateTime, nullable=False)
    min_participants = Column(Integer, default=1)
    max_participants = Column(Integer, nullable=True)
    status = Column(SQLEnum(SlotStatus.OPEN, SlotStatus.FULL, SlotStatus.COMPLETED, name="slot_status"), 
                    default=SlotStatus.OPEN)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    # Relationships
    movie = relationship("Movie", back_populates="slots")
    creator = relationship("User", back_populates="created_slots", foreign_keys=[creator_id])
    participants = relationship("SlotParticipant", back_populates="slot", cascade="all, delete-orphan")
    room = relationship("Room", back_populates="slot", uselist=False)


class SlotParticipant(Base):
    """Slot participant model"""
    __tablename__ = "slot_participants"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    # Relationships
    slot = relationship("Slot", back_populates="participants")
    user = relationship("User", back_populates="slot_participations")


class Room(Base):
    """Room model"""
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False, unique=True)
    telegram_group_id = Column(BigInteger, nullable=True)  # Заглушка
    telegram_topic_id = Column(Integer, nullable=True)  # Заглушка
    status = Column(SQLEnum(RoomStatus.ACTIVE, RoomStatus.COMPLETED, name="room_status"), 
                    default=RoomStatus.ACTIVE)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    discussion_end_time = Column(DateTime, nullable=True)
    
    # Relationships
    slot = relationship("Slot", back_populates="room")
    ratings = relationship("Rating", back_populates="room")
    comments = relationship("Comment", back_populates="room")


class Rating(Base):
    """Rating model"""
    __tablename__ = "ratings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    rater_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)  # кто оценивает
    rated_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)  # кого оценивают
    score = Column(Integer, nullable=False)  # 1-5
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    # Relationships
    room = relationship("Room", back_populates="ratings")
    rater = relationship("User", back_populates="ratings_given", foreign_keys=[rater_id])
    rated = relationship("User", back_populates="ratings_received", foreign_keys=[rated_id])


class Episode(Base):
    """Episode model for series"""
    __tablename__ = "episodes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    series_id = Column(Integer, ForeignKey("movies.id"), nullable=False)  # references Movie with type 'series'
    season_number = Column(Integer, nullable=False)
    episode_number = Column(Integer, nullable=False)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    air_date = Column(DateTime, nullable=True)
    runtime_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    # Relationships
    series = relationship("Movie", back_populates="episodes")
    comments = relationship("Comment", back_populates="episode")
    watch_history = relationship("WatchHistory", back_populates="episode")


class Comment(Base):
    """Comments inside a room, optionally bound to a specific episode"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=True)
    content = Column(Text, nullable=False)
    reply_to_id = Column(Integer, ForeignKey("comments.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    # Relationships
    room = relationship("Room", back_populates="comments")
    user = relationship("User", back_populates="comments")
    episode = relationship("Episode", back_populates="comments")
    likes = relationship("Like", back_populates="comment", cascade="all, delete-orphan")


class Like(Base):
    """Likes for comments"""
    __tablename__ = "likes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    # Relationships
    comment = relationship("Comment", back_populates="likes")
    user = relationship("User", back_populates="likes")


class WatchHistory(Base):
    """Watch history of users for movies and episodes"""
    __tablename__ = "watch_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    episode_id = Column(Integer, ForeignKey("episodes.id"), nullable=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    watched_at = Column(DateTime, default=lambda: datetime.utcnow())
    progress_seconds = Column(Integer, nullable=True)  # optional playback progress
    completed = Column(Integer, default=0)  # 0/1
    
    # Relationships
    user = relationship("User", back_populates="watch_history")
    episode = relationship("Episode", back_populates="watch_history")

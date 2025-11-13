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
    year = Column(Integer, nullable=True)
    type = Column(SQLEnum(MovieType.MOVIE, MovieType.SERIES, name="movie_type"), nullable=False)
    kinopoisk_id = Column(String, nullable=True)
    imdb_id = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    poster_url = Column(String, nullable=True)
    genres = Column(String, nullable=True)  # comma-separated genres
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    # Relationships
    slots = relationship("Slot", back_populates="movie")


class Slot(Base):
    """Slot model"""
    __tablename__ = "slots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    creator_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    datetime = Column(DateTime, nullable=False)
    min_participants = Column(Integer, default=2)
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


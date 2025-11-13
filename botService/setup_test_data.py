#!/usr/bin/env python3
"""Setup test data for bot testing"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.database.session import SessionLocal
from bot.database.repositories import UserRepository, MovieRepository, SlotRepository, SlotParticipantRepository
from bot.constants import MovieType
from datetime import datetime, timedelta

def setup_test_data():
    """Create test users, movies, and slots for testing"""
    print("🔧 Setting up test data...")
    
    db = SessionLocal()
    try:
        # Create test users with different ratings
        print("👥 Creating test users...")
        
        # Main user (you) - реальный пользователь
        main_user = UserRepository.get_or_create(db, 890859555, "kirbot314", "Кирилл")
        main_user.rating = 4.0
        main_user.total_ratings = 3
        
        # Создаем второго тестового пользователя для слота (не будем ему отправлять сообщения)
        test_user = UserRepository.get_or_create(db, 111111111, "test_user", "Тестовый пользователь")
        test_user.rating = 4.2
        test_user.total_ratings = 5
        
        db.commit()
        print(f"✅ Created users: Кирилл (4.0⭐), Тестовый пользователь (4.2⭐)")
        
        # Create test movies
        print("🎬 Creating test movies...")
        
        movie1 = MovieRepository.create(
            db=db,
            title="Inception",
            year=2010,
            movie_type=MovieType.MOVIE,
            kinopoisk_id="447301",
            description="A thief who steals corporate secrets through dream-sharing technology"
        )
        
        movie2 = MovieRepository.create(
            db=db,
            title="Breaking Bad",
            year=2008,
            movie_type=MovieType.SERIES,
            imdb_id="tt0903747",
            description="A high school chemistry teacher turned methamphetamine producer"
        )
        
        print(f"✅ Created movies: {movie1.title}, {movie2.title}")
        
        # Create test slots
        print("📅 Creating test slots...")
        
        # Target time: 15.11.2025 20:00
        target_time = datetime(2025, 11, 15, 20, 0)
        
        # Slot 1: Inception с тестовым пользователем ждущим (1/2 participants)
        slot1 = SlotRepository.create(
            db=db,
            movie_id=movie1.id,
            creator_id=test_user.id,
            datetime_obj=target_time,
            min_participants=1  # Нужен 1 участник для тестирования
        )
        SlotParticipantRepository.add_participant(db, slot1.id, test_user.id)
        
        print(f"✅ Created slots:")
        print(f"   - {movie1.title}: 15.11.2025 20:00 (1/2 участников) - Тестовый пользователь ждет!")
        
        print("\n🎯 Test scenario ready:")
        print("1. Добавьте фильм через /add_movie")
        print("   → Отправьте: https://www.kinopoisk.ru/film/447301/")
        print("   → Выберите слот тестового пользователя")
        print("   → Автоматически присоединитесь (2/2)")
        print("   → Создастся комната и получите кнопку создания группы!")
        
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_test_data()
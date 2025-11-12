#!/usr/bin/env python3
"""Test script for the new movie matching logic"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.database.session import SessionLocal
from bot.database.repositories import UserRepository, MovieRepository, SlotRepository, SlotParticipantRepository
from bot.services.matching import MatchingService
from bot.services.room_manager import RoomManager
from bot.constants import MovieType
from datetime import datetime, timedelta

def test_matching_logic():
    """Test the movie matching and room creation logic"""
    print("🧪 Testing movie matching logic...")
    
    db = SessionLocal()
    try:
        # Create test users with different ratings
        user1 = UserRepository.get_or_create(db, 12345, "user1", "Test User 1")
        user1.rating = 4.5
        user1.total_ratings = 10
        
        user2 = UserRepository.get_or_create(db, 12346, "user2", "Test User 2") 
        user2.rating = 4.2
        user2.total_ratings = 8
        
        user3 = UserRepository.get_or_create(db, 12347, "user3", "Test User 3")
        user3.rating = 2.1
        user3.total_ratings = 5
        
        user4 = UserRepository.get_or_create(db, 12348, "user4", "Test User 4")
        user4.rating = 4.3
        user4.total_ratings = 12
        
        db.commit()
        
        # Create test movie
        movie = MovieRepository.create(
            db=db,
            title="Test Movie",
            year=2024,
            movie_type=MovieType.MOVIE,
            description="A test movie for matching logic"
        )
        
        # Create test slot with user1 as creator
        future_time = datetime.now() + timedelta(hours=2)
        slot = SlotRepository.create(
            db=db,
            movie_id=movie.id,
            creator_id=user1.id,
            datetime_obj=future_time,
            min_participants=3
        )
        
        # Add user1 as participant
        SlotParticipantRepository.add_participant(db, slot.id, user1.id)
        
        print(f"✅ Created test movie: {movie.title}")
        print(f"✅ Created test slot with min_participants: {slot.min_participants}")
        print(f"✅ Added user1 (rating: {user1.rating}) as creator")
        
        # Test 1: Check compatible slots for user2 (similar rating)
        print("\n🔍 Test 1: Finding compatible slots for user2 (rating: 4.2)")
        compatible_slots = MatchingService.find_compatible_slots(db, movie.id, user2.id)
        print(f"Compatible slots found: {len(compatible_slots)}")
        
        # Test 2: Check if user2 should auto-join
        print("\n🔍 Test 2: Checking auto-join for user2")
        best_slot = MatchingService.find_best_slot_for_auto_join(db, movie.id, user2.id)
        if best_slot:
            print(f"✅ User2 should auto-join slot {best_slot.id}")
            SlotParticipantRepository.add_participant(db, best_slot.id, user2.id)
            db.refresh(best_slot)
            print(f"Participants after adding user2: {len(best_slot.participants)}")
        else:
            print("❌ User2 should not auto-join")
        
        # Test 3: Check compatible slots for user3 (different rating)
        print("\n🔍 Test 3: Finding compatible slots for user3 (rating: 2.1)")
        compatible_slots_user3 = MatchingService.find_compatible_slots(db, movie.id, user3.id)
        print(f"Compatible slots found for user3: {len(compatible_slots_user3)}")
        
        # Test 4: Add user4 and check room creation
        print("\n🔍 Test 4: Adding user4 and checking room creation")
        SlotParticipantRepository.add_participant(db, slot.id, user4.id)
        db.refresh(slot)
        print(f"Participants after adding user4: {len(slot.participants)}")
        
        should_create = RoomManager.should_create_room(slot)
        print(f"Should create room: {should_create}")
        
        if should_create:
            print("🎉 Room creation conditions met!")
            # In real scenario, room would be created here
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_matching_logic()
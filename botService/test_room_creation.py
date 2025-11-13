#!/usr/bin/env python3
"""Test script to verify room creation logic"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.database.session import SessionLocal
from bot.database.repositories import SlotRepository, SlotParticipantRepository
from bot.services.room_manager import RoomManager

def test_room_creation():
    """Test if room creation logic works correctly"""
    db = SessionLocal()
    try:
        # Get all slots
        from bot.database.models import Slot
        all_slots = db.query(Slot).all()
        
        print(f"Found {len(all_slots)} slots in database:")
        
        for slot in all_slots:
            participants_count = len(slot.participants)
            should_create = RoomManager.should_create_room(slot)
            
            print(f"Slot {slot.id}:")
            print(f"  Movie: {slot.movie.title}")
            print(f"  Participants: {participants_count}/{slot.min_participants}")
            print(f"  Status: {slot.status}")
            print(f"  Should create room: {should_create}")
            print(f"  Participants list: {[p.user_id for p in slot.participants]}")
            print()
            
            if should_create:
                print(f"🎉 SLOT {slot.id} IS READY FOR ROOM CREATION!")
                print(f"   Movie: {slot.movie.title}")
                print(f"   Participants: {participants_count}/{slot.min_participants}")
                print()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_room_creation()
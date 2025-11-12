#!/usr/bin/env python3
"""Check database contents"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.database.session import SessionLocal
from bot.database.models import User, Movie, Slot, SlotParticipant
from bot.constants import SlotStatus

def check_database():
    """Check what's in the database"""
    print("🔍 Checking database contents...")
    
    db = SessionLocal()
    try:
        # Check users
        print("\n👥 Users:")
        users = db.query(User).all()
        for user in users:
            print(f"  - ID: {user.id}, Username: {user.username}, Name: {user.first_name}")
        
        # Check movies
        print("\n🎬 Movies:")
        movies = db.query(Movie).all()
        for movie in movies:
            print(f"  - ID: {movie.id}, Title: {movie.title}, Kinopoisk ID: {movie.kinopoisk_id}")
        
        # Check slots
        print("\n📅 Slots:")
        slots = db.query(Slot).all()
        for slot in slots:
            participants = [p.user_id for p in slot.participants]
            print(f"  - ID: {slot.id}, Movie: {slot.movie.title}, Status: {slot.status}")
            print(f"    DateTime: {slot.datetime}, Min participants: {slot.min_participants}")
            print(f"    Participants: {participants} ({len(participants)} total)")
            print(f"    Creator: {slot.creator_id}")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database()
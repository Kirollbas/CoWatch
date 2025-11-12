#!/usr/bin/env python3
"""Clear movies from database to test new parser"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.database.session import SessionLocal
from bot.database.models import Movie, Slot, SlotParticipant, Room

def clear_movies():
    """Clear all movies and related data"""
    print("🗑️ Clearing movies from database...")
    
    db = SessionLocal()
    try:
        # Delete in correct order due to foreign key constraints
        print("Deleting slot participants...")
        db.query(SlotParticipant).delete()
        
        print("Deleting rooms...")
        db.query(Room).delete()
        
        print("Deleting slots...")
        db.query(Slot).delete()
        
        print("Deleting movies...")
        db.query(Movie).delete()
        
        db.commit()
        print("✅ All movies and related data cleared!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_movies()
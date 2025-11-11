"""Initialize database - create all tables"""
from bot.database.session import engine, Base
from bot.database.models import User, Movie, Slot, SlotParticipant, Room, Rating

def init_database():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database()


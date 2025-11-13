"""Initialize database - create all tables"""
from bot.database.session import engine, Base
from bot.database.models import User, Movie, Slot, SlotParticipant, Room, Rating
from sqlalchemy import text, inspect

def init_database():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    ensure_schema()

def ensure_schema():
    """Ensure new nullable columns exist on existing tables"""
    insp = inspect(engine)
    dialect = engine.dialect.name
    
    # movies.genres
    try:
        cols = {c["name"] for c in insp.get_columns("movies")}
        if "genres" not in cols:
            ddl = "ALTER TABLE movies ADD COLUMN genres VARCHAR" if dialect != "sqlite" else "ALTER TABLE movies ADD COLUMN genres TEXT"
            with engine.connect() as conn:
                conn.execute(text(ddl))
                conn.commit()
            print("Added movies.genres column")
    except Exception as e:
        print(f"Schema check for movies.genres failed: {e}")
    
    # user_votes.genres
    try:
        if insp.has_table("user_votes"):
            cols = {c["name"] for c in insp.get_columns("user_votes")}
            if "genres" not in cols:
                ddl = "ALTER TABLE user_votes ADD COLUMN genres VARCHAR" if dialect != "sqlite" else "ALTER TABLE user_votes ADD COLUMN genres TEXT"
                with engine.connect() as conn:
                    conn.execute(text(ddl))
                    conn.commit()
                print("Added user_votes.genres column")
    except Exception as e:
        print(f"Schema check for user_votes.genres failed: {e}")

if __name__ == "__main__":
    init_database()


"""Database session management"""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from bot.config import Config

# Create engine with connection pool settings
engine = create_engine(
    Config.DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600    # Recycle connections after 1 hour
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get database session (generator for dependency injection)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """Context manager for database sessions with automatic rollback on error"""
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


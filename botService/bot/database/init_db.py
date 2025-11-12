"""Initialize database using Alembic migrations"""
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from alembic.config import Config as AlembicConfig
from alembic import command
from bot.config import Config
import logging

logger = logging.getLogger(__name__)


def init_database():
    """Initialize database by running Alembic migrations"""
    try:
        # Get path to alembic.ini
        alembic_ini_path = project_root / "alembic.ini"
        
        if not alembic_ini_path.exists():
            raise FileNotFoundError(
                f"Alembic config not found at {alembic_ini_path}. "
                "Make sure you're running from the botService directory."
            )
        
        # Create Alembic config
        alembic_cfg = AlembicConfig(str(alembic_ini_path))
        
        # Override database URL from environment/config
        alembic_cfg.set_main_option("sqlalchemy.url", Config.DATABASE_URL)
        
        # Check if alembic_version table exists (migrations already initialized)
        from sqlalchemy import inspect, text
        from bot.database.session import engine
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        has_alembic_version = "alembic_version" in tables
        
        if not has_alembic_version and tables:
            # Database exists but migrations haven't been run
            # Check if it looks like an old database created with create_all()
            if "users" in tables and "movies" in tables:
                logger.warning(
                    "Found existing database without Alembic version tracking. "
                    "Stamping database with initial migration version..."
                )
                # Check which tables exist to determine migration version
                has_new_tables = any(t in tables for t in ["episodes", "comments", "likes", "watch_history"])
                
                if has_new_tables:
                    # Database has new tables, stamp with latest
                    stamp_version = "head"
                else:
                    # Database only has old tables, stamp with first migration
                    stamp_version = "20251111_000001"
                
                # Stamp with the appropriate migration version
                command.stamp(alembic_cfg, stamp_version)
                logger.info(f"Database stamped with version {stamp_version}. Running any pending migrations...")
        
        # Run migrations to head
        logger.info(f"Running database migrations to head (database: {Config.DATABASE_URL})...")
        try:
            command.upgrade(alembic_cfg, "head")
        except Exception as upgrade_error:
            # If upgrade fails and we haven't stamped, try stamping first
            if not has_alembic_version and "already exists" in str(upgrade_error).lower():
                logger.warning("Migration failed due to existing tables. Attempting to stamp database...")
                command.stamp(alembic_cfg, "20251111_000001")
                # Try upgrade again
                command.upgrade(alembic_cfg, "head")
            else:
                raise
        
        logger.info("Database migrations applied successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()


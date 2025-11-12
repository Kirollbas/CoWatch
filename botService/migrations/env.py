import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy import create_engine

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add project path to import modules
if "/Users/nikitabogatyrev/mag/CoWatch/botService" not in sys.path:
    sys.path.insert(0, "/Users/nikitabogatyrev/mag/CoWatch/botService")

# Import SQLAlchemy Base and config for DATABASE_URL
from bot.database.session import Base  # noqa: E402
from bot.config import Config  # noqa: E402

# add your model's MetaData object here
target_metadata = Base.metadata


def get_url() -> str:
    # Prefer environment override if provided by alembic -x db_url=...
    x_db_url = context.get_x_argument(as_dictionary=True).get("db_url")
    if x_db_url:
        return x_db_url
    return Config.DATABASE_URL


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        render_as_batch=True,  # important for SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section) or {}
    url = get_url()

    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True,  # important for SQLite
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()



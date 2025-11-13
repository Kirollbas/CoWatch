"""add kinopoisk ratings and metadata

Revision ID: 20251111_000003
Revises: 20251111_000002
Create Date: 2025-11-11 00:30:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251111_000003"
down_revision = "20251111_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to movies table
    op.add_column("movies", sa.Column("name_original", sa.String(), nullable=True))
    
    # Kinopoisk API ratings
    op.add_column("movies", sa.Column("rating", sa.Float(), nullable=True))
    op.add_column("movies", sa.Column("rating_kinopoisk", sa.Float(), nullable=True))
    op.add_column("movies", sa.Column("rating_imdb", sa.Float(), nullable=True))
    op.add_column("movies", sa.Column("rating_film_critics", sa.Float(), nullable=True))
    op.add_column("movies", sa.Column("rating_await", sa.Float(), nullable=True))
    op.add_column("movies", sa.Column("rating_rf_critics", sa.Float(), nullable=True))
    
    # Additional metadata from Kinopoisk API
    op.add_column("movies", sa.Column("film_length", sa.Integer(), nullable=True))
    op.add_column("movies", sa.Column("age_rating", sa.String(), nullable=True))
    op.add_column("movies", sa.Column("slogan", sa.String(), nullable=True))
    op.add_column("movies", sa.Column("countries", sa.String(), nullable=True))
    op.add_column("movies", sa.Column("genres", sa.String(), nullable=True))
    
    # Timestamp for tracking updates
    op.add_column("movies", sa.Column("updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove columns in reverse order
    op.drop_column("movies", "updated_at")
    op.drop_column("movies", "genres")
    op.drop_column("movies", "countries")
    op.drop_column("movies", "slogan")
    op.drop_column("movies", "age_rating")
    op.drop_column("movies", "film_length")
    op.drop_column("movies", "rating_rf_critics")
    op.drop_column("movies", "rating_await")
    op.drop_column("movies", "rating_film_critics")
    op.drop_column("movies", "rating_imdb")
    op.drop_column("movies", "rating_kinopoisk")
    op.drop_column("movies", "rating")
    op.drop_column("movies", "name_original")



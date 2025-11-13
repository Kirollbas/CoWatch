"""add kinopoisk user tables

Revision ID: 20251113_000004
Revises: 20251111_000003
Create Date: 2025-11-13 16:00:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251113_000004"
down_revision = "20251111_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # user_kinopoisk - mapping Telegram user to Kinopoisk user ID
    op.create_table(
        "user_kinopoisk",
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("kp_user_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )
    
    # user_votes - user's Kinopoisk votes/preferences
    op.create_table(
        "user_votes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kinopoisk_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),  # FILM / TV_SERIES
        sa.Column("user_rating", sa.Integer(), nullable=False),  # 1-10 scale on KP
        sa.Column("poster_url", sa.String(), nullable=True),
        sa.Column("genres", sa.String(), nullable=True),  # comma-separated genres
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )
    op.create_index("uq_user_movie_vote", "user_votes", ["user_id", "kinopoisk_id"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_user_movie_vote", table_name="user_votes")
    op.drop_table("user_votes")
    op.drop_table("user_kinopoisk")


"""initial schema

Revision ID: 20251111_000001
Revises: 
Create Date: 2025-11-11 00:00:01
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251111_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enums
    movie_type = sa.Enum("movie", "series", name="movie_type")
    slot_status = sa.Enum("open", "full", "completed", name="slot_status")
    room_status = sa.Enum("active", "completed", name="room_status")
    movie_type.create(op.get_bind(), checkfirst=True)
    slot_status.create(op.get_bind(), checkfirst=True)
    room_status.create(op.get_bind(), checkfirst=True)

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("rating", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("total_ratings", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )

    # movies
    op.create_table(
        "movies",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("type", movie_type, nullable=False),
        sa.Column("kinopoisk_id", sa.String(), nullable=True),
        sa.Column("imdb_id", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("poster_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )

    # slots
    op.create_table(
        "slots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id"), nullable=False),
        sa.Column("creator_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("datetime", sa.DateTime(), nullable=False),
        sa.Column("min_participants", sa.Integer(), nullable=False, server_default=sa.text("2")),
        sa.Column("max_participants", sa.Integer(), nullable=True),
        sa.Column("status", slot_status, nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )

    # slot_participants
    op.create_table(
        "slot_participants",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("slot_id", sa.Integer(), sa.ForeignKey("slots.id"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )
    op.create_index("ix_slot_participants_slot_user", "slot_participants", ["slot_id", "user_id"], unique=True)

    # rooms
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("slot_id", sa.Integer(), sa.ForeignKey("slots.id"), nullable=False, unique=True),
        sa.Column("telegram_group_id", sa.BigInteger(), nullable=True),
        sa.Column("telegram_topic_id", sa.Integer(), nullable=True),
        sa.Column("status", room_status, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("discussion_end_time", sa.DateTime(), nullable=True),
    )

    # ratings
    op.create_table(
        "ratings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id"), nullable=False),
        sa.Column("rater_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rated_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )
    op.create_index("ix_rating_unique", "ratings", ["room_id", "rater_id", "rated_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_rating_unique", table_name="ratings")
    op.drop_table("ratings")
    op.drop_table("rooms")
    op.drop_index("ix_slot_participants_slot_user", table_name="slot_participants")
    op.drop_table("slot_participants")
    op.drop_table("slots")
    op.drop_table("movies")
    op.drop_table("users")

    # Enums last
    bind = op.get_bind()
    sa.Enum(name="room_status").drop(bind, checkfirst=True)
    sa.Enum(name="slot_status").drop(bind, checkfirst=True)
    sa.Enum(name="movie_type").drop(bind, checkfirst=True)



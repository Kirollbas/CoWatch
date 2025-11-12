"""extend content for episodes, comments, likes, watch history

Revision ID: 20251111_000002
Revises: 20251111_000001
Create Date: 2025-11-11 00:20:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251111_000002"
down_revision = "20251111_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # episodes
    op.create_table(
        "episodes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("series_id", sa.Integer(), sa.ForeignKey("movies.id"), nullable=False),
        sa.Column("season_number", sa.Integer(), nullable=False),
        sa.Column("episode_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("air_date", sa.DateTime(), nullable=True),
        sa.Column("runtime_minutes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )
    op.create_index(
        "ix_episode_unique_per_series",
        "episodes",
        ["series_id", "season_number", "episode_number"],
        unique=True,
    )

    # comments
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("episode_id", sa.Integer(), sa.ForeignKey("episodes.id"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("reply_to_id", sa.Integer(), sa.ForeignKey("comments.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )
    op.create_index("ix_comments_room_created_at", "comments", ["room_id", "created_at"], unique=False)

    # likes
    op.create_table(
        "likes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("comment_id", sa.Integer(), sa.ForeignKey("comments.id"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )
    op.create_index("ix_likes_unique", "likes", ["comment_id", "user_id"], unique=True)

    # watch_history
    op.create_table(
        "watch_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("movie_id", sa.Integer(), sa.ForeignKey("movies.id"), nullable=False),
        sa.Column("episode_id", sa.Integer(), sa.ForeignKey("episodes.id"), nullable=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id"), nullable=True),
        sa.Column("watched_at", sa.DateTime(), nullable=False, server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("progress_seconds", sa.Integer(), nullable=True),
        sa.Column("completed", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index(
        "ix_watch_history_user_movie_episode",
        "watch_history",
        ["user_id", "movie_id", "episode_id", "watched_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_watch_history_user_movie_episode", table_name="watch_history")
    op.drop_table("watch_history")
    op.drop_index("ix_likes_unique", table_name="likes")
    op.drop_table("likes")
    op.drop_index("ix_comments_room_created_at", table_name="comments")
    op.drop_table("comments")
    op.drop_index("ix_episode_unique_per_series", table_name="episodes")
    op.drop_table("episodes")



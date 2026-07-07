"""Add saved competition tracker rows.

Revision ID: 0006_add_saved_competitions
Revises: 0005_add_google_oauth
Create Date: 2026-07-07
"""

import sqlalchemy as sa
from alembic import op


revision = "0006_add_saved_competitions"
down_revision = "0005_add_google_oauth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    # Revision 0001 creates tables from current metadata for clean installs, so
    # fresh databases can already have this table before 0006 runs.
    if "saved_competitions" in inspector.get_table_names():
        return
    op.create_table(
        "saved_competitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("competition_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="interested"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("completed_requirement_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "competition_id", name="uq_user_competition"),
    )
    op.create_index("ix_saved_competitions_user_id", "saved_competitions", ["user_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "saved_competitions" in inspector.get_table_names():
        op.drop_table("saved_competitions")

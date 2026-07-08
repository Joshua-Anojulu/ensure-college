"""Add recommendation-letter tracker rows.

Revision ID: 0007_add_recommendation_letters
Revises: 0006_add_saved_competitions
Create Date: 2026-07-07
"""

import sqlalchemy as sa
from alembic import op


revision = "0007_add_recommendation_letters"
down_revision = "0006_add_saved_competitions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    # Revision 0001 creates tables from current metadata for clean installs, so
    # fresh databases can already have this table before 0007 runs.
    if "recommendation_letters" in inspector.get_table_names():
        return
    op.create_table(
        "recommendation_letters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommender_name", sa.String(length=200), nullable=False),
        sa.Column("relationship", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="requested"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_recommendation_letters_user_id", "recommendation_letters", ["user_id"]
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "recommendation_letters" in inspector.get_table_names():
        op.drop_table("recommendation_letters")

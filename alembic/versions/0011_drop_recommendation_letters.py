"""Drop the recommendation-letter tracker table.

Revision ID: 0011_drop_recommendation_letters
Revises: 0010_add_match_alert_state
Create Date: 2026-07-09

The manual rec-letter tracker is replaced by a rollup computed from each saved
opportunity's application_requirements, so the dedicated table is no longer
needed.
"""

import sqlalchemy as sa
from alembic import op


revision = "0011_drop_recommendation_letters"
down_revision = "0010_add_match_alert_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "recommendation_letters" in inspector.get_table_names():
        op.drop_table("recommendation_letters")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
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

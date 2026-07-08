"""Track which opportunities a user has been alerted about (new-match alerts).

Revision ID: 0010_add_match_alert_state
Revises: 0009_pipeline_check
Create Date: 2026-07-08
"""

import sqlalchemy as sa
from alembic import op


revision = "0010_add_match_alert_state"
down_revision = "0009_pipeline_check"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("users")}
    # NULL means "not yet baselined": the first run records current matches
    # without emailing, so users are only alerted about opportunities added later.
    if "alerted_opportunity_ids" not in columns:
        op.add_column("users", sa.Column("alerted_opportunity_ids", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("users")}
    if "alerted_opportunity_ids" in columns:
        op.drop_column("users", "alerted_opportunity_ids")

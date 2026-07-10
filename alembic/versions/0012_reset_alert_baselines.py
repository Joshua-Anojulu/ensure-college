"""Reset new-match alert baselines for the matcher-improvements deploy.

Revision ID: 0012_reset_alert_baselines
Revises: 0011_drop_recommendation_letters
Create Date: 2026-07-10

Data-only migration. Related-field scoring promotes some long-eligible
"possible" matches to "strong"; without a reset, the next weekly alert run
would email every subscriber about items that are not actually new. Setting
``users.alerted_opportunity_ids`` back to NULL reuses the alert system's
first-run semantics (``app/alerts.py``): a NULL baseline is recorded silently
and only later additions ever alert. Downgrade is a no-op: the baselines this
clears are derived state that the next run rebuilds.
"""

import sqlalchemy as sa
from alembic import op

revision = "0012_reset_alert_baselines"
down_revision = "0011_drop_recommendation_letters"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("UPDATE users SET alerted_opportunity_ids = NULL"))


def downgrade() -> None:
    pass

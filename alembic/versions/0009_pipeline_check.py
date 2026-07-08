"""No-op migration to verify migrations auto-apply on deploy.

Revision ID: 0009_pipeline_check
Revises: 0008_add_reminder_prefs
Create Date: 2026-07-08

Changes no schema. Its only purpose is to confirm that a freshly deployed
migration reaches the Neon production database without a manual
``alembic upgrade head`` (i.e. that startup/build migrations are wired up).
Safe if the pipeline is still broken: no table or column changes, so the
running code is unaffected whether Neon is at 0008 or 0009.
"""

revision = "0009_pipeline_check"
down_revision = "0008_add_reminder_prefs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

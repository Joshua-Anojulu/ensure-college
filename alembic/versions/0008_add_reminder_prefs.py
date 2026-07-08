"""Add deadline-reminder preferences to users.

Revision ID: 0008_add_reminder_prefs
Revises: 0007_add_recommendation_letters
Create Date: 2026-07-08
"""

import secrets

import sqlalchemy as sa
from alembic import op


revision = "0008_add_reminder_prefs"
down_revision = "0007_add_recommendation_letters"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("users")}

    if "reminders_enabled" not in columns:
        op.add_column(
            "users",
            sa.Column("reminders_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    if "reminder_unsubscribe_token" not in columns:
        op.add_column(
            "users",
            sa.Column("reminder_unsubscribe_token", sa.String(length=64), nullable=True),
        )
        # Backfill a unique token for existing accounts.
        users = sa.table(
            "users",
            sa.column("id", sa.Integer),
            sa.column("reminder_unsubscribe_token", sa.String),
        )
        rows = bind.execute(sa.select(users.c.id)).fetchall()
        for (user_id,) in rows:
            bind.execute(
                users.update()
                .where(users.c.id == user_id)
                .values(reminder_unsubscribe_token=secrets.token_urlsafe(32))
            )
        op.create_index(
            "ix_users_reminder_unsubscribe_token",
            "users",
            ["reminder_unsubscribe_token"],
            unique=True,
        )
    if "reminder_last_sent_on" not in columns:
        op.add_column("users", sa.Column("reminder_last_sent_on", sa.Date(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("users")}
    if "reminder_last_sent_on" in columns:
        op.drop_column("users", "reminder_last_sent_on")
    if "reminder_unsubscribe_token" in columns:
        op.drop_index("ix_users_reminder_unsubscribe_token", table_name="users")
        op.drop_column("users", "reminder_unsubscribe_token")
    if "reminders_enabled" in columns:
        op.drop_column("users", "reminders_enabled")

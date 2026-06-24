"""Add one-time password-reset tokens and credential-versioned sessions.

Revision ID: 0003_add_password_reset_tokens
Revises: 0002_add_requirement_progress
Create Date: 2026-06-21
"""

import sqlalchemy as sa
from alembic import op


revision = "0003_add_password_reset_tokens"
down_revision = "0002_add_requirement_progress"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    # Revision 0001 creates clean databases from current metadata, so a fresh
    # install may already have both this column and the token table.
    if "auth_version" not in user_columns:
        op.add_column(
            "users",
            sa.Column("auth_version", sa.Integer(), nullable=False, server_default="0"),
        )

    if "password_reset_tokens" not in inspector.get_table_names():
        op.create_table(
            "password_reset_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])
        op.create_index(
            "ix_password_reset_tokens_token_hash",
            "password_reset_tokens",
            ["token_hash"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "password_reset_tokens" in inspector.get_table_names():
        op.drop_table("password_reset_tokens")
    user_columns = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    if "auth_version" in user_columns:
        op.drop_column("users", "auth_version")

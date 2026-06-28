"""Add Google OAuth account linkage.

Revision ID: 0005_add_google_oauth
Revises: 0004_add_saved_programs
Create Date: 2026-06-27
"""

import sqlalchemy as sa
from alembic import op


revision = "0005_add_google_oauth"
down_revision = "0004_add_saved_programs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"]: column for column in inspector.get_columns("users")}
    indexes = {index["name"] for index in inspector.get_indexes("users")}

    with op.batch_alter_table("users") as batch_op:
        password_hash = columns.get("password_hash")
        if password_hash is not None and not password_hash["nullable"]:
            batch_op.alter_column(
                "password_hash",
                existing_type=sa.String(length=255),
                nullable=True,
            )
        if "google_sub" not in columns:
            batch_op.add_column(sa.Column("google_sub", sa.String(length=255), nullable=True))

    if "ix_users_google_sub" not in indexes:
        op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"]: column for column in inspector.get_columns("users")}
    indexes = {index["name"] for index in inspector.get_indexes("users")}

    if "ix_users_google_sub" in indexes:
        op.drop_index("ix_users_google_sub", table_name="users")

    # Google-only users cannot satisfy the old NOT NULL password constraint.
    op.execute("DELETE FROM users WHERE password_hash IS NULL")

    with op.batch_alter_table("users") as batch_op:
        if "google_sub" in columns:
            batch_op.drop_column("google_sub")
        password_hash = columns.get("password_hash")
        if password_hash is not None and password_hash["nullable"]:
            batch_op.alter_column(
                "password_hash",
                existing_type=sa.String(length=255),
                nullable=False,
            )

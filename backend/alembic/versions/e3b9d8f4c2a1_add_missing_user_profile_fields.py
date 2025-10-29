"""Add missing user profile fields (first_name, last_name, is_verified)

Revision ID: e3b9d8f4c2a1
Revises: add_sessions_table
Create Date: 2025-10-29 12:00:00

Purpose:
    The current `User` SQLModel defines `first_name`, `last_name`, and `is_verified` columns
    which are absent from the physical `users` table created by earlier migrations.
    This mismatch causes INSERT failures (500 errors) during /auth/register since ORM
    attempts to write those fields. This migration adds the missing columns in an
    idempotent way.

Strategy:
    * Add columns with server_default values to satisfy NOT NULL constraints for existing rows.
    * Backfill existing rows with derived names (from email local part) if present.
    * Optionally (commented) remove server_default where supported; SQLite requires table rebuild
      for altering defaults, so we retain them for development convenience.

Idempotency:
    We inspect existing columns and only add those that are missing. This allows repeated runs
    or pre-populated test databases without failure.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e3b9d8f4c2a1"
down_revision: Union[str, None] = "add_sessions_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _derive_name_from_email(conn) -> None:
    """Populate first_name/last_name for existing users where we just added columns.

    Heuristic:
        * Split local part of email at '.', '-', '_'.
        * First token -> first_name (capitalized), last token -> last_name (capitalized).
        * If only one token, reuse for both first and last.
    This is a best-effort placeholder so UI renders something coherent.
    """
    # SQLite string functions used for portability; complex parsing done in Python.
    result = conn.execute(sa.text("SELECT id, email FROM users"))
    rows = result.fetchall()
    update_stmt = sa.text(
        "UPDATE users SET first_name = :first_name, last_name = :last_name WHERE id = :id"
    )
    for r in rows:
        user_id, email = r
        local = email.split("@")[0] if email else "user"
        # Tokenize
        for sep in [".", "-", "_"]:
            local = local.replace(sep, " ")
        parts = [p for p in local.split() if p]
        if not parts:
            first_name = last_name = "User"
        elif len(parts) == 1:
            first_name = last_name = parts[0].capitalize()
        else:
            first_name = parts[0].capitalize()
            last_name = parts[-1].capitalize()
        conn.execute(update_stmt, {"first_name": first_name, "last_name": last_name, "id": user_id})


def upgrade() -> None:  # pragma: no cover - migration logic
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Create users table if entirely missing (defensive for environments where earlier migration didn't run)
    if 'users' not in inspector.get_table_names():
        op.create_table(
            'users',
            sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False, unique=True, index=True),
            sa.Column('password_hash', sa.String(length=255), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column('failed_attempts', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('lock_until', sa.DateTime(timezone=True), nullable=True),
            # New columns added directly when creating table
            sa.Column('first_name', sa.String(length=100), nullable=False, server_default='User'),
            sa.Column('last_name', sa.String(length=100), nullable=False, server_default='User'),
            sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        )
        # After creating, optionally derive actual names
        _derive_name_from_email(conn)
        return

    existing_cols = {c['name'] for c in inspector.get_columns('users')}

    # Add first_name column if missing
    if 'first_name' not in existing_cols:
        op.add_column(
            'users',
            sa.Column('first_name', sa.String(length=100), nullable=False, server_default='User'),
        )

    # Add last_name column if missing
    if 'last_name' not in existing_cols:
        op.add_column(
            'users',
            sa.Column('last_name', sa.String(length=100), nullable=False, server_default='User'),
        )

    # Add is_verified column if missing
    if 'is_verified' not in existing_cols:
        op.add_column(
            'users',
            sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        )

    # Backfill names only if we just added them
    new_cols = {c['name'] for c in inspector.get_columns('users')}
    if ('first_name' in new_cols and 'first_name' not in existing_cols) or (
        'last_name' in new_cols and 'last_name' not in existing_cols
    ):
        _derive_name_from_email(conn)

    # Optional removal of server_default (kept for SQLite convenience)


def downgrade() -> None:  # pragma: no cover - migration logic
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = {c["name"] for c in inspector.get_columns("users")}
    # Drop in reverse logical order (safe checks)
    if "is_verified" in existing_cols:
        op.drop_column("users", "is_verified")
    if "last_name" in existing_cols:
        op.drop_column("users", "last_name")
    if "first_name" in existing_cols:
        op.drop_column("users", "first_name")

"""Add lockout fields to users table

Revision ID: add_auth_lockout_fields
Revises: b4e7c1d9aa10
Create Date: 2025-10-20

This migration originally branched off af9d234e1b5c creating a second head.
We updated its down_revision to a3c9824a5658 to produce a single linear chain:
6934fbabba4f -> af9d234e1b5c -> a3c9824a5658 -> add_auth_lockout_fields -> add_sessions_table.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

# revision identifiers, used by Alembic.
revision: str = "add_auth_lockout_fields"
down_revision: Union[str, None] = "b4e7c1d9aa10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Idempotent additions; skip if columns already present (tests may pre-create schema).
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols = [c['name'] for c in inspector.get_columns('users')]
    if 'failed_attempts' not in existing_cols:
        op.add_column("users", sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"))
        # Keep default for SQLite simplicity.
    if 'lock_until' not in existing_cols:
        op.add_column("users", sa.Column("lock_until", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "lock_until")
    op.drop_column("users", "failed_attempts")
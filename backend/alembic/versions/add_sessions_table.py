"""Create sessions table

Revision ID: add_sessions_table
Revises: add_auth_lockout_fields
Create Date: 2025-10-20

Part of linear chain after resolving multi-head issue.
Chain: 6934fbabba4f -> af9d234e1b5c -> a3c9824a5658 -> add_auth_lockout_fields -> add_sessions_table.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "add_sessions_table"
down_revision: Union[str, None] = "add_auth_lockout_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'sessions' not in inspector.get_table_names():
        op.create_table(
            "sessions",
            sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
            sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("demo", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        )
    else:
        # Add missing columns if table pre-created without them
        existing_cols = {c['name'] for c in inspector.get_columns('sessions')}
        if 'demo' not in existing_cols:
            op.add_column("sessions", sa.Column("demo", sa.Boolean(), nullable=False, server_default=sa.text("0")))
        if 'revoked_at' not in existing_cols:
            op.add_column("sessions", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
        if 'expires_at' not in existing_cols:
            op.add_column("sessions", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False))
        if 'last_activity_at' not in existing_cols:
            op.add_column("sessions", sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
        if 'created_at' not in existing_cols:
            op.add_column("sessions", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
        if 'user_id' not in existing_cols:
            op.add_column("sessions", sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False))
        if 'id' not in existing_cols:
            op.add_column("sessions", sa.Column("id", sa.String(length=36), primary_key=True, nullable=False))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'sessions' in inspector.get_table_names():
        op.drop_table("sessions")
"""Create users table

Revision ID: b4e7c1d9aa10
Revises: a3c9824a5658
Create Date: 2025-10-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

revision = "b4e7c1d9aa10"
down_revision = "a3c9824a5658"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'users' not in inspector.get_table_names():
        op.create_table(
            "users",
            sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False, unique=True),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'users' in inspector.get_table_names():
        indexes = {idx['name'] for idx in inspector.get_indexes('users')}
        if 'ix_users_email' in indexes:
            op.drop_index("ix_users_email", table_name="users")
        op.drop_table("users")
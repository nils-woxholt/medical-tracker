"""Create users table

Revision ID: 7b1c2d9f2e01
Revises: 6934fbabba4f
Create Date: 2025-10-20

Adds initial users table required by later auth-related migrations.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

# revision identifiers, used by Alembic.
revision = "7b1c2d9f2e01"
down_revision = "6934fbabba4f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
    )


def downgrade() -> None:
    op.drop_table("users")
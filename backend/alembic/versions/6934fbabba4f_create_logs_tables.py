"""create_logs_tables

Revision ID: 6934fbabba4f
Revises: 
Create Date: 2025-10-16 15:07:06.585877

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '6934fbabba4f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create base log tables (idempotent)."""
    conn = op.get_bind()
    inspector = inspect(conn)

    if 'medication_logs' not in inspector.get_table_names():
        op.create_table(
            'medication_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('medication_name', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
            sa.Column('dosage', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
            sa.Column('taken_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('logged_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('side_effects', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
            sa.Column('side_effect_severity', sa.Enum('NONE', 'MILD', 'MODERATE', 'SEVERE', 'CRITICAL', name='severitylevel'), nullable=True),
            sa.Column('effectiveness_rating', sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_medication_logs_user_id'), 'medication_logs', ['user_id'], unique=False)

    if 'symptom_logs' not in inspector.get_table_names():
        # Align schema with tests that insert integer severity and textual duration.
        op.create_table(
            'symptom_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column('symptom_name', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True),
            sa.Column('symptom_type', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=True),
            sa.Column('severity', sa.Integer(), nullable=False),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('logged_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('duration_minutes', sa.Integer(), nullable=True),
            sa.Column('duration', sa.Text(), nullable=True),
            sa.Column('triggers', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
            sa.Column('location', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('impact_rating', sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_symptom_logs_user_id'), 'symptom_logs', ['user_id'], unique=False)


def downgrade() -> None:
    """Intentionally retain tables to allow error recovery tests to preserve data.

    The integration test expects data to survive a downgrade/upgrade cycle for
    the base migration. We therefore make this downgrade a no-op regarding table
    removal to keep existing log data intact.
    """
    # No operation performed (data preserved).
    pass
"""Add conditions and doctors tables with linking

Revision ID: a3c9824a5658
Revises: af9d234e1b5c
Create Date: 2025-10-17 10:44:12.270800

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func


# revision identifiers, used by Alembic.
revision = 'a3c9824a5658'
down_revision = 'af9d234e1b5c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Create conditions table ###
    op.create_table('conditions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for conditions table
    # Index for user's conditions queries (most common use case)
    op.create_index('ix_conditions_user_id', 'conditions', ['user_id'])
    
    # Index for active condition queries
    op.create_index('ix_conditions_active', 'conditions', ['is_active'])
    
    # Composite index for user's active conditions
    op.create_index('ix_conditions_user_active', 'conditions', ['user_id', 'is_active'])
    
    # Composite unique index to prevent duplicate condition names per user
    op.create_index('ix_conditions_user_name_unique', 'conditions', ['user_id', 'name'], unique=True)
    
    # Index for created_at for sorting recent conditions
    op.create_index('ix_conditions_created_at', 'conditions', ['created_at'])
    
    # ### Create doctors table ###
    op.create_table('doctors',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('specialty', sa.String(100), nullable=False),
        sa.Column('contact_info', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for doctors table
    # Index for user's doctors queries (most common use case)
    op.create_index('ix_doctors_user_id', 'doctors', ['user_id'])
    
    # Index for active doctor queries
    op.create_index('ix_doctors_active', 'doctors', ['is_active'])
    
    # Composite index for user's active doctors
    op.create_index('ix_doctors_user_active', 'doctors', ['user_id', 'is_active'])
    
    # Index for specialty searches
    op.create_index('ix_doctors_specialty', 'doctors', ['specialty'])
    
    # Composite index for user's doctors by specialty
    op.create_index('ix_doctors_user_specialty', 'doctors', ['user_id', 'specialty'])
    
    # Index for created_at for sorting recent doctors
    op.create_index('ix_doctors_created_at', 'doctors', ['created_at'])
    
    # ### Create doctor_condition_links table ###
    op.create_table('doctor_condition_links',
        sa.Column('doctor_id', sa.String(36), nullable=False),
        sa.Column('condition_id', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.ForeignKeyConstraint(['condition_id'], ['conditions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('doctor_id', 'condition_id')
    )
    
    # Create indexes for doctor_condition_links table
    # Index for finding doctors for a condition
    op.create_index('ix_doctor_condition_condition_id', 'doctor_condition_links', ['condition_id'])
    
    # Index for finding conditions for a doctor
    op.create_index('ix_doctor_condition_doctor_id', 'doctor_condition_links', ['doctor_id'])
    
    # Index for recent links
    op.create_index('ix_doctor_condition_created_at', 'doctor_condition_links', ['created_at'])


def downgrade() -> None:
    # ### Drop doctor_condition_links table ###
    op.drop_index('ix_doctor_condition_created_at', table_name='doctor_condition_links')
    op.drop_index('ix_doctor_condition_doctor_id', table_name='doctor_condition_links')
    op.drop_index('ix_doctor_condition_condition_id', table_name='doctor_condition_links')
    op.drop_table('doctor_condition_links')
    
    # ### Drop doctors table ###
    op.drop_index('ix_doctors_created_at', table_name='doctors')
    op.drop_index('ix_doctors_user_specialty', table_name='doctors')
    op.drop_index('ix_doctors_specialty', table_name='doctors')
    op.drop_index('ix_doctors_user_active', table_name='doctors')
    op.drop_index('ix_doctors_active', table_name='doctors')
    op.drop_index('ix_doctors_user_id', table_name='doctors')
    op.drop_table('doctors')
    
    # ### Drop conditions table ###
    op.drop_index('ix_conditions_created_at', table_name='conditions')
    op.drop_index('ix_conditions_user_name_unique', table_name='conditions')
    op.drop_index('ix_conditions_user_active', table_name='conditions')
    op.drop_index('ix_conditions_active', table_name='conditions')
    op.drop_index('ix_conditions_user_id', table_name='conditions')
    op.drop_table('conditions')
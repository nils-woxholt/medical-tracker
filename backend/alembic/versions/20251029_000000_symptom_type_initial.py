"""Initial migration for SymptomType and SymptomLog (Feature 004).

Revision ID format uses date for traceability in feature branch.
"""
from __future__ import annotations

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251029_000000_symptom_type_initial"
down_revision: Union[str, None] = None  # set to previous revision id when integrating
branch_labels: Union[str, Sequence[str], None] = ("feature-004",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "symptom_type",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500)),
        sa.Column("category", sa.String(length=100)),
        sa.Column("default_severity_numeric", sa.Integer(), nullable=False),
        sa.Column("default_impact_numeric", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_symptom_type_user_name_unique",
        "symptom_type",
        ["user_id", "name"],
        unique=True,
    )
    op.create_index("ix_symptom_type_active", "symptom_type", ["active"])

    op.create_table(
        "symptom_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symptom_type_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime()),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("severity_numeric", sa.Integer(), nullable=False),
        sa.Column("impact_numeric", sa.Integer(), nullable=False),
        sa.Column("severity_label", sa.String(length=20)),
        sa.Column("impact_label", sa.String(length=20)),
        sa.Column("notes", sa.String(length=1000)),
        sa.Column("confirmation_long_duration", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["symptom_type_id"], ["symptom_type.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_symptom_log_symptom_type_id", "symptom_log", ["symptom_type_id"])
    op.create_index("ix_symptom_log_user_started", "symptom_log", ["user_id", "started_at"])

    # Add check constraints matching validation rules.
    op.create_check_constraint(
        "ck_symptom_log_severity_numeric_range",
        "symptom_log",
        "severity_numeric BETWEEN 1 AND 10",
    )
    op.create_check_constraint(
        "ck_symptom_log_impact_numeric_range",
        "symptom_log",
        "impact_numeric BETWEEN 1 AND 10",
    )
    op.create_check_constraint(
        "ck_symptom_log_duration_max",
        "symptom_log",
        "duration_minutes IS NULL OR duration_minutes <= 1440",
    )
    op.create_check_constraint(
        "ck_symptom_log_long_duration_confirmation",
        "symptom_log",
        "duration_minutes IS NULL OR duration_minutes <= 720 OR confirmation_long_duration = 1",
    )


def downgrade() -> None:
    op.drop_table("symptom_log")
    op.drop_table("symptom_type")

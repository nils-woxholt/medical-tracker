"""Initial migration for SymptomType and SymptomLog (Feature 004).

Finalized for integration into linear chain after existing head `e3b9d8f4c2a1`.
Adds FK to users.id (string PK) and CHECK constraints for numeric ranges & duration rules.
"""
from __future__ import annotations

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

# revision identifiers, used by Alembic.
revision: str = "20251029_000000_symptom_type_initial"
down_revision: Union[str, None] = "e3b9d8f4c2a1"  # previous head, maintain linear history
branch_labels: Union[str, Sequence[str], None] = ("feature-004",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:  # pragma: no cover - migration logic
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    existing_tables = set(inspector.get_table_names())

    if "symptom_type" not in existing_tables:
        op.create_table(
            "symptom_type",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.String(length=500)),
            sa.Column("category", sa.String(length=100)),
            sa.Column("default_severity_numeric", sa.Integer(), nullable=False),
            sa.Column("default_impact_numeric", sa.Integer(), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
            # Default numeric ranges enforced at DB level for safety
            sa.CheckConstraint("default_severity_numeric BETWEEN 1 AND 10", name="ck_symptom_type_default_severity_range"),
            sa.CheckConstraint("default_impact_numeric BETWEEN 1 AND 10", name="ck_symptom_type_default_impact_range"),
        )
        # Indexes (wrap in try in case of race / prior manual creation)
        try:
            op.create_index(
                "ix_symptom_type_user_name_unique",
                "symptom_type",
                ["user_id", "name"],
                unique=True,
            )
        except Exception:  # pragma: no cover - defensive
            pass
        try:
            op.create_index("ix_symptom_type_active", "symptom_type", ["active"])
        except Exception:  # pragma: no cover - defensive
            pass

    if "symptom_log" not in existing_tables:
        op.create_table(
            "symptom_log",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("symptom_type_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ended_at", sa.DateTime(timezone=True)),
            sa.Column("duration_minutes", sa.Integer()),
            sa.Column("severity_numeric", sa.Integer(), nullable=False),
            sa.Column("impact_numeric", sa.Integer(), nullable=False),
            sa.Column("severity_label", sa.String(length=20)),
            sa.Column("impact_label", sa.String(length=20)),
            sa.Column("notes", sa.String(length=1000)),
            sa.Column("confirmation_long_duration", sa.Boolean()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
            sa.ForeignKeyConstraint(["symptom_type_id"], ["symptom_type.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
            sa.CheckConstraint("severity_numeric BETWEEN 1 AND 10", name="ck_symptom_log_severity_numeric_range"),
            sa.CheckConstraint("impact_numeric BETWEEN 1 AND 10", name="ck_symptom_log_impact_numeric_range"),
            sa.CheckConstraint(
                "duration_minutes IS NULL OR (duration_minutes BETWEEN 1 AND 1440)",
                name="ck_symptom_log_duration_range",
            ),
            sa.CheckConstraint(
                "duration_minutes IS NULL OR NOT (duration_minutes > 720 AND (confirmation_long_duration IS NULL OR confirmation_long_duration = 0))",
                name="ck_symptom_log_long_duration_confirmation",
            ),
        )
        try:
            op.create_index("ix_symptom_log_symptom_type_id", "symptom_log", ["symptom_type_id"])
        except Exception:  # pragma: no cover - defensive
            pass
        try:
            op.create_index("ix_symptom_log_user_started", "symptom_log", ["user_id", "started_at"])
        except Exception:  # pragma: no cover - defensive
            pass

    # If tables already existed, we deliberately do not mutate them here to keep migration idempotent.


def downgrade() -> None:  # pragma: no cover - migration logic
    # Drop child table first due to FK dependency
    if op.get_bind().dialect.has_table(op.get_bind(), "symptom_log"):
        op.drop_table("symptom_log")
    if op.get_bind().dialect.has_table(op.get_bind(), "symptom_type"):
        op.drop_table("symptom_type")

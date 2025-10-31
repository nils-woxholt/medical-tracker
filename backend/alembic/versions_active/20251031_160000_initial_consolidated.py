"""Initial consolidated schema (clean first release).

Active copy used by Alembic (Option A). Original historical fragmented migrations
are archived under deprecated/ and the prior consolidated file under versions/ is
retained only for reference. This file contains the full schema creation logic.
"""

from __future__ import annotations

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

# Revision identifiers
revision: str = "20251031_160000_initial_consolidated"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = ("clean-initial",)
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:  # pragma: no cover - migration logic
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lock_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_name", sa.String(length=100), nullable=False, server_default="User"),
        sa.Column("last_name", sa.String(length=100), nullable=False, server_default="User"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
    )

    # sessions
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("demo", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"], unique=False)

    # medications
    op.create_table(
        "medications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.UniqueConstraint("name", name="uq_medications_name"),
    )
    op.create_index("ix_medications_active", "medications", ["is_active"])
    op.create_index("ix_medications_active_name", "medications", ["is_active", "name"])
    op.create_index("ix_medications_created_at", "medications", ["created_at"])
    op.create_index("ix_medications_updated_at", "medications", ["updated_at"])

    # conditions
    op.create_table(
        "conditions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_conditions_user_id", "conditions", ["user_id"])
    op.create_index("ix_conditions_active", "conditions", ["is_active"])
    op.create_index("ix_conditions_user_active", "conditions", ["user_id", "is_active"])
    op.create_index("ix_conditions_user_name_unique", "conditions", ["user_id", "name"], unique=True)
    op.create_index("ix_conditions_created_at", "conditions", ["created_at"])

    # doctors
    op.create_table(
        "doctors",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("specialty", sa.String(length=100), nullable=False),
        sa.Column("contact_info", sa.String(length=200)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_doctors_user_id", "doctors", ["user_id"])
    op.create_index("ix_doctors_active", "doctors", ["is_active"])
    op.create_index("ix_doctors_user_active", "doctors", ["user_id", "is_active"])
    op.create_index("ix_doctors_specialty", "doctors", ["specialty"])
    op.create_index("ix_doctors_user_specialty", "doctors", ["user_id", "specialty"])
    op.create_index("ix_doctors_created_at", "doctors", ["created_at"])

    # doctor_condition_links
    op.create_table(
        "doctor_condition_links",
        sa.Column("doctor_id", sa.String(length=36), nullable=False),
        sa.Column("condition_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctors.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["condition_id"], ["conditions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("doctor_id", "condition_id"),
    )
    op.create_index("ix_doctor_condition_condition_id", "doctor_condition_links", ["condition_id"])
    op.create_index("ix_doctor_condition_doctor_id", "doctor_condition_links", ["doctor_id"])
    op.create_index("ix_doctor_condition_created_at", "doctor_condition_links", ["created_at"])

    # symptom_type
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint("default_severity_numeric BETWEEN 1 AND 10", name="ck_symptom_type_default_severity_range"),
        sa.CheckConstraint("default_impact_numeric BETWEEN 1 AND 10", name="ck_symptom_type_default_impact_range"),
    )
    op.create_index("ix_symptom_type_user_name_unique", "symptom_type", ["user_id", "name"], unique=True)
    op.create_index("ix_symptom_type_active", "symptom_type", ["active"])

    # symptom_log
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
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
    op.create_index("ix_symptom_log_symptom_type_id", "symptom_log", ["symptom_type_id"])
    op.create_index("ix_symptom_log_user_started", "symptom_log", ["user_id", "started_at"])

    # audit_entry
    op.create_table(
        "audit_entry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=func.now()),
        sa.Column("diff", sa.JSON(), nullable=True),
    )
    op.create_index("ix_audit_entry_entity", "audit_entry", ["entity_type", "entity_id"])
    op.create_index("ix_audit_entry_action", "audit_entry", ["action"])

    # Legacy compatibility tables
    op.create_table(
        "medication_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("medication_name", sa.String(length=200), nullable=False),
        sa.Column("dosage", sa.String(length=100), nullable=False),
        sa.Column("taken_at", sa.DateTime(timezone=True)),
        sa.Column("logged_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text()),
        sa.Column("side_effects", sa.String(length=500)),
        sa.Column(
            "side_effect_severity",
            sa.Enum("NONE", "MILD", "MODERATE", "SEVERE", "CRITICAL", name="severitylevel"),
        ),
        sa.Column("effectiveness_rating", sa.Integer()),
    )
    op.create_index("ix_medication_logs_user_id", "medication_logs", ["user_id"])

    op.create_table(
        "symptom_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("symptom_name", sa.String(length=200)),
        sa.Column("symptom_type", sa.String(length=200)),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("logged_at", sa.DateTime(timezone=True)),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("duration", sa.Text()),
        sa.Column("triggers", sa.String(length=500)),
        sa.Column("location", sa.String(length=100)),
        sa.Column("notes", sa.Text()),
        sa.Column("impact_rating", sa.Integer()),
    )
    op.create_index("ix_symptom_logs_user_id", "symptom_logs", ["user_id"])


def downgrade() -> None:  # pragma: no cover - migration logic
    # Drop in dependency order (children first)
    for table in [
        "audit_entry",
        "symptom_logs",
        "medication_logs",
        "symptom_log",
        "symptom_type",
        "doctor_condition_links",
        "doctors",
        "conditions",
        "medications",
        "sessions",
        "users",
    ]:
        bind = op.get_bind()
        if bind.dialect.has_table(bind, table):
            op.drop_table(table)

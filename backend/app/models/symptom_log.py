"""SQLModel for SymptomLog entity (Feature 004).

Stores individual symptom occurrences referencing SymptomType.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Column, DateTime, ForeignKey
from sqlalchemy import CheckConstraint


class SymptomLogBase(SQLModel):
    # SQLModel default table naming removes underscore: SymptomType -> symptomtype
    symptom_type_id: int = Field(foreign_key="symptomtype.id", index=True)
    started_at: datetime = Field(sa_column=Column(DateTime(timezone=False), nullable=False))
    ended_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=False), nullable=True))
    severity_numeric: int = Field(ge=1, le=10)
    impact_numeric: int = Field(ge=1, le=10)
    notes: Optional[str] = Field(default=None, max_length=1000)
    confirmation_long_duration: Optional[bool] = Field(
        default=None,
        description="Must be True when duration_minutes > 720 and <= 1440",
    )


class SymptomLog(SymptomLogBase, table=True):  # type: ignore[call-arg]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, description="User id (string UUID)")
    duration_minutes: Optional[int] = Field(
        default=None, description="Total duration minutes (calculated on close)", ge=1, le=1440
    )
    severity_label: Optional[str] = Field(default=None, description="Derived from severity_numeric")
    impact_label: Optional[str] = Field(default=None, description="Derived from impact_numeric")
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))
    __table_args__ = (
        # severity & impact numeric range (redundant with pydantic but enforced at DB)
        CheckConstraint("severity_numeric BETWEEN 1 AND 10", name="ck_symptomlog_severity_range"),
        CheckConstraint("impact_numeric BETWEEN 1 AND 10", name="ck_symptomlog_impact_range"),
        # duration range or NULL
        CheckConstraint("duration_minutes IS NULL OR (duration_minutes BETWEEN 1 AND 1440)", name="ck_symptomlog_duration_range"),
        # long-duration confirmation rule: if duration_minutes > 720 must have confirmation_long_duration = 1
        CheckConstraint(
            "duration_minutes IS NULL OR NOT (duration_minutes > 720 AND (confirmation_long_duration IS NULL OR confirmation_long_duration = 0))",
            name="ck_symptomlog_long_duration_confirmation",
        ),
    )


class SymptomLogCreate(SymptomLogBase):
    user_id: int


class SymptomLogRead(SymptomLogBase):
    id: int
    user_id: int
    duration_minutes: Optional[int]
    severity_label: Optional[str]
    impact_label: Optional[str]
    created_at: datetime

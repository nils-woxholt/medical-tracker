"""SQLModel for SymptomLog entity (Feature 004).

Stores individual symptom occurrences referencing SymptomType.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Column, DateTime, ForeignKey


class SymptomLogBase(SQLModel):
    symptom_type_id: int = Field(foreign_key="symptom_type.id", index=True)
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
    __tablename__ = "symptom_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    duration_minutes: Optional[int] = Field(
        default=None, description="Total duration minutes (calculated on close)", ge=1, le=1440
    )
    severity_label: Optional[str] = Field(default=None, description="Derived from severity_numeric")
    impact_label: Optional[str] = Field(default=None, description="Derived from impact_numeric")
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=False), nullable=False))

    # CHECK constraints will be added via Alembic migration for enforcement.


class SymptomLogCreate(SymptomLogBase):
    user_id: int


class SymptomLogRead(SymptomLogBase):
    id: int
    user_id: int
    duration_minutes: Optional[int]
    severity_label: Optional[str]
    impact_label: Optional[str]
    created_at: datetime

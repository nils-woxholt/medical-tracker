"""Legacy log models for integration test compatibility.

Provides lightweight SQLModel mappings for the original ``medication_logs`` and
``symptom_logs`` tables used by existing integration tests (feel vs yesterday
and migrations). These coexist with newer domain models without table name
conflicts:

* ``MedicationLog`` -> ``medication_logs`` (legacy) – no newer duplicate.
* ``SymptomLog`` -> ``symptom_logs`` (legacy) – newer ``SymptomLog`` feature
  model uses implicit table name ``symptomlog`` so it does not clash.

Do NOT extend these models for new functionality; they will be replaced by a
unified logging design. They are intentionally minimal.
"""

from enum import Enum
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, Text, Integer, String


class SeverityLevel(str, Enum):  # Backwards-compatible enum values
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class MedicationLog(SQLModel, table=True):  # type: ignore[call-arg]
    __tablename__ = "medication_logs"  # type: ignore[assignment]
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field()
    medication_name: str = Field(max_length=200)
    dosage: str = Field(max_length=100)
    taken_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    logged_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    notes: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    side_effects: Optional[str] = Field(default=None, max_length=500)
    side_effect_severity: Optional[SeverityLevel] = Field(default=None)
    effectiveness_rating: Optional[int] = Field(
        default=None,
        description="1–5 subjective effectiveness rating",
        ge=1,
        le=5,
    )


class SymptomLog(SQLModel, table=True):  # type: ignore[call-arg]
    __tablename__ = "symptom_logs"  # type: ignore[assignment]
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field()
    symptom_name: Optional[str] = Field(default=None, max_length=200)
    symptom_type: Optional[str] = Field(default=None, max_length=200)
    severity: int = Field(description="Legacy severity numeric (1–10 approx scale)")
    started_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    ended_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    logged_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    duration_minutes: Optional[int] = Field(default=None)
    duration: Optional[str] = Field(default=None)
    triggers: Optional[str] = Field(default=None, max_length=500)
    location: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None)
    impact_rating: Optional[int] = Field(default=None, description="Legacy impact rating scale")


# Convenience/compatibility helper index metadata (documentation only)
class LogIndexes:
    MEDICATION_USER_DATE = ("user_id", "taken_at")
    MEDICATION_USER_LOG_DATE = ("user_id", "logged_at")
    SYMPTOM_USER_DATE = ("user_id", "started_at")
    SYMPTOM_USER_LOG_DATE = ("user_id", "logged_at")
    SYMPTOM_SEVERITY = ("severity",)


def _severity_enum_to_numeric(level: Optional[SeverityLevel]) -> Optional[int]:
    mapping = {
        SeverityLevel.NONE: 0,
        SeverityLevel.MILD: 2,
        SeverityLevel.MODERATE: 5,
        SeverityLevel.SEVERE: 7,
        SeverityLevel.CRITICAL: 9,
    }
    return mapping.get(level) if level else None


__all__ = [
    "MedicationLog",
    "SymptomLog",
    "SeverityLevel",
    "LogIndexes",
]
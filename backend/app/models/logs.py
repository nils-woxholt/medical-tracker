"""
Log Models - MedicationLog and SymptomLog entities

This module defines the SQLModel entities for medication and symptom logging
in the SaaS Medical Tracker application.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, Text
from sqlmodel import Field, SQLModel

from app.models.base import Base, TimestampMixin


class SeverityLevel(str, Enum):
    """Severity levels for symptoms and side effects."""
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class MedicationLog(Base, TimestampMixin, table=True):
    """
    Medication log entry table.
    
    Tracks daily medication intake with dosage, timing, and optional notes.
    Each entry represents a single medication dose taken by a user.
    """
    __tablename__ = "medication_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, description="User ID who logged the medication")
    
    # Medication details
    medication_name: str = Field(max_length=200, description="Name of the medication taken")
    dosage: str = Field(max_length=100, description="Dosage amount and unit (e.g., '500mg', '2 tablets')")
    
    # Timing
    taken_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        description="When the medication was actually taken"
    )
    logged_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        description="When this log entry was created"
    )
    
    # Optional fields
    notes: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Additional notes about the medication intake"
    )
    side_effects: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Any side effects experienced"
    )
    side_effect_severity: Optional[SeverityLevel] = Field(
        default=None,
        description="Severity of side effects if any"
    )
    
    # Effectiveness rating (1-5 scale)
    effectiveness_rating: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="How effective the medication felt (1-5 scale)"
    )

    class Config:
        """Model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class SymptomLog(Base, TimestampMixin, table=True):
    """
    Symptom log entry table.
    
    Tracks daily symptom occurrences with severity, duration, and context.
    Each entry represents a symptom episode experienced by a user.
    """
    __tablename__ = "symptom_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, description="User ID who logged the symptom")
    
    # Symptom details
    symptom_name: str = Field(max_length=200, description="Name or description of the symptom")
    severity: SeverityLevel = Field(description="Severity level of the symptom")
    
    # Timing
    started_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        description="When the symptom started (if known)"
    )
    ended_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
        description="When the symptom ended (if applicable)"
    )
    logged_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True)),
        description="When this log entry was created"
    )
    
    # Duration in minutes (computed or manually entered)
    duration_minutes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Duration of the symptom in minutes"
    )
    
    # Context and additional information
    triggers: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Potential triggers for the symptom"
    )
    location: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Body location where symptom occurred"
    )
    notes: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Additional notes about the symptom"
    )
    
    # Impact on daily activities (1-5 scale, 1=no impact, 5=severe impact)
    impact_rating: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Impact on daily activities (1-5 scale)"
    )

    class Config:
        """Model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


# Index definitions for query optimization
class LogIndexes:
    """
    Database indexes for log tables to optimize queries.
    
    These indexes support common query patterns like:
    - Fetching logs by user and date range
    - Finding recent logs for summaries
    - Aggregating logs for feel-vs-yesterday calculations
    """
    
    # MedicationLog indexes
    MEDICATION_USER_DATE = ("user_id", "taken_at")
    MEDICATION_USER_LOG_DATE = ("user_id", "logged_at")
    
    # SymptomLog indexes
    SYMPTOM_USER_DATE = ("user_id", "started_at")
    SYMPTOM_USER_LOG_DATE = ("user_id", "logged_at")
    SYMPTOM_SEVERITY = ("severity",)


# Helper functions for common queries
def get_recent_medication_logs_query(user_id: str, days: int = 7):
    """
    Helper to build query for recent medication logs.
    
    Args:
        user_id: User ID to filter by
        days: Number of days to look back
        
    Returns:
        Query object for recent medication logs
    """
    from sqlalchemy import and_, func
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    return (
        MedicationLog.user_id == user_id,
        MedicationLog.taken_at >= cutoff_date
    )


def get_recent_symptom_logs_query(user_id: str, days: int = 7):
    """
    Helper to build query for recent symptom logs.
    
    Args:
        user_id: User ID to filter by
        days: Number of days to look back
        
    Returns:
        Query object for recent symptom logs
    """
    from sqlalchemy import and_, func
    from datetime import timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    return (
        SymptomLog.user_id == user_id,
        SymptomLog.started_at >= cutoff_date
    )


# Example usage and testing
if __name__ == "__main__":
    from datetime import datetime, timezone
    
    # Example MedicationLog
    med_log = MedicationLog(
        user_id="user123",
        medication_name="Ibuprofen",
        dosage="200mg",
        taken_at=datetime.now(timezone.utc),
        logged_at=datetime.now(timezone.utc),
        notes="Taken for headache",
        effectiveness_rating=4
    )
    
    # Example SymptomLog
    symptom_log = SymptomLog(
        user_id="user123",
        symptom_name="Headache",
        severity=SeverityLevel.MODERATE,
        started_at=datetime.now(timezone.utc),
        logged_at=datetime.now(timezone.utc),
        duration_minutes=120,
        location="Forehead",
        impact_rating=3
    )
    
    print("✅ Log models created successfully")
    print(f"MedicationLog fields: {list(med_log.__fields__.keys())}")
    print(f"SymptomLog fields: {list(symptom_log.__fields__.keys())}")
    print(f"Severity levels: {list(SeverityLevel)}")
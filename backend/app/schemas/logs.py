"""
Pydantic Schemas for Log Operations

This module defines the request and response schemas for medication and symptom
logging operations in the SaaS Medical Tracker application.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.models.logs import SeverityLevel


# Base schemas for common patterns
class LogBaseSchema(BaseModel):
    """Base schema for log entries with common validation."""
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


# MedicationLog schemas
class MedicationLogCreate(BaseModel):
    """Schema for creating a new medication log entry."""
    
    medication_name: str = Field(
        ..., 
        min_length=1, 
        max_length=200,
        description="Name of the medication taken"
    )
    dosage: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Dosage amount and unit (e.g., '500mg', '2 tablets')"
    )
    taken_at: datetime = Field(
        ..., 
        description="When the medication was actually taken"
    )
    notes: Optional[str] = Field(
        None, 
        max_length=1000,
        description="Additional notes about the medication intake"
    )
    side_effects: Optional[str] = Field(
        None, 
        max_length=500,
        description="Any side effects experienced"
    )
    side_effect_severity: Optional[SeverityLevel] = Field(
        None,
        description="Severity of side effects if any"
    )
    effectiveness_rating: Optional[int] = Field(
        None, 
        ge=1, 
        le=5,
        description="How effective the medication felt (1-5 scale)"
    )

    @validator('taken_at')
    def validate_taken_at(cls, v):
        """Ensure taken_at is not too far in the future."""
        if v > datetime.utcnow():
            from datetime import timedelta
            # Allow up to 1 hour in the future to account for timezone issues
            if v > datetime.utcnow() + timedelta(hours=1):
                raise ValueError('taken_at cannot be more than 1 hour in the future')
        return v

    @validator('side_effects')
    def validate_side_effects_with_severity(cls, v, values):
        """If side effects are provided, severity should also be provided."""
        if v and v.strip():  # If side effects are provided
            if 'side_effect_severity' not in values or not values['side_effect_severity']:
                raise ValueError('side_effect_severity must be provided when side_effects are specified')
        return v


class MedicationLogUpdate(BaseModel):
    """Schema for updating an existing medication log entry."""
    
    medication_name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=200
    )
    dosage: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=100
    )
    taken_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=1000)
    side_effects: Optional[str] = Field(None, max_length=500)
    side_effect_severity: Optional[SeverityLevel] = None
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5)


class MedicationLogResponse(LogBaseSchema):
    """Schema for medication log response."""
    
    id: int
    user_id: str
    medication_name: str
    dosage: str
    taken_at: datetime
    logged_at: datetime
    notes: Optional[str] = None
    side_effects: Optional[str] = None
    side_effect_severity: Optional[SeverityLevel] = None
    effectiveness_rating: Optional[int] = None


# SymptomLog schemas
class SymptomLogCreate(BaseModel):
    """Schema for creating a new symptom log entry."""
    
    symptom_name: str = Field(
        ..., 
        min_length=1, 
        max_length=200,
        description="Name or description of the symptom"
    )
    severity: SeverityLevel = Field(
        ...,
        description="Severity level of the symptom"
    )
    started_at: datetime = Field(
        ..., 
        description="When the symptom started (if known)"
    )
    ended_at: Optional[datetime] = Field(
        None,
        description="When the symptom ended (if applicable)"
    )
    duration_minutes: Optional[int] = Field(
        None, 
        ge=0,
        description="Duration of the symptom in minutes"
    )
    triggers: Optional[str] = Field(
        None, 
        max_length=500,
        description="Potential triggers for the symptom"
    )
    location: Optional[str] = Field(
        None, 
        max_length=100,
        description="Body location where symptom occurred"
    )
    notes: Optional[str] = Field(
        None, 
        max_length=1000,
        description="Additional notes about the symptom"
    )
    impact_rating: Optional[int] = Field(
        None, 
        ge=1, 
        le=5,
        description="Impact on daily activities (1-5 scale)"
    )

    @validator('ended_at')
    def validate_ended_at(cls, v, values):
        """Ensure ended_at is after started_at."""
        if v and 'started_at' in values:
            if v <= values['started_at']:
                raise ValueError('ended_at must be after started_at')
        return v

    @validator('started_at')
    def validate_started_at(cls, v):
        """Ensure started_at is not too far in the future."""
        if v > datetime.utcnow():
            from datetime import timedelta
            # Allow up to 1 hour in the future to account for timezone issues
            if v > datetime.utcnow() + timedelta(hours=1):
                raise ValueError('started_at cannot be more than 1 hour in the future')
        return v


class SymptomLogUpdate(BaseModel):
    """Schema for updating an existing symptom log entry."""
    
    symptom_name: Optional[str] = Field(None, min_length=1, max_length=200)
    severity: Optional[SeverityLevel] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    triggers: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)
    impact_rating: Optional[int] = Field(None, ge=1, le=5)


class SymptomLogResponse(LogBaseSchema):
    """Schema for symptom log response."""
    
    id: int
    user_id: str
    symptom_name: str
    severity: SeverityLevel
    started_at: datetime
    ended_at: Optional[datetime] = None
    logged_at: datetime
    duration_minutes: Optional[int] = None
    triggers: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    impact_rating: Optional[int] = None


# Aggregated response schemas
class LogSummaryResponse(BaseModel):
    """Schema for log summary (recent logs for landing page)."""
    
    recent_medications: List[MedicationLogResponse] = Field(
        default_factory=list,
        description="Recent medication logs (last 5)"
    )
    recent_symptoms: List[SymptomLogResponse] = Field(
        default_factory=list,
        description="Recent symptom logs (last 5)"
    )
    total_medications_today: int = Field(
        default=0,
        description="Total medication logs for today"
    )
    total_symptoms_today: int = Field(
        default=0,
        description="Total symptom logs for today"
    )


# Feel vs Yesterday response schemas
class FeelVsYesterdayResponse(BaseModel):
    """Schema for feel vs yesterday comparison."""
    
    status: str = Field(
        ...,
        description="Overall feeling status: 'better', 'same', 'worse', 'unknown'"
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence score for the status (0.0 to 1.0)"
    )
    summary: str = Field(
        ...,
        description="Human-readable summary of the comparison"
    )
    details: dict = Field(
        default_factory=dict,
        description="Detailed breakdown of the analysis"
    )
    date_compared: str = Field(
        ...,
        description="Date being compared (YYYY-MM-DD format)"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "status": "better",
                "confidence": 0.75,
                "summary": "Feeling better today - fewer symptoms and medications were more effective",
                "details": {
                    "symptom_severity_change": -0.5,
                    "medication_effectiveness_change": 0.3,
                    "symptom_count_change": -1
                },
                "date_compared": "2025-10-15"
            }
        }


# List query parameters
class LogListParams(BaseModel):
    """Schema for log list query parameters."""
    
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of records to return")
    offset: int = Field(default=0, ge=0, description="Number of records to skip")
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Ensure end_date is after start_date."""
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v


# Error response schemas
class ErrorDetail(BaseModel):
    """Schema for error details."""
    
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses."""
    
    message: str = "Validation error"
    details: List[ErrorDetail] = Field(default_factory=list)
    error_code: str = "VALIDATION_ERROR"


# Example usage and testing
if __name__ == "__main__":
    from datetime import datetime, timezone
    
    # Example MedicationLogCreate
    med_create = MedicationLogCreate(
        medication_name="Ibuprofen",
        dosage="200mg",
        taken_at=datetime.now(timezone.utc),
        notes="Taken for headache",
        effectiveness_rating=4
    )
    
    # Example SymptomLogCreate
    symptom_create = SymptomLogCreate(
        symptom_name="Headache",
        severity=SeverityLevel.MODERATE,
        started_at=datetime.now(timezone.utc),
        duration_minutes=120,
        location="Forehead",
        impact_rating=3
    )
    
    print("✅ Log schemas created successfully")
    print(f"MedicationLogCreate fields: {list(med_create.__fields__.keys())}")
    print(f"SymptomLogCreate fields: {list(symptom_create.__fields__.keys())}")
    print("All validations passed")
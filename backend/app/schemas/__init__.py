"""
Pydantic Schemas for API Request/Response Models

This module defines the Pydantic models used for API serialization and validation.
These schemas define the structure of data coming into and going out of our API endpoints.
"""

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.generics import GenericModel

# Generic type for response data
DataT = TypeVar('DataT')


class BaseSchema(BaseModel):
    """
    Base schema class with common configuration.
    
    All Pydantic schemas should inherit from this to ensure
    consistent serialization behavior.
    """

    model_config = ConfigDict(
        # Allow population by field name or alias
        populate_by_name=True,

        # Validate assignment on field updates
        validate_assignment=True,

        # Use enum values in serialization
        use_enum_values=True,

        # Allow arbitrary types
        arbitrary_types_allowed=True,

        # Serialize datetime as ISO format
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class TimestampSchemaMixin(BaseModel):
    """
    Mixin for schemas that include timestamp fields.
    
    Provides created_at and updated_at fields for API responses.
    """

    created_at: Optional[datetime] = Field(
        None,
        description="When the record was created",
        example="2023-12-01T10:00:00Z"
    )

    updated_at: Optional[datetime] = Field(
        None,
        description="When the record was last updated",
        example="2023-12-01T15:30:00Z"
    )


class PaginationParams(BaseSchema):
    """
    Standard pagination parameters for list endpoints.
    
    Used as a query parameter model for paginated endpoints.
    """

    page: int = Field(
        1,
        ge=1,
        description="Page number (1-indexed)",
        example=1
    )

    page_size: int = Field(
        20,
        ge=1,
        le=100,
        description="Number of items per page (max 100)",
        example=20
    )

    search: Optional[str] = Field(
        None,
        max_length=255,
        description="Search query to filter results",
        example="symptom"
    )


class PaginatedResponse(BaseSchema, Generic[DataT]):
    """
    Generic paginated response wrapper.
    
    Wraps any list of items with pagination metadata.
    """

    items: List[DataT] = Field(
        description="List of items for the current page"
    )

    total: int = Field(
        ge=0,
        description="Total number of items across all pages",
        example=100
    )

    page: int = Field(
        ge=1,
        description="Current page number",
        example=1
    )

    page_size: int = Field(
        ge=1,
        description="Number of items per page",
        example=20
    )

    pages: int = Field(
        ge=0,
        description="Total number of pages",
        example=5
    )


class HealthCheckResponse(BaseSchema):
    """Response schema for health check endpoints."""

    status: str = Field(
        description="Service status",
        example="healthy"
    )

    timestamp: datetime = Field(
        description="Health check timestamp",
        example="2023-12-01T10:00:00Z"
    )

    version: str = Field(
        description="Application version",
        example="1.0.0"
    )

    database: bool = Field(
        description="Database connectivity status",
        example=True
    )


class ErrorResponse(BaseSchema):
    """Standard error response schema."""

    error: str = Field(
        description="Error type or code",
        example="VALIDATION_ERROR"
    )

    message: str = Field(
        description="Human-readable error message",
        example="The provided email address is invalid"
    )

    details: Optional[Any] = Field(
        None,
        description="Additional error details (validation errors, etc.)",
        example={"field": "email", "issue": "invalid_format"}
    )

    request_id: Optional[str] = Field(
        None,
        description="Request ID for tracing",
        example="req_123456789"
    )


# Authentication Schemas
class TokenRequest(BaseSchema):
    """Request schema for token generation."""

    email: EmailStr = Field(
        description="User email address",
        example="user@example.com"
    )

    password: str = Field(
        min_length=8,
        description="User password",
        example="SecurePassword123!"
    )


class TokenResponse(BaseSchema):
    """Response schema for successful authentication."""

    access_token: str = Field(
        description="JWT access token",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )

    token_type: str = Field(
        "bearer",
        description="Token type",
        example="bearer"
    )

    expires_in: int = Field(
        description="Token expiration time in seconds",
        example=3600
    )


class UserBase(BaseSchema):
    """Base user schema with common fields."""

    email: EmailStr = Field(
        description="User email address",
        example="user@example.com"
    )

    full_name: Optional[str] = Field(
        None,
        max_length=255,
        description="User's full name",
        example="John Doe"
    )

    is_active: bool = Field(
        True,
        description="Whether the user account is active",
        example=True
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(
        min_length=8,
        max_length=255,
        description="User password (will be hashed)",
        example="SecurePassword123!"
    )

    confirm_password: str = Field(
        min_length=8,
        max_length=255,
        description="Password confirmation (must match password)",
        example="SecurePassword123!"
    )


class UserUpdate(BaseSchema):
    """Schema for updating user information."""

    full_name: Optional[str] = Field(
        None,
        max_length=255,
        description="User's full name",
        example="John Doe"
    )

    email: Optional[EmailStr] = Field(
        None,
        description="User email address",
        example="newemail@example.com"
    )


class UserResponse(UserBase, TimestampSchemaMixin):
    """Schema for user API responses."""

    id: UUID = Field(
        description="User unique identifier",
        example="123e4567-e89b-12d3-a456-426614174000"
    )


class UserPasswordChange(BaseSchema):
    """Schema for password change requests."""

    current_password: str = Field(
        min_length=1,
        description="Current password for verification",
        example="OldPassword123!"
    )

    new_password: str = Field(
        min_length=8,
        max_length=255,
        description="New password",
        example="NewSecurePassword123!"
    )

    confirm_new_password: str = Field(
        min_length=8,
        max_length=255,
        description="New password confirmation",
        example="NewSecurePassword123!"
    )


# Medication Schemas
class MedicationBase(BaseSchema):
    """Base medication schema."""

    name: str = Field(
        min_length=1,
        max_length=255,
        description="Medication name",
        example="Ibuprofen"
    )

    dosage: Optional[str] = Field(
        None,
        max_length=100,
        description="Medication dosage",
        example="200mg"
    )

    frequency: Optional[str] = Field(
        None,
        max_length=100,
        description="How often to take the medication",
        example="Twice daily with meals"
    )

    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes about the medication",
        example="Take with food to reduce stomach irritation"
    )


class MedicationCreate(MedicationBase):
    """Schema for creating a new medication."""
    pass


class MedicationUpdate(BaseSchema):
    """Schema for updating medication information."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Medication name",
        example="Ibuprofen"
    )

    dosage: Optional[str] = Field(
        None,
        max_length=100,
        description="Medication dosage",
        example="200mg"
    )

    frequency: Optional[str] = Field(
        None,
        max_length=100,
        description="How often to take the medication",
        example="Twice daily with meals"
    )

    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes about the medication",
        example="Take with food to reduce stomach irritation"
    )


class MedicationResponse(MedicationBase, TimestampSchemaMixin):
    """Schema for medication API responses."""

    id: UUID = Field(
        description="Medication unique identifier",
        example="123e4567-e89b-12d3-a456-426614174000"
    )

    user_id: UUID = Field(
        description="ID of the user who owns this medication",
        example="123e4567-e89b-12d3-a456-426614174000"
    )


# Symptom Log Schemas
class SymptomLogBase(BaseSchema):
    """Base symptom log schema."""

    symptom: str = Field(
        min_length=1,
        max_length=255,
        description="Symptom name or description",
        example="Headache"
    )

    severity: int = Field(
        ge=1,
        le=10,
        description="Symptom severity on a scale of 1-10",
        example=7
    )

    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes about the symptom",
        example="Started after lunch, located on the left side"
    )

    occurred_at: Optional[datetime] = Field(
        None,
        description="When the symptom occurred (defaults to now)",
        example="2023-12-01T14:30:00Z"
    )


class SymptomLogCreate(SymptomLogBase):
    """Schema for creating a new symptom log entry."""
    pass


class SymptomLogUpdate(BaseSchema):
    """Schema for updating symptom log information."""

    symptom: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Symptom name or description",
        example="Headache"
    )

    severity: Optional[int] = Field(
        None,
        ge=1,
        le=10,
        description="Symptom severity on a scale of 1-10",
        example=7
    )

    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes about the symptom",
        example="Started after lunch, located on the left side"
    )

    occurred_at: Optional[datetime] = Field(
        None,
        description="When the symptom occurred",
        example="2023-12-01T14:30:00Z"
    )


class SymptomLogResponse(SymptomLogBase, TimestampSchemaMixin):
    """Schema for symptom log API responses."""

    id: UUID = Field(
        description="Symptom log unique identifier",
        example="123e4567-e89b-12d3-a456-426614174000"
    )

    user_id: UUID = Field(
        description="ID of the user who logged this symptom",
        example="123e4567-e89b-12d3-a456-426614174000"
    )


# Example usage and validation testing
if __name__ == "__main__":
    # Test pagination parameters
    pagination = PaginationParams(page=2, page_size=50, search="headache")
    print(f"Pagination: {pagination.model_dump_json(indent=2)}")

    # Test error response
    error = ErrorResponse(
        error="VALIDATION_ERROR",
        message="Invalid email format",
        details={"field": "email", "code": "invalid_format"}
    )
    print(f"Error Response: {error.model_dump_json(indent=2)}")

    # Test user creation
    user_create = UserCreate(
        email="test@example.com",
        full_name="Test User",
        password="TestPassword123!",
        confirm_password="TestPassword123!"
    )
    print(f"User Create: {user_create.model_dump_json(indent=2)}")

    print("✅ Pydantic schemas test completed")

# Import log schemas
from app.schemas.logs import (
    FeelVsYesterdayResponse,
    LogListParams,
    LogSummaryResponse,
    MedicationLogCreate,
    MedicationLogResponse,
    MedicationLogUpdate,
    SymptomLogCreate,
    SymptomLogResponse,
    SymptomLogUpdate,
    ValidationErrorResponse,
)

# Import medical context schemas
from app.schemas.medical_context import (
    ConditionBase,
    ConditionCreate,
    ConditionResponse,
    ConditionUpdate,
    ConditionList,
    DoctorBase,
    DoctorCreate,
    DoctorResponse,
    DoctorUpdate,
    DoctorList,
    DoctorConditionLinkCreate,
    DoctorConditionLinkResponse,
    PassportConditionItem,
    PassportDoctorItem,
    PassportItem,
    PassportResponse,
)

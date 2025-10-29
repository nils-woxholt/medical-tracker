"""
Pydantic schemas for medication endpoints.

Defines request/response validation schemas for medication API endpoints
with proper validation rules and documentation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class MedicationBase(BaseModel):
    """Base medication schema with common fields."""
    
    name: str = Field(
        min_length=2,
        max_length=100,
        description="Medication name (must be unique)",
        example="Aspirin"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional medication description",
        example="Pain reliever and anti-inflammatory medication"
    )
    is_active: bool = Field(
        True,
        description="Whether the medication is active and available for logging",
        example=True
    )

    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate medication name is properly formatted."""
        if not v or not v.strip():
            raise ValueError('Medication name cannot be empty')
        
        # Remove extra whitespace
        v = v.strip()
        
        # Check for reasonable characters
        if not all(c.isalnum() or c.isspace() or c in '-_()/' for c in v):
            raise ValueError('Medication name contains invalid characters')
            
        return v

    @field_validator('description')
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate medication description if provided."""
        if v is not None:
            v = v.strip()
            if not v:  # Empty after strip
                return None
        return v


class MedicationCreate(MedicationBase):
    """Schema for creating a new medication."""
    
    # Inherit all fields from base with is_active defaulting to True
    is_active: bool = Field(
        True,
        description="Whether the medication is active (defaults to True for new medications)"
    )


class MedicationUpdate(BaseModel):
    """Schema for updating an existing medication."""
    
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Updated medication name"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Updated medication description"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Updated active status"
    )

    @field_validator('name')
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate medication name if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Medication name cannot be empty')
            v = v.strip()
            if not all(c.isalnum() or c.isspace() or c in '-_()/' for c in v):
                raise ValueError('Medication name contains invalid characters')
        return v

    @field_validator('description')
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate medication description if provided."""
        if v is not None:
            v = v.strip()
            if not v:  # Empty after strip
                return None
        return v


class MedicationResponse(MedicationBase):
    """Schema for medication response with all fields."""
    
    id: int = Field(description="Unique medication identifier", example=1)
    created_at: datetime = Field(
        description="When the medication was created",
        example="2023-01-01T10:00:00Z"
    )
    updated_at: datetime = Field(
        description="When the medication was last updated",  
        example="2023-01-01T10:00:00Z"
    )

    class Config:
        from_attributes = True  # For SQLModel compatibility


class MedicationPublic(BaseModel):
    """Public medication schema (excludes audit fields)."""
    
    id: int = Field(description="Unique medication identifier", example=1)
    name: str = Field(description="Medication name", example="Aspirin")
    description: Optional[str] = Field(
        description="Medication description",
        example="Pain reliever and anti-inflammatory medication"
    )
    is_active: bool = Field(description="Whether medication is active", example=True)

    class Config:
        from_attributes = True


class MedicationListResponse(BaseModel):
    """Response schema for paginated medication list."""
    
    items: List[MedicationResponse] = Field(
        description="List of medications",
        example=[]
    )
    total: int = Field(
        description="Total number of medications matching filters",
        example=10
    )
    page: int = Field(
        description="Current page number",
        example=1
    )
    per_page: int = Field(
        description="Number of items per page",
        example=10
    )
    pages: int = Field(
        description="Total number of pages",
        example=1
    )


class MedicationSearchParams(BaseModel):
    """Schema for medication search parameters."""
    
    search: Optional[str] = Field(
        None,
        max_length=100,
        description="Search term for medication name or description",
        example="aspirin"
    )
    active_only: bool = Field(
        True,
        description="Filter to only active medications",
        example=True
    )
    page: int = Field(
        1,
        ge=1,
        description="Page number for pagination",
        example=1
    )
    per_page: int = Field(
        10,
        ge=1,
        le=100,
        description="Number of items per page (1-100)",
        example=10
    )

    @field_validator('search')
    def validate_search(cls, v: Optional[str]) -> Optional[str]:
        """Validate search term."""
        if v is not None:
            v = v.strip()
            if not v:  # Empty after strip
                return None
        return v


class MedicationDeactivateResponse(BaseModel):
    """Response schema for medication deactivation."""
    
    id: int = Field(description="Medication ID that was deactivated")
    message: str = Field(description="Confirmation message")
    deactivated_at: datetime = Field(description="When the medication was deactivated")
    # Include current active status (expected by contract tests)
    is_active: bool = Field(
        description="Active status after deactivation (will be False)",
        example=False
    )

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    
    detail: str = Field(description="Error description")
    error_code: Optional[str] = Field(None, description="Optional error code")


class ValidationErrorResponse(BaseModel):
    """Validation error response schema."""
    
    detail: List[dict] = Field(description="List of validation errors")
    
    class Config:
        schema_extra = {
            "example": {
                "detail": [
                    {
                        "loc": ["body", "name"],
                        "msg": "ensure this value has at least 2 characters",
                        "type": "value_error.any_str.min_length",
                        "ctx": {"limit_value": 2}
                    }
                ]
            }
        }
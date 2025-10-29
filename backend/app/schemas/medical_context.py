"""Pydantic schemas for medical context endpoints (conditions and doctors).

Defines request/response validation schemas for condition and doctor API endpoints
with proper validation rules, documentation, and passport aggregation schemas.
"""

from datetime import datetime
from typing import Optional, List, Annotated
from pydantic import BaseModel, Field, field_validator, StringConstraints
from uuid import UUID


class ConditionBase(BaseModel):
    """Base condition schema with common fields."""

    name: Annotated[str, StringConstraints(min_length=2, max_length=100)] = Field(
        description="Condition name",
        examples=["Hypertension"],
    )
    description: Annotated[Optional[str], StringConstraints(max_length=500)] = Field(
        default=None,
        description="Optional condition description",
        examples=["High blood pressure requiring regular monitoring"],
    )
    is_active: bool = Field(
        default=True,
        description="Whether the condition is active and being tracked",
        examples=[True],
    )

    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate condition name is properly formatted."""
        if not v or not v.strip():
            raise ValueError('Condition name cannot be empty')
        
        # Remove extra whitespace
        v = v.strip()
        
        # Check for reasonable characters (allow medical terminology)
        if not all(c.isalnum() or c.isspace() or c in '-_()/.,' for c in v):
            raise ValueError('Condition name contains invalid characters')
            
        return v

    @field_validator('description')
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description if provided."""
        if v is not None:
            v = v.strip()
            if not v:  # Empty string after stripping
                return None
        return v


class ConditionCreate(ConditionBase):
    """Schema for creating a new condition."""
    pass


class ConditionUpdate(BaseModel):
    """Schema for updating an existing condition."""

    name: Annotated[Optional[str], StringConstraints(min_length=2, max_length=100)] = Field(
        default=None,
        description="Updated condition name",
        examples=["Hypertension"],
    )
    description: Annotated[Optional[str], StringConstraints(max_length=500)] = Field(
        default=None,
        description="Updated condition description",
        examples=["High blood pressure requiring regular monitoring"],
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Whether the condition is active and being tracked",
        examples=[True],
    )

    @field_validator('name')
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate condition name if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Condition name cannot be empty')
            
            v = v.strip()
            if not all(c.isalnum() or c.isspace() or c in '-_()/.,' for c in v):
                raise ValueError('Condition name contains invalid characters')
                
        return v

    @field_validator('description')
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description if provided."""
        if v is not None:
            v = v.strip()
            if not v:  # Empty string after stripping
                return None
        return v


class ConditionResponse(ConditionBase):
    """Schema for condition API responses."""

    id: str = Field(
        description="Unique condition identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    user_id: str = Field(
        description="ID of the user who owns this condition",
        examples=["user-uuid-123"],
    )
    created_at: datetime = Field(
        description="Timestamp when condition was created",
        examples=["2024-01-15T10:30:00Z"],
    )
    updated_at: datetime = Field(
        description="Timestamp when condition was last updated",
        examples=["2024-01-15T10:30:00Z"],
    )

    class Config:
        from_attributes = True


class DoctorBase(BaseModel):
    """Base doctor schema with common fields."""

    name: Annotated[str, StringConstraints(min_length=2, max_length=100)] = Field(
        description="Doctor's full name",
        examples=["Dr. Sarah Johnson"],
    )
    specialty: Annotated[str, StringConstraints(min_length=2, max_length=100)] = Field(
        description="Doctor's medical specialty",
        examples=["Cardiology"],
    )
    contact_info: Annotated[Optional[str], StringConstraints(max_length=200)] = Field(
        default=None,
        description="Doctor's contact information (email, phone, etc.)",
        examples=["sarah.johnson@heartcenter.com"],
    )
    is_active: bool = Field(
        default=True,
        description="Whether the doctor is active in practice",
        examples=[True],
    )

    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        """Validate doctor name is properly formatted."""
        if not v or not v.strip():
            raise ValueError('Doctor name cannot be empty')
        
        # Remove extra whitespace
        v = v.strip()
        
        # Check for reasonable characters (allow titles like Dr.)
        if not all(c.isalnum() or c.isspace() or c in '-_.(),' for c in v):
            raise ValueError('Doctor name contains invalid characters')
            
        return v

    @field_validator('specialty')
    def validate_specialty(cls, v: str) -> str:
        """Validate specialty is properly formatted."""
        if not v or not v.strip():
            raise ValueError('Specialty cannot be empty')
        
        # Remove extra whitespace
        v = v.strip()
        
        # Check for reasonable characters
        if not all(c.isalnum() or c.isspace() or c in '-_&()/' for c in v):
            raise ValueError('Specialty contains invalid characters')
            
        return v

    @field_validator('contact_info')
    def validate_contact_info(cls, v: Optional[str]) -> Optional[str]:
        """Validate contact info if provided."""
        if v is not None:
            v = v.strip()
            if not v:  # Empty string after stripping
                return None
        return v


class DoctorCreate(DoctorBase):
    """Schema for creating a new doctor."""
    pass


class DoctorUpdate(BaseModel):
    """Schema for updating an existing doctor."""

    name: Annotated[Optional[str], StringConstraints(min_length=2, max_length=100)] = Field(
        default=None,
        description="Updated doctor name",
        examples=["Dr. Sarah Johnson"],
    )
    specialty: Annotated[Optional[str], StringConstraints(min_length=2, max_length=100)] = Field(
        default=None,
        description="Updated specialty",
        examples=["Cardiology"],
    )
    contact_info: Annotated[Optional[str], StringConstraints(max_length=200)] = Field(
        default=None,
        description="Updated contact information",
        examples=["sarah.johnson@heartcenter.com"],
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Whether the doctor is active in practice",
        examples=[True],
    )

    @field_validator('name')
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate doctor name if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Doctor name cannot be empty')
            
            v = v.strip()
            if not all(c.isalnum() or c.isspace() or c in '-_.(),' for c in v):
                raise ValueError('Doctor name contains invalid characters')
                
        return v

    @field_validator('specialty')
    def validate_specialty(cls, v: Optional[str]) -> Optional[str]:
        """Validate specialty if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Specialty cannot be empty')
            
            v = v.strip()
            if not all(c.isalnum() or c.isspace() or c in '-_&()/' for c in v):
                raise ValueError('Specialty contains invalid characters')
                
        return v

    @field_validator('contact_info')
    def validate_contact_info(cls, v: Optional[str]) -> Optional[str]:
        """Validate contact info if provided."""
        if v is not None:
            v = v.strip()
            if not v:  # Empty string after stripping
                return None
        return v


class DoctorResponse(DoctorBase):
    """Schema for doctor API responses."""

    id: str = Field(
        description="Unique doctor identifier",
        examples=["550e8400-e29b-41d4-a716-446655440001"],
    )
    user_id: str = Field(
        description="ID of the user who owns this doctor record",
        examples=["user-uuid-123"],
    )
    created_at: datetime = Field(
        description="Timestamp when doctor was created",
        examples=["2024-01-15T10:30:00Z"],
    )
    updated_at: datetime = Field(
        description="Timestamp when doctor was last updated",
        examples=["2024-01-15T10:30:00Z"],
    )

    class Config:
        from_attributes = True


class DoctorConditionLinkCreate(BaseModel):
    """Schema for linking a doctor to a condition."""

    doctor_id: str = Field(
        description="Doctor identifier to link",
        examples=["550e8400-e29b-41d4-a716-446655440001"],
    )
    condition_id: str = Field(
        description="Condition identifier to link",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )

    @field_validator('doctor_id', 'condition_id')
    def validate_ids(cls, v: str) -> str:
        """Validate that IDs are properly formatted."""
        if not v or not v.strip():
            raise ValueError('ID cannot be empty')
        
        v = v.strip()
        
        # Basic UUID format validation (36 characters with hyphens)
        if len(v) != 36 or v.count('-') != 4:
            raise ValueError('ID must be a valid UUID format')
            
        return v


class DoctorConditionLinkResponse(BaseModel):
    """Schema for doctor-condition link responses."""

    doctor_id: str = Field(
        description="Doctor identifier",
        examples=["550e8400-e29b-41d4-a716-446655440001"],
    )
    condition_id: str = Field(
        description="Condition identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    created_at: datetime = Field(
        description="Timestamp when link was created",
        examples=["2024-01-15T10:30:00Z"],
    )

    class Config:
        from_attributes = True


class PassportConditionItem(BaseModel):
    """Schema for a condition item in the passport response."""

    id: str = Field(
        description="Condition identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    name: str = Field(
        description="Condition name",
        examples=["Hypertension"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Condition description",
        examples=["High blood pressure requiring regular monitoring"],
    )
    is_active: bool = Field(
        description="Whether the condition is active",
        examples=[True],
    )
    created_at: datetime = Field(
        description="When the condition was created",
        examples=["2024-01-15T10:30:00Z"],
    )
    updated_at: datetime = Field(
        description="When the condition was last updated",
        examples=["2024-01-15T10:30:00Z"],
    )

    class Config:
        from_attributes = True


class PassportDoctorItem(BaseModel):
    """Schema for a doctor item in the passport response."""

    id: str = Field(
        description="Doctor identifier",
        examples=["550e8400-e29b-41d4-a716-446655440001"],
    )
    name: str = Field(
        description="Doctor name",
        examples=["Dr. Sarah Johnson"],
    )
    specialty: str = Field(
        description="Doctor specialty",
        examples=["Cardiology"],
    )
    contact_info: Optional[str] = Field(
        default=None,
        description="Doctor contact information",
        examples=["sarah.johnson@heartcenter.com"],
    )
    is_active: bool = Field(
        description="Whether the doctor is active",
        examples=[True],
    )

    class Config:
        from_attributes = True


class PassportItem(BaseModel):
    """Schema for a passport item containing condition and linked doctors."""

    condition: PassportConditionItem = Field(
        description="The medical condition",
    )
    doctors: List[PassportDoctorItem] = Field(
        description="List of doctors linked to this condition",
        examples=[[]],
    )

    class Config:
        from_attributes = True


class PassportResponse(BaseModel):
    """Schema for the complete passport response."""

    passport: List[PassportItem] = Field(
        description="List of conditions with their linked doctors",
        examples=[[]],
    )
    total_conditions: int = Field(
        description="Total number of active conditions",
        examples=[2],
    )
    total_doctors: int = Field(
        description="Total number of unique active doctors",
        examples=[3],
    )

    class Config:
        from_attributes = True


# Convenience type aliases for commonly used lists
ConditionList = List[ConditionResponse]
DoctorList = List[DoctorResponse]
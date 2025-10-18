"""
Pydantic schemas for medical context endpoints (conditions and doctors).

Defines request/response validation schemas for condition and doctor API endpoints
with proper validation rules, documentation, and passport aggregation schemas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from uuid import UUID


class ConditionBase(BaseModel):
    """Base condition schema with common fields."""
    
    name: str = Field(
        min_length=2,
        max_length=100,
        description="Condition name",
        example="Hypertension"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional condition description",
        example="High blood pressure requiring regular monitoring"
    )
    is_active: bool = Field(
        True,
        description="Whether the condition is active and being tracked",
        example=True
    )

    @validator('name')
    def validate_name(cls, v):
        """Validate condition name is properly formatted."""
        if not v or not v.strip():
            raise ValueError('Condition name cannot be empty')
        
        # Remove extra whitespace
        v = v.strip()
        
        # Check for reasonable characters (allow medical terminology)
        if not all(c.isalnum() or c.isspace() or c in '-_()/.,' for c in v):
            raise ValueError('Condition name contains invalid characters')
            
        return v

    @validator('description')
    def validate_description(cls, v):
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
    
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Updated condition name",
        example="Hypertension"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Updated condition description",
        example="High blood pressure requiring regular monitoring"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether the condition is active and being tracked",
        example=True
    )

    @validator('name')
    def validate_name(cls, v):
        """Validate condition name if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Condition name cannot be empty')
            
            v = v.strip()
            if not all(c.isalnum() or c.isspace() or c in '-_()/.,' for c in v):
                raise ValueError('Condition name contains invalid characters')
                
        return v

    @validator('description')
    def validate_description(cls, v):
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
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    user_id: str = Field(
        description="ID of the user who owns this condition",
        example="user-uuid-123"
    )
    created_at: datetime = Field(
        description="Timestamp when condition was created",
        example="2024-01-15T10:30:00Z"
    )
    updated_at: datetime = Field(
        description="Timestamp when condition was last updated",
        example="2024-01-15T10:30:00Z"
    )

    class Config:
        from_attributes = True


class DoctorBase(BaseModel):
    """Base doctor schema with common fields."""
    
    name: str = Field(
        min_length=2,
        max_length=100,
        description="Doctor's full name",
        example="Dr. Sarah Johnson"
    )
    specialty: str = Field(
        min_length=2,
        max_length=100,
        description="Doctor's medical specialty",
        example="Cardiology"
    )
    contact_info: Optional[str] = Field(
        None,
        max_length=200,
        description="Doctor's contact information (email, phone, etc.)",
        example="sarah.johnson@heartcenter.com"
    )
    is_active: bool = Field(
        True,
        description="Whether the doctor is active in practice",
        example=True
    )

    @validator('name')
    def validate_name(cls, v):
        """Validate doctor name is properly formatted."""
        if not v or not v.strip():
            raise ValueError('Doctor name cannot be empty')
        
        # Remove extra whitespace
        v = v.strip()
        
        # Check for reasonable characters (allow titles like Dr.)
        if not all(c.isalnum() or c.isspace() or c in '-_.(),' for c in v):
            raise ValueError('Doctor name contains invalid characters')
            
        return v

    @validator('specialty')
    def validate_specialty(cls, v):
        """Validate specialty is properly formatted."""
        if not v or not v.strip():
            raise ValueError('Specialty cannot be empty')
        
        # Remove extra whitespace
        v = v.strip()
        
        # Check for reasonable characters
        if not all(c.isalnum() or c.isspace() or c in '-_&()/' for c in v):
            raise ValueError('Specialty contains invalid characters')
            
        return v

    @validator('contact_info')
    def validate_contact_info(cls, v):
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
    
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Updated doctor name",
        example="Dr. Sarah Johnson"
    )
    specialty: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Updated specialty",
        example="Cardiology"
    )
    contact_info: Optional[str] = Field(
        None,
        max_length=200,
        description="Updated contact information",
        example="sarah.johnson@heartcenter.com"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether the doctor is active in practice",
        example=True
    )

    @validator('name')
    def validate_name(cls, v):
        """Validate doctor name if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Doctor name cannot be empty')
            
            v = v.strip()
            if not all(c.isalnum() or c.isspace() or c in '-_.(),' for c in v):
                raise ValueError('Doctor name contains invalid characters')
                
        return v

    @validator('specialty')
    def validate_specialty(cls, v):
        """Validate specialty if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Specialty cannot be empty')
            
            v = v.strip()
            if not all(c.isalnum() or c.isspace() or c in '-_&()/' for c in v):
                raise ValueError('Specialty contains invalid characters')
                
        return v

    @validator('contact_info')
    def validate_contact_info(cls, v):
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
        example="550e8400-e29b-41d4-a716-446655440001"
    )
    user_id: str = Field(
        description="ID of the user who owns this doctor record",
        example="user-uuid-123"
    )
    created_at: datetime = Field(
        description="Timestamp when doctor was created",
        example="2024-01-15T10:30:00Z"
    )
    updated_at: datetime = Field(
        description="Timestamp when doctor was last updated",
        example="2024-01-15T10:30:00Z"
    )

    class Config:
        from_attributes = True


class DoctorConditionLinkCreate(BaseModel):
    """Schema for linking a doctor to a condition."""
    
    doctor_id: str = Field(
        description="Doctor identifier to link",
        example="550e8400-e29b-41d4-a716-446655440001"
    )
    condition_id: str = Field(
        description="Condition identifier to link",
        example="550e8400-e29b-41d4-a716-446655440000"
    )

    @validator('doctor_id', 'condition_id')
    def validate_ids(cls, v):
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
        example="550e8400-e29b-41d4-a716-446655440001"
    )
    condition_id: str = Field(
        description="Condition identifier",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    created_at: datetime = Field(
        description="Timestamp when link was created",
        example="2024-01-15T10:30:00Z"
    )

    class Config:
        from_attributes = True


class PassportConditionItem(BaseModel):
    """Schema for a condition item in the passport response."""
    
    id: str = Field(
        description="Condition identifier",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    name: str = Field(
        description="Condition name",
        example="Hypertension"
    )
    description: Optional[str] = Field(
        None,
        description="Condition description",
        example="High blood pressure requiring regular monitoring"
    )
    is_active: bool = Field(
        description="Whether the condition is active",
        example=True
    )
    created_at: datetime = Field(
        description="When the condition was created",
        example="2024-01-15T10:30:00Z"
    )
    updated_at: datetime = Field(
        description="When the condition was last updated",
        example="2024-01-15T10:30:00Z"
    )

    class Config:
        from_attributes = True


class PassportDoctorItem(BaseModel):
    """Schema for a doctor item in the passport response."""
    
    id: str = Field(
        description="Doctor identifier",
        example="550e8400-e29b-41d4-a716-446655440001"
    )
    name: str = Field(
        description="Doctor name",
        example="Dr. Sarah Johnson"
    )
    specialty: str = Field(
        description="Doctor specialty",
        example="Cardiology"
    )
    contact_info: Optional[str] = Field(
        None,
        description="Doctor contact information",
        example="sarah.johnson@heartcenter.com"
    )
    is_active: bool = Field(
        description="Whether the doctor is active",
        example=True
    )

    class Config:
        from_attributes = True


class PassportItem(BaseModel):
    """Schema for a passport item containing condition and linked doctors."""
    
    condition: PassportConditionItem = Field(
        description="The medical condition"
    )
    doctors: List[PassportDoctorItem] = Field(
        description="List of doctors linked to this condition",
        example=[]
    )

    class Config:
        from_attributes = True


class PassportResponse(BaseModel):
    """Schema for the complete passport response."""
    
    passport: List[PassportItem] = Field(
        description="List of conditions with their linked doctors",
        example=[]
    )
    total_conditions: int = Field(
        description="Total number of active conditions",
        example=2
    )
    total_doctors: int = Field(
        description="Total number of unique active doctors",
        example=3
    )

    class Config:
        from_attributes = True


# Convenience type aliases for commonly used lists
ConditionList = List[ConditionResponse]
DoctorList = List[DoctorResponse]
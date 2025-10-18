"""
SQLModel for MedicationMaster entity.

Defines the database model for medication master data with proper
fields, relationships, and indexing for efficient queries.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime, Index
from sqlalchemy import String, Boolean, Text, func


class MedicationMasterBase(SQLModel):
    """Base model for medication master data with common fields."""
    
    name: str = Field(
        min_length=2,
        max_length=100,
        description="Medication name",
        schema_extra={"example": "Aspirin"}
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional medication description",
        schema_extra={"example": "Pain reliever and anti-inflammatory"}
    )
    is_active: bool = Field(
        default=True,
        description="Whether the medication is active and available for logging",
        schema_extra={"example": True}
    )


class MedicationMaster(MedicationMasterBase, table=True):
    """
    SQLModel for medication master data table.
    
    This model stores the master list of medications that can be logged.
    Includes soft deletion via is_active field and audit timestamps.
    """
    
    __tablename__ = "medications"
    
    id: Optional[int] = Field(
        default=None, 
        primary_key=True,
        description="Unique medication identifier"
    )
    
    # Override base fields with database-specific configurations
    name: str = Field(
        min_length=2,
        max_length=100,
        sa_column=Column(String(100), nullable=False, unique=True),
        description="Medication name (must be unique)",
        schema_extra={"example": "Aspirin"}
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        sa_column=Column(Text, nullable=True),
        description="Optional medication description",
        schema_extra={"example": "Pain reliever and anti-inflammatory"}
    )
    
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, default=True),
        description="Whether the medication is active and available for logging"
    )
    
    # Audit fields
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, default=func.now()),
        description="Timestamp when medication was created"
    )
    
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=True), 
            nullable=False, 
            default=func.now(),
            onupdate=func.now()
        ),
        description="Timestamp when medication was last updated"
    )
    
    # Database indexes for performance
    __table_args__ = (
        # Index for active medication queries (most common use case)
        Index("ix_medications_active", "is_active"),
        
        # Composite index for active medication searches by name
        Index("ix_medications_active_name", "is_active", "name"),
        
        # Index for name searches (case-insensitive searches)
        Index("ix_medications_name_lower", func.lower("name")),
        
        # Index for created_at for audit and sorting
        Index("ix_medications_created_at", "created_at"),
        
        # Index for updated_at for audit and sorting
        Index("ix_medications_updated_at", "updated_at"),
    )


class MedicationMasterCreate(MedicationMasterBase):
    """Schema for creating new medications."""
    pass


class MedicationMasterUpdate(SQLModel):
    """Schema for updating existing medications."""
    
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Medication name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Medication description"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Whether the medication is active"
    )


class MedicationMasterRead(MedicationMasterBase):
    """Schema for reading medication data with all fields."""
    
    id: int = Field(description="Unique medication identifier")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class MedicationMasterPublic(MedicationMasterBase):
    """Public schema for medication data (excludes audit fields)."""
    
    id: int = Field(description="Unique medication identifier")


# Type aliases for easier imports
MedicationCreate = MedicationMasterCreate
MedicationUpdate = MedicationMasterUpdate  
MedicationRead = MedicationMasterRead
MedicationPublic = MedicationMasterPublic
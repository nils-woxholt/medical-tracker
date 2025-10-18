"""
SQLModel for Condition and Doctor entities with linking relationships.

Defines the database models for medical conditions and doctors with proper
fields, relationships, and indexing for efficient queries. Includes the
many-to-many linking table for doctor-condition relationships.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Column, DateTime, Index, Relationship
from sqlalchemy import String, Boolean, Text, func, ForeignKey, Table

from app.models.base import metadata


class ConditionBase(SQLModel):
    """Base model for medical condition data with common fields."""
    
    name: str = Field(
        min_length=2,
        max_length=100,
        description="Condition name",
        schema_extra={"example": "Hypertension"}
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional condition description",
        schema_extra={"example": "High blood pressure requiring monitoring"}
    )
    is_active: bool = Field(
        default=True,
        description="Whether the condition is active and being tracked",
        schema_extra={"example": True}
    )


class DoctorBase(SQLModel):
    """Base model for doctor data with common fields."""
    
    name: str = Field(
        min_length=2,
        max_length=100,
        description="Doctor's full name",
        schema_extra={"example": "Dr. Sarah Johnson"}
    )
    specialty: str = Field(
        min_length=2,
        max_length=100,
        description="Doctor's medical specialty",
        schema_extra={"example": "Cardiology"}
    )
    contact_info: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Doctor's contact information (email, phone, etc.)",
        schema_extra={"example": "sarah.johnson@heartcenter.com"}
    )
    is_active: bool = Field(
        default=True,
        description="Whether the doctor is active in practice",
        schema_extra={"example": True}
    )


# Link table for many-to-many relationship between doctors and conditions
doctor_condition_link = Table(
    "doctor_condition_links",
    metadata,
    Column("doctor_id", String(36), ForeignKey("doctors.id"), primary_key=True),
    Column("condition_id", String(36), ForeignKey("conditions.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=func.now()),
    # Index for efficient lookups
    Index("ix_doctor_condition_doctor", "doctor_id"),
    Index("ix_doctor_condition_condition", "condition_id"),
)


class Condition(ConditionBase, table=True):
    """
    SQLModel for medical conditions table.
    
    This model stores medical conditions that users are tracking.
    Includes user ownership, soft deletion via is_active field, and audit timestamps.
    """
    
    __tablename__ = "conditions"
    
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        sa_column=Column(String(36), primary_key=True, nullable=False),
        description="Unique condition identifier (UUID)"
    )
    
    user_id: str = Field(
        sa_column=Column(String(36), nullable=False),
        description="ID of the user who owns this condition",
        schema_extra={"example": "user-uuid-123"}
    )
    
    # Override base fields with database-specific configurations
    name: str = Field(
        min_length=2,
        max_length=100,
        sa_column=Column(String(100), nullable=False),
        description="Condition name",
        schema_extra={"example": "Hypertension"}
    )
    
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        sa_column=Column(Text, nullable=True),
        description="Optional condition description",
        schema_extra={"example": "High blood pressure requiring monitoring"}
    )
    
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, default=True),
        description="Whether the condition is active and being tracked"
    )
    
    # Audit fields
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, default=func.now()),
        description="Timestamp when condition was created"
    )
    
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=True), 
            nullable=False, 
            default=func.now(),
            onupdate=func.now()
        ),
        description="Timestamp when condition was last updated"
    )
    
    # Relationships (commented out for now - will be handled at the service layer)
    # doctors: List["Doctor"] = Relationship(
    #     back_populates="conditions",
    #     link_model=doctor_condition_link,
    #     sa_relationship_kwargs={"lazy": "selectin"}
    # )
    
    # Database indexes for performance
    __table_args__ = (
        # Index for user's conditions queries (most common use case)
        Index("ix_conditions_user_id", "user_id"),
        
        # Index for active condition queries
        Index("ix_conditions_active", "is_active"),
        
        # Composite index for user's active conditions
        Index("ix_conditions_user_active", "user_id", "is_active"),
        
        # Composite unique index to prevent duplicate condition names per user
        Index("ix_conditions_user_name_unique", "user_id", "name", unique=True),
        
        # Index for created_at for sorting recent conditions
        Index("ix_conditions_created_at", "created_at"),
    )


class Doctor(DoctorBase, table=True):
    """
    SQLModel for doctors table.
    
    This model stores doctor information that can be linked to conditions.
    Includes user ownership, soft deletion via is_active field, and audit timestamps.
    """
    
    __tablename__ = "doctors"
    
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        sa_column=Column(String(36), primary_key=True, nullable=False),
        description="Unique doctor identifier (UUID)"
    )
    
    user_id: str = Field(
        sa_column=Column(String(36), nullable=False),
        description="ID of the user who owns this doctor record",
        schema_extra={"example": "user-uuid-123"}
    )
    
    # Override base fields with database-specific configurations
    name: str = Field(
        min_length=2,
        max_length=100,
        sa_column=Column(String(100), nullable=False),
        description="Doctor's full name",
        schema_extra={"example": "Dr. Sarah Johnson"}
    )
    
    specialty: str = Field(
        min_length=2,
        max_length=100,
        sa_column=Column(String(100), nullable=False),
        description="Doctor's medical specialty",
        schema_extra={"example": "Cardiology"}
    )
    
    contact_info: Optional[str] = Field(
        default=None,
        max_length=200,
        sa_column=Column(String(200), nullable=True),
        description="Doctor's contact information",
        schema_extra={"example": "sarah.johnson@heartcenter.com"}
    )
    
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, default=True),
        description="Whether the doctor is active in practice"
    )
    
    # Audit fields
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, default=func.now()),
        description="Timestamp when doctor was created"
    )
    
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=True), 
            nullable=False, 
            default=func.now(),
            onupdate=func.now()
        ),
        description="Timestamp when doctor was last updated"
    )
    
    # Relationships (commented out for now - will be handled at the service layer)
    # conditions: List["Condition"] = Relationship(
    #     back_populates="doctors",
    #     link_model=doctor_condition_link,
    #     sa_relationship_kwargs={"lazy": "selectin"}
    # )
    
    # Database indexes for performance
    __table_args__ = (
        # Index for user's doctors queries (most common use case)
        Index("ix_doctors_user_id", "user_id"),
        
        # Index for active doctor queries
        Index("ix_doctors_active", "is_active"),
        
        # Composite index for user's active doctors
        Index("ix_doctors_user_active", "user_id", "is_active"),
        
        # Index for specialty searches
        Index("ix_doctors_specialty", "specialty"),
        
        # Composite index for user's doctors by specialty
        Index("ix_doctors_user_specialty", "user_id", "specialty"),
        
        # Index for created_at for sorting recent doctors
        Index("ix_doctors_created_at", "created_at"),
    )


class DoctorConditionLink(SQLModel, table=True):
    """
    SQLModel for doctor-condition link table.
    
    This model manages the many-to-many relationship between doctors and conditions.
    Includes audit timestamp for when the link was created.
    """
    
    __tablename__ = "doctor_condition_links"
    
    doctor_id: str = Field(
        sa_column=Column(String(36), ForeignKey("doctors.id"), primary_key=True, nullable=False),
        description="Doctor identifier"
    )
    
    condition_id: str = Field(
        sa_column=Column(String(36), ForeignKey("conditions.id"), primary_key=True, nullable=False),
        description="Condition identifier"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, default=func.now()),
        description="Timestamp when link was created"
    )
    
    # Database indexes for performance
    __table_args__ = (
        # Index for finding doctors for a condition
        Index("ix_doctor_condition_condition_id", "condition_id"),
        
        # Index for finding conditions for a doctor  
        Index("ix_doctor_condition_doctor_id", "doctor_id"),
        
        # Index for recent links
        Index("ix_doctor_condition_created_at", "created_at"),
    )
"""
User model for the SaaS Medical Tracker.

This module defines the User model for authentication and user management.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Column
from typing import ClassVar
from sqlalchemy import String, Boolean, DateTime, func


class UserBase(SQLModel):
    """Base user model with common fields."""
    
    email: str = Field(
        min_length=5,
        max_length=255,
        description="User's email address (unique identifier)",
        schema_extra={"example": "user@example.com"}
    )
    
    first_name: str = Field(
        min_length=1,
        max_length=100,
        description="User's first name",
        schema_extra={"example": "John"}
    )
    
    last_name: str = Field(
        min_length=1,
        max_length=100,
        description="User's last name",
        schema_extra={"example": "Doe"}
    )
    
    is_active: bool = Field(
        default=True,
        description="Whether the user account is active",
        schema_extra={"example": True}
    )
    
    is_verified: bool = Field(
        default=False,
        description="Whether the user's email is verified",
        schema_extra={"example": True}
    )


class User(UserBase, table=True):
    """
    SQLModel for users table.
    
    This model stores user account information for authentication and personalization.
    """
    
    __tablename__: ClassVar[str] = "users"
    
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        sa_column=Column(String(36), primary_key=True, nullable=False),
        description="Unique user identifier (UUID)"
    )
    
    password_hash: str = Field(
        sa_column=Column(String(255), nullable=False),
        description="Hashed user password"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, default=func.now()),
        description="Timestamp when user was created"
    )
    
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, default=func.now()),
        description="Timestamp when user was last updated"
    )

    # Authentication lockout tracking fields
    failed_attempts: int = Field(
        default=0,
        description="Consecutive failed login attempts"
    )
    lock_until: Optional[datetime] = Field(
        default=None,
        description="If set and in the future, user is locked out from authentication"
    )


class UserCreate(UserBase):
    """Model for user creation requests."""
    password: str = Field(min_length=8, max_length=255)


class UserRead(UserBase):
    """Model for user read responses."""
    id: str
    created_at: datetime
    updated_at: datetime


class UserUpdate(SQLModel):
    """Model for user update requests."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
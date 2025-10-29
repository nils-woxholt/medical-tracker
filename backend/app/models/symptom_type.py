"""SQLModel for SymptomType entity (Feature 004).

Represents a reusable definition of a symptom with default severity / impact values.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Column, DateTime, Index


class SymptomTypeBase(SQLModel):
    name: str = Field(index=True, min_length=2, max_length=100, description="Unique symptom type name per user")
    description: Optional[str] = Field(default=None, max_length=500)
    category: Optional[str] = Field(default=None, max_length=100)


class SymptomType(SymptomTypeBase, table=True):  # type: ignore[call-arg]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True, description="Owner user id (string UUID)")
    default_severity_numeric: int = Field(ge=1, le=10, description="Default severity numeric scale 1-10")
    default_impact_numeric: int = Field(ge=1, le=10, description="Default impact numeric scale 1-10")
    active: bool = Field(default=True, index=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    __table_args__ = (
        Index("ix_symptom_type_user_name_unique", "user_id", "name", unique=True),
    )

    def touch(self) -> None:
        self.updated_at = datetime.utcnow()


class SymptomTypeCreate(SymptomTypeBase):
    default_severity_numeric: int = Field(ge=1, le=10)
    default_impact_numeric: int = Field(ge=1, le=10)


class SymptomTypeRead(SymptomTypeBase):
    id: int
    default_severity_numeric: int
    default_impact_numeric: int
    active: bool
    created_at: datetime
    updated_at: datetime


class SymptomTypeUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    category: Optional[str] = Field(default=None, max_length=100)
    default_severity_numeric: Optional[int] = Field(default=None, ge=1, le=10)
    default_impact_numeric: Optional[int] = Field(default=None, ge=1, le=10)
    active: Optional[bool] = None

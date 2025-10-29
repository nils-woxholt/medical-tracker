"""AuditEntry model extension for Feature 004 changes on SymptomType.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any, Dict

from sqlmodel import SQLModel, Field, Column, DateTime


class AuditEntry(SQLModel, table=True):  # type: ignore[call-arg]
    __tablename__ = "audit_entry"

    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str = Field(description="symptom_type | medication_master")
    entity_id: int = Field(index=True)
    action: str = Field(description="create | update | deactivate")
    user_id: Optional[int] = Field(default=None, index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=False), nullable=False))
    diff: Optional[Dict[str, Any]] = Field(default=None, description="Changed fields diff JSON structure")

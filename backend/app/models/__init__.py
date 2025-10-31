"""
Models package for SaaS Medical Tracker

This package contains all SQLModel database entities and related utilities.
"""

from app.models.base import Base, TimestampMixin
from app.models.logs import SeverityLevel  # legacy enum only
from app.models.medication import MedicationMaster as MedicationMaster
from app.models.symptom_log import SymptomLog as SymptomLog
from app.models.medical_context import (
    Condition, 
    ConditionBase,
    Doctor, 
    DoctorBase,
    DoctorConditionLink
)
from app.models.user import User, UserBase, UserCreate, UserRead, UserUpdate

__all__ = [
    "Base",
    "TimestampMixin", 
    "MedicationMaster",
    "SymptomLog",
    "SeverityLevel",
    "Condition",
    "ConditionBase", 
    "Doctor",
    "DoctorBase",
    "DoctorConditionLink",
    "User",
    "UserBase",
    "UserCreate", 
    "UserRead",
    "UserUpdate"
]
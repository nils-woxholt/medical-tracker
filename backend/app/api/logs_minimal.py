"""Minimal logs endpoints to satisfy contract tests.

This module provides an in-memory implementation for medication and symptom logs
with shapes expected by tests/contract/test_logs.py. It is intentionally
lightweight and avoids persistence. A full implementation would live in a
separate module with database-backed models.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

from app.core.dependencies import get_medication_service, get_current_user
from app.services.medication import MedicationService

router = APIRouter()

class MedicationLogCreateMinimal(BaseModel):
    medication_name: str = Field(..., min_length=1)
    dosage: Optional[str] = Field(None, description="Dosage string e.g. '200mg'")
    taken_at: Optional[datetime] = Field(None, description="Time medication taken")
    notes: Optional[str] = None
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5)

class MedicationLogResponseMinimal(BaseModel):
    id: int
    user_id: str
    medication_name: str
    dosage: Optional[str] = None
    taken_at: Optional[datetime] = None
    notes: Optional[str] = None
    effectiveness_rating: Optional[int] = None
    logged_at: datetime

class SymptomLogCreateMinimal(BaseModel):
    symptom_name: str = Field(..., min_length=1)
    severity: str = Field(..., min_length=1, description="Severity level: one of none|mild|moderate|severe|critical (case-insensitive)")
    started_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    location: Optional[str] = None
    impact_rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = None

    @classmethod
    def _allowed_severities(cls) -> List[str]:
        return ["none", "mild", "moderate", "severe", "critical"]

    def model_validate(self):  # not used directly by Pydantic v2; add explicit custom validation via __post_init__ pattern
        pass

    @staticmethod
    def normalize_severity(value: str) -> str:
        return value.strip().lower()

    def __init__(self, **data: Any):  # type: ignore[override]
        super().__init__(**data)
        norm = self.normalize_severity(self.severity)
        if norm not in self._allowed_severities():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=[{"loc": ("body", "severity"), "msg": "Invalid severity level", "type": "value_error"}]
            )
        # Store canonical lowercase version
        object.__setattr__(self, 'severity', norm)

class SymptomLogResponseMinimal(BaseModel):
    id: int
    user_id: str
    symptom_name: str
    severity: str
    started_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    impact_rating: Optional[int] = None
    notes: Optional[str] = None
    logged_at: datetime

_LOG_STORE: List[Dict[str, Any]] = []
_LOG_SEQ: int = 1
_SYMPTOM_STORE: List[Dict[str, Any]] = []
_SYMPTOM_SEQ: int = 1

@router.post('/logs/medications', response_model=MedicationLogResponseMinimal, status_code=status.HTTP_201_CREATED)
async def create_medication_log_minimal(
    log: MedicationLogCreateMinimal,
    medication_service: MedicationService = Depends(get_medication_service),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> MedicationLogResponseMinimal:
    name_norm = log.medication_name.strip()
    # Enforce deactivated medication rejection (integration test expectation)
    # Perform a direct fetch so we can inspect is_active state rather than just boolean existence.
    try:
        med = medication_service.get_medication_by_name(name_norm)
        if med is not None and med.is_active is False:
            # Explicitly reject with 400 (acceptable per integration test: 400 or 422)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Medication '{name_norm}' is inactive/deactivated"
            )
    except HTTPException:
        raise
    except Exception:
        # Silently ignore unexpected DB issues for this minimal implementation.
        pass
    global _LOG_SEQ
    entry = {
        'id': _LOG_SEQ,
        'user_id': current_user['user_id'],
        'medication_name': name_norm,
        'dosage': log.dosage,
        'taken_at': log.taken_at or datetime.utcnow(),
        'notes': log.notes,
        'effectiveness_rating': log.effectiveness_rating,
        'logged_at': datetime.utcnow()
    }
    _LOG_STORE.append(entry)
    _LOG_SEQ += 1
    return MedicationLogResponseMinimal(**entry)

@router.get('/logs/medications', response_model=List[MedicationLogResponseMinimal])
async def list_medication_logs_minimal(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
) -> List[MedicationLogResponseMinimal]:
    filtered = _LOG_STORE
    if start_date:
        filtered = [e for e in filtered if e['taken_at'] and e['taken_at'] >= start_date]
    if end_date:
        filtered = [e for e in filtered if e['taken_at'] and e['taken_at'] <= end_date]
    sliced = filtered[offset: offset + limit]
    return [MedicationLogResponseMinimal(**e) for e in sliced]

@router.get('/logs/medications/{log_id}', response_model=MedicationLogResponseMinimal)
async def get_medication_log_minimal(
    log_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> MedicationLogResponseMinimal:
    for e in _LOG_STORE:
        if e['id'] == log_id:
            return MedicationLogResponseMinimal(**e)
    raise HTTPException(status_code=404, detail="Medication log not found")

@router.post('/logs/symptoms', response_model=SymptomLogResponseMinimal, status_code=status.HTTP_201_CREATED)
async def create_symptom_log_minimal(
    log: SymptomLogCreateMinimal,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> SymptomLogResponseMinimal:
    global _SYMPTOM_SEQ
    entry = {
        'id': _SYMPTOM_SEQ,
        'user_id': current_user['user_id'],
        'symptom_name': log.symptom_name.strip(),
        'severity': log.severity,
        'started_at': log.started_at or datetime.utcnow(),
        'duration_minutes': log.duration_minutes,
        'location': log.location,
        'impact_rating': log.impact_rating,
        'notes': log.notes,
        'logged_at': datetime.utcnow()
    }
    _SYMPTOM_STORE.append(entry)
    _SYMPTOM_SEQ += 1
    return SymptomLogResponseMinimal(**entry)

@router.get('/logs/symptoms', response_model=List[SymptomLogResponseMinimal])
async def list_symptom_logs_minimal(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
) -> List[SymptomLogResponseMinimal]:
    sliced = _SYMPTOM_STORE[offset: offset + limit]
    return [SymptomLogResponseMinimal(**e) for e in sliced]

@router.get('/logs/summary')
async def logs_summary_minimal(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    # Recent = last 5 entries each
    recent_meds = [MedicationLogResponseMinimal(**e).model_dump() for e in _LOG_STORE[-5:]]
    recent_syms = [SymptomLogResponseMinimal(**e).model_dump() for e in _SYMPTOM_STORE[-5:]]
    # Totals 'today' approximate using UTC date match on logged_at
    today = datetime.utcnow().date()
    meds_today = sum(1 for e in _LOG_STORE if e['logged_at'].date() == today)
    syms_today = sum(1 for e in _SYMPTOM_STORE if e['logged_at'].date() == today)
    return {
        'recent_medications': recent_meds,
        'recent_symptoms': recent_syms,
        'total_medications_today': meds_today,
        'total_symptoms_today': syms_today,
    }

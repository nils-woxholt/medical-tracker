"""Service layer for SymptomLog operations (Feature 004).

Responsibilities:
  * Create symptom logs ensuring referenced SymptomType is active.
  * Compute / normalize duration and enforce confirmation rule.
  * Derive severity / impact labels from numeric values.
  * Provide close operation to set ended_at and finalize duration.
  * List/query recent logs for user (basic pagination stub).

Lean Mode: structured logging only.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select

from app.models.symptom_log import SymptomLog, SymptomLogCreate
from app.models.symptom_type import SymptomType
from app.models.audit_entry import AuditEntry  # type: ignore[attr-defined]
from app.services.active_guard import ensure_active, GuardInactiveError
from app.services.severity_mapping import severity_label, impact_label
from app.services.duration_validator import normalize_duration, DurationValidationError


class SymptomLogService:
    def __init__(self, session: Session, user_id: str):
        self.session = session
        self.user_id = user_id

    # --- creation ---
    def create(self, data: SymptomLogCreate) -> SymptomLog:
        if data.user_id != self.user_id:
            raise ValueError("user mismatch for symptom log creation")

        # Ensure referenced SymptomType active
        try:
            symptom_type = ensure_active(self.session, SymptomType, data.symptom_type_id)
        except GuardInactiveError as e:
            raise ValueError(str(e))

        # Derive labels
        sev_label = severity_label(data.severity_numeric)
        imp_label = impact_label(data.impact_numeric)

        duration, long_required = normalize_duration(
            provided_duration=data.duration_minutes if hasattr(data, "duration_minutes") else None,
            started_at=data.started_at,
            ended_at=data.ended_at,
            confirmation_flag=data.confirmation_long_duration,
        )
        if long_required and data.confirmation_long_duration is not True:
            # normalize_duration would have raised, but double safety
            raise DurationValidationError("Long duration requires confirmation")

        log = SymptomLog(
            symptom_type_id=data.symptom_type_id,
            user_id=self.user_id,
            started_at=data.started_at,
            ended_at=data.ended_at,
            severity_numeric=data.severity_numeric,
            impact_numeric=data.impact_numeric,
            severity_label=sev_label,
            impact_label=imp_label,
            notes=data.notes,
            confirmation_long_duration=data.confirmation_long_duration,
            duration_minutes=duration,
            created_at=datetime.utcnow(),
        )
        self.session.add(log)
        self.session.flush()
        self._audit("create", log.id, {}, self._snapshot(log))
        return log

    # --- close operation ---
    def close(self, log_id: int, ended_at: Optional[datetime] = None) -> SymptomLog:
        log = self.session.get(SymptomLog, log_id)
        if not log or log.user_id != self.user_id:
            raise ValueError("SymptomLog not found")
        before = self._snapshot(log)
        if log.ended_at:
            return log  # already closed
        log.ended_at = ended_at or datetime.utcnow()
        duration, long_required = normalize_duration(
            provided_duration=log.duration_minutes,
            started_at=log.started_at,
            ended_at=log.ended_at,
            confirmation_flag=log.confirmation_long_duration,
        )
        log.duration_minutes = duration
        # If long_required but no confirmation flag yet, we do not auto-set; caller must re-confirm via update (simpler logic in Lean Mode)
        self._audit("close", log.id, before, self._snapshot(log))
        return log

    # --- queries ---
    def list_recent(self, limit: int = 20) -> List[SymptomLog]:
        stmt = (
            select(SymptomLog)
            .where(SymptomLog.user_id == self.user_id)
            .order_by(SymptomLog.started_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(stmt))

    # --- audit helpers ---
    def _audit(self, action: str, entity_id: int, before: dict, after: dict) -> None:
        entry = AuditEntry(
            entity_type="SymptomLog",
            entity_id=entity_id,
            action=action,
            user_id=self.user_id,
            before_json=str(before),
            after_json=str(after),
            created_at=datetime.utcnow(),
        )
        self.session.add(entry)

    def _snapshot(self, log: SymptomLog) -> dict:
        return {
            "symptom_type_id": log.symptom_type_id,
            "started_at": log.started_at.isoformat(),
            "ended_at": log.ended_at.isoformat() if log.ended_at else None,
            "severity_numeric": log.severity_numeric,
            "impact_numeric": log.impact_numeric,
            "severity_label": log.severity_label,
            "impact_label": log.impact_label,
            "duration_minutes": log.duration_minutes,
            "confirmation_long_duration": log.confirmation_long_duration,
            "notes": log.notes,
        }

__all__ = ["SymptomLogService"]

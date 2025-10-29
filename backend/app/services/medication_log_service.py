"""Service layer for MedicationLog operations (Feature 004).

Responsibilities:
  * Create medication intake logs; ensure referenced medication master is active.
  * Provide listing of recent logs.
  * (Lean) No update semantics beyond creation; future phases may add editing.
"""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlmodel import Session, select

from app.models.logs import MedicationLog
from app.models.medication import MedicationMaster
from app.models.audit_entry import AuditEntry  # type: ignore[attr-defined]
from app.services.active_guard import ensure_active, GuardInactiveError


class MedicationLogService:
    def __init__(self, session: Session, user_id: str):
        self.session = session
        self.user_id = user_id

    def create(self, medication_id: int, medication_name: str, dosage: str, taken_at: datetime, notes: str | None = None, effectiveness_rating: int | None = None) -> MedicationLog:
        # Ensure medication master active
        try:
            ensure_active(self.session, MedicationMaster, medication_id)
        except GuardInactiveError as e:
            raise ValueError(str(e))

        log = MedicationLog(
            user_id=self.user_id,
            medication_name=medication_name,
            dosage=dosage,
            taken_at=taken_at,
            logged_at=datetime.utcnow(),
            notes=notes,
            effectiveness_rating=effectiveness_rating,
        )
        self.session.add(log)
        self.session.flush()
        self._audit("create", log.id, {}, self._snapshot(log))
        return log

    def list_recent(self, limit: int = 20) -> List[MedicationLog]:
        stmt = (
            select(MedicationLog)
            .where(MedicationLog.user_id == self.user_id)
            .order_by(MedicationLog.taken_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(stmt))

    def _audit(self, action: str, entity_id: int, before: dict, after: dict) -> None:
        entry = AuditEntry(
            entity_type="MedicationLog",
            entity_id=entity_id,
            action=action,
            user_id=self.user_id,
            before_json=str(before),
            after_json=str(after),
            created_at=datetime.utcnow(),
        )
        self.session.add(entry)

    def _snapshot(self, log: MedicationLog) -> dict:
        return {
            "medication_name": log.medication_name,
            "dosage": log.dosage,
            "taken_at": log.taken_at.isoformat(),
            "logged_at": log.logged_at.isoformat(),
            "notes": log.notes,
            "effectiveness_rating": log.effectiveness_rating,
        }

__all__ = ["MedicationLogService"]

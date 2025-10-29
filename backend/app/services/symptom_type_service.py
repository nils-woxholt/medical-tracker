"""Service layer for SymptomType CRUD (Feature 004).

Responsibilities:
  * Create symptom type for user.
  * Update fields (with optimistic audit logging of changed columns).
  * Deactivate (soft delete) ensuring logs remain.

Lean Mode: structured logging only; metrics/tracing deferred.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select

from app.models.symptom_type import SymptomType, SymptomTypeCreate, SymptomTypeUpdate
from app.models.audit_entry import AuditEntry  # type: ignore[attr-defined]
from app.services.severity_mapping import severity_label, impact_label


class SymptomTypeService:
    def __init__(self, session: Session, user_id: str):
        self.session = session
        self.user_id = user_id

    # --- CRUD operations ---
    def list_active(self) -> List[SymptomType]:
        return list(
            self.session.exec(
                select(SymptomType).where(SymptomType.user_id == self.user_id, SymptomType.active == True)  # noqa: E712
            )
        )

    def get(self, symptom_type_id: int) -> Optional[SymptomType]:
        return self.session.get(SymptomType, symptom_type_id)

    def create(self, data: SymptomTypeCreate) -> SymptomType:
        entity = SymptomType(
            user_id=self.user_id,
            name=data.name,
            description=data.description,
            category=data.category,
            default_severity_numeric=data.default_severity_numeric,
            default_impact_numeric=data.default_impact_numeric,
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(entity)
        self.session.flush()  # obtain id
        self._audit("create", entity.id, {}, self._snapshot(entity))
        return entity

    def update(self, symptom_type_id: int, data: SymptomTypeUpdate) -> SymptomType:
        entity = self.get(symptom_type_id)
        if not entity or entity.user_id != self.user_id:
            raise ValueError("SymptomType not found")
        before = self._snapshot(entity)
        changed = {}
        for field in ["name", "description", "category", "default_severity_numeric", "default_impact_numeric", "active"]:
            new_val = getattr(data, field, None)
            if new_val is not None and new_val != getattr(entity, field):
                setattr(entity, field, new_val)
                changed[field] = new_val
        entity.updated_at = datetime.utcnow()
        if changed:
            self._audit("update", entity.id, before, self._snapshot(entity))
        return entity

    def deactivate(self, symptom_type_id: int) -> SymptomType:
        entity = self.get(symptom_type_id)
        if not entity or entity.user_id != self.user_id:
            raise ValueError("SymptomType not found")
        if not entity.active:
            return entity
        before = self._snapshot(entity)
        entity.active = False
        entity.updated_at = datetime.utcnow()
        self._audit("deactivate", entity.id, before, self._snapshot(entity))
        return entity

    # --- Audit ---
    def _audit(self, action: str, entity_id: int, before: dict, after: dict) -> None:
        entry = AuditEntry(
            entity_type="SymptomType",
            entity_id=entity_id,
            action=action,
            user_id=self.user_id,
            before_json=str(before),
            after_json=str(after),
            created_at=datetime.utcnow(),
        )
        self.session.add(entry)

    def _snapshot(self, entity: SymptomType) -> dict:
        return {
            "name": entity.name,
            "description": entity.description,
            "category": entity.category,
            "default_severity_numeric": entity.default_severity_numeric,
            "default_impact_numeric": entity.default_impact_numeric,
            "active": entity.active,
        }

__all__ = ["SymptomTypeService"]

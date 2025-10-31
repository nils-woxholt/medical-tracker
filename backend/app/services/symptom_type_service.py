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
from app.services.severity_mapping import severity_label, impact_label  # imported for future label derivations (placeholder)


class SymptomTypeService:
    def __init__(self, session: Session, user_id: str):
        self.session = session
        self.user_id = user_id

    # --- CRUD operations ---
    def list_active(self) -> List[SymptomType]:
        stmt = select(SymptomType).where(
            SymptomType.user_id == self.user_id,
            SymptomType.active == True,  # noqa: E712
        )
        try:  # SQLModel Session convenience
            return list(self.session.exec(stmt))
        except AttributeError:  # plain SQLAlchemy Session
            return list(self.session.execute(stmt).scalars())

    def get(self, symptom_type_id: int) -> Optional[SymptomType]:
        return self.session.get(SymptomType, symptom_type_id)

    def create(self, data: SymptomTypeCreate) -> SymptomType:
        # Explicit uniqueness guard for test environments that create tables without Alembic migration indexes.
        # In production the DB unique index (user_id,name) enforces this constraint.
        stmt = select(SymptomType).where(
            SymptomType.user_id == self.user_id,
            SymptomType.name == data.name,
        )
        try:
            existing = self.session.exec(stmt).first()
        except AttributeError:
            existing = self.session.execute(stmt).scalars().first()
        if existing:
            raise ValueError("duplicate name")
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
        assert entity.id is not None, "SymptomType ID not set after flush"
        self._audit("create", int(entity.id), {}, self._snapshot(entity))
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
            assert entity.id is not None, "SymptomType ID unexpectedly None during update"
            self._audit("update", int(entity.id), before, self._snapshot(entity))
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
        assert entity.id is not None, "SymptomType ID unexpectedly None during deactivate"
        self._audit("deactivate", int(entity.id), before, self._snapshot(entity))
        return entity

    # --- Audit ---
    def _audit(self, action: str, entity_id: int, before: dict, after: dict) -> None:
        # Compute diff of changed keys for compact audit trail
        if action == "create":
            # Include all fields for initial creation diff, even if None
            diff = {k: {"before": before.get(k), "after": after.get(k)} for k in after.keys()}
        else:
            diff = {k: {"before": before.get(k), "after": after.get(k)} for k in after.keys() if before.get(k) != after.get(k)}
        entry = AuditEntry(
            entity_type="symptom_type",
            entity_id=entity_id,
            action=action,
            user_id=None,  # user linkage optional; could map to numeric later
            diff=diff or None,
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

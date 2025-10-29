"""Active foreign key guard utility (Feature 004).

Provides helper functions to ensure referenced master entities are active
before creating dependent log records.

Design:
  * Works with SQLModel session; fetches entity by id and checks `active` / `is_active` flag.
  * Raises GuardInactiveError if inactive or missing (with clear message for API layer mapping to 400/422).
  * Keeps logic lean; Strict Mode may add metrics later.
"""
from __future__ import annotations

from typing import Any, Optional, Type, TypeVar
from sqlmodel import SQLModel, Session, select


class GuardInactiveError(ValueError):
    """Raised when a referenced entity is inactive or does not exist."""


TModel = TypeVar("TModel", bound=SQLModel)


def _extract_active_flag(obj: Any) -> Optional[bool]:
    # Support both `active` and `is_active` naming conventions.
    if hasattr(obj, "active"):
        return getattr(obj, "active")  # type: ignore[attr-defined]
    if hasattr(obj, "is_active"):
        return getattr(obj, "is_active")  # type: ignore[attr-defined]
    return None


def ensure_active(session: Session, model_cls: Type[TModel], entity_id: Any) -> TModel:
    """Fetch entity and confirm it's active.

    Args:
        session: SQLModel session.
        model_cls: Model class (e.g., SymptomType, MedicationMaster).
        entity_id: Primary key value.

    Returns:
        The active entity instance.

    Raises:
        GuardInactiveError: if entity missing or inactive.
    """
    instance = session.exec(select(model_cls).where(model_cls.id == entity_id)).first()
    if instance is None:
        raise GuardInactiveError(f"Referenced {model_cls.__name__} id={entity_id} not found")
    active = _extract_active_flag(instance)
    if active is None:
        # If model doesn't expose active flag treat as always active.
        return instance
    if not active:
        raise GuardInactiveError(f"Referenced {model_cls.__name__} id={entity_id} is inactive")
    return instance


__all__ = ["ensure_active", "GuardInactiveError"]

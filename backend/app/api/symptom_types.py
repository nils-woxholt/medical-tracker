"""Symptom Types API Router (Feature 004 Phase 3 US1).

Provides CRUD + deactivate endpoints for SymptomType.
All endpoints require authenticated user (Bearer token) and operate in user scope.

Endpoints:
  POST   /api/v1/symptom-types            create
  GET    /api/v1/symptom-types            list (active only optional)
  GET    /api/v1/symptom-types/{id}       read
  PUT    /api/v1/symptom-types/{id}       update
  PATCH  /api/v1/symptom-types/{id}/deactivate  deactivate (soft)

Lean Mode: structured logging only; metrics/tracing deferred.
"""
from __future__ import annotations

from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.dependencies import get_sync_db_session, get_current_user_id_or_session
from app.models.symptom_type import (
    SymptomType,
    SymptomTypeCreate,
    SymptomTypeRead,
    SymptomTypeUpdate,
)
from app.services.symptom_type_service import SymptomTypeService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/symptom-types", tags=["Symptom Types"])


def get_service(
    session: Session = Depends(get_sync_db_session),
    user_id: str = Depends(get_current_user_id_or_session),
) -> SymptomTypeService:
    return SymptomTypeService(session=session, user_id=user_id)


@router.post("", response_model=SymptomTypeRead, status_code=status.HTTP_201_CREATED)
def create_symptom_type(
    payload: SymptomTypeCreate,
    service: SymptomTypeService = Depends(get_service),
    session: Session = Depends(get_sync_db_session),
):
    try:
        entity = service.create(payload)
        session.commit()
        session.refresh(entity)
        return SymptomTypeRead.model_validate(entity)
    except IntegrityError as e:  # unique name constraint violation
        session.rollback()
        logger.info("symptom_type.create.conflict", error=str(e), name=payload.name)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Symptom type name already exists")
    except ValueError as e:  # domain errors
        session.rollback()
        msg = str(e)
        if "duplicate" in msg.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Symptom type name already exists")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


@router.get("", response_model=List[SymptomTypeRead])
def list_symptom_types(
    include_inactive: bool = Query(False, description="Include inactive symptom types in results"),
    service: SymptomTypeService = Depends(get_service),
    session: Session = Depends(get_sync_db_session),
):
    """List symptom types for the current user.

    By default returns only active types. When include_inactive=True returns both active and inactive.
    """
    if not include_inactive:
        data = service.list_active()
    else:
        stmt = select(SymptomType).where(SymptomType.user_id == service.user_id)
        try:
            data = list(session.exec(stmt))  # type: ignore[attr-defined]
        except AttributeError:
            data = list(session.execute(stmt).scalars())
    return [SymptomTypeRead.model_validate(d) for d in data]


@router.get("/{id}", response_model=SymptomTypeRead)
def get_symptom_type(
    id: int,
    service: SymptomTypeService = Depends(get_service),
):
    entity = service.get(id)
    if not entity or entity.user_id != service.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symptom type not found")
    return SymptomTypeRead.model_validate(entity)


@router.put("/{id}", response_model=SymptomTypeRead)
def update_symptom_type(
    id: int,
    payload: SymptomTypeUpdate,
    service: SymptomTypeService = Depends(get_service),
    session: Session = Depends(get_sync_db_session),
):
    try:
        entity = service.update(id, payload)
        session.commit()
        session.refresh(entity)
        return SymptomTypeRead.model_validate(entity)
    except IntegrityError as e:
        session.rollback()
        logger.info("symptom_type.update.conflict", error=str(e), id=id)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Symptom type name already exists")
    except ValueError as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{id}/deactivate", response_model=SymptomTypeRead)
def deactivate_symptom_type(
    id: int,
    service: SymptomTypeService = Depends(get_service),
    session: Session = Depends(get_sync_db_session),
):
    try:
        entity = service.deactivate(id)
        session.commit()
        session.refresh(entity)
        return SymptomTypeRead.model_validate(entity)
    except ValueError:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symptom type not found")


__all__ = ["router"]

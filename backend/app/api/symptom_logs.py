"""Symptom Logs API Router (Feature 004 Phase 4 US2).

Provides minimal create and list endpoints for SymptomLog entities.

Endpoints:
  POST /api/v1/symptom-logs        create new log
  GET  /api/v1/symptom-logs        list recent logs (optional filters)

Scope: current authenticated user.
Lean Mode: minimal validation + service layer; advanced pagination deferred.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.core.dependencies import get_sync_db_session, get_current_user_id_or_session
from app.models.symptom_log import SymptomLogRead, SymptomLogCreate, SymptomLog
from app.services.symptom_log_service import SymptomLogService
from app.services.duration_validator import DurationValidationError

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/symptom-logs", tags=["Symptom Logs"])


def get_service(
    session: Session = Depends(get_sync_db_session),
    user_id: str = Depends(get_current_user_id_or_session),
) -> SymptomLogService:
    return SymptomLogService(session=session, user_id=user_id)


@router.post("", response_model=SymptomLogRead, status_code=status.HTTP_201_CREATED)
def create_symptom_log(
    payload: SymptomLogCreate,
    service: SymptomLogService = Depends(get_service),
    session: Session = Depends(get_sync_db_session),
):
    try:
        entity = service.create(payload)
        session.commit()
        session.refresh(entity)
        return SymptomLogRead.model_validate(entity)
    except DurationValidationError as e:
        session.rollback()
        logger.info("symptom_log.create.duration_error", error=str(e))
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ValueError as e:
        session.rollback()
        msg = str(e)
        logger.info("symptom_log.create.value_error", error=msg)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)


@router.get("", response_model=List[SymptomLogRead])
def list_symptom_logs(
    limit: int = Query(20, ge=1, le=200, description="Max number of recent logs"),
    symptom_type_id: Optional[int] = Query(None, description="Filter by symptom type id"),
    started_after: Optional[datetime] = Query(None, description="Filter logs with started_at >= this UTC timestamp"),
    started_before: Optional[datetime] = Query(None, description="Filter logs with started_at <= this UTC timestamp"),
    service: SymptomLogService = Depends(get_service),
    session: Session = Depends(get_sync_db_session),
    user_id: str = Depends(get_current_user_id_or_session),
):
    # Build dynamic query (Lean Mode: simple filters only)
    stmt = select(SymptomLog).where(SymptomLog.user_id == user_id)  # type: ignore[attr-defined]
    if symptom_type_id is not None:
        stmt = stmt.where(SymptomLog.symptom_type_id == symptom_type_id)
    if started_after is not None:
        stmt = stmt.where(SymptomLog.started_at >= started_after)  # type: ignore[attr-defined]
    if started_before is not None:
        stmt = stmt.where(SymptomLog.started_at <= started_before)  # type: ignore[attr-defined]
    stmt = stmt.order_by(SymptomLog.started_at.desc()).limit(limit)  # type: ignore[attr-defined]
    data = list(session.exec(stmt))
    return [SymptomLogRead.model_validate(d) for d in data]


__all__ = ["router"]
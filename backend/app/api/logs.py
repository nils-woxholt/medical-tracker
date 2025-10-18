"""
Logs API Router

This module provides REST API endpoints for medication and symptom logging
in the SaaS Medical Tracker application.
"""

import time
from datetime import datetime, timezone
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.logs import MedicationLog, SymptomLog
from app.schemas.logs import (
    LogListParams,
    LogSummaryResponse,
    MedicationLogCreate,
    MedicationLogResponse,
    MedicationLogUpdate,
    SymptomLogCreate,
    SymptomLogResponse,
    SymptomLogUpdate,
)
from app.telemetry.metrics import (
    record_user_action,
    record_database_query,
    record_error,
    track_user_action,
    track_database_query,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


# Medication Logs endpoints
@router.post(
    "/logs/medications",
    response_model=MedicationLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create medication log",
    description="Create a new medication log entry for the authenticated user"
)
@track_user_action("medication_log_create")
async def create_medication_log(
    medication_data: MedicationLogCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> MedicationLogResponse:
    """Create a new medication log entry."""
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Creating medication log",
        user_id=user_id,
        medication_name=medication_data.medication_name,
        dosage=medication_data.dosage,
        taken_at=medication_data.taken_at,
        has_side_effects=bool(medication_data.side_effects),
        effectiveness_rating=medication_data.effectiveness_rating,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        # Create medication log
        medication_log = MedicationLog(
            user_id=user_id,
            medication_name=medication_data.medication_name,
            dosage=medication_data.dosage,
            taken_at=medication_data.taken_at,
            logged_at=datetime.now(timezone.utc),
            notes=medication_data.notes,
            side_effects=medication_data.side_effects,
            side_effect_severity=medication_data.side_effect_severity,
            effectiveness_rating=medication_data.effectiveness_rating
        )
        
        db_start = time.time()
        db.add(medication_log)
        db.commit()
        db.refresh(medication_log)
        db_duration = time.time() - db_start
        
        # Record database metrics
        record_database_query("medication_log_create", db_duration, "success")
        
        # Record business metrics
        record_user_action("medication_logged", str(user_id))
        
        # Log successful creation with timing
        total_duration = time.time() - start_time
        logger.info(
            "Medication log created successfully",
            user_id=user_id,
            log_id=medication_log.id,
            medication_name=medication_data.medication_name,
            total_duration_ms=round(total_duration * 1000, 2),
            db_duration_ms=round(db_duration * 1000, 2),
            request_id=getattr(request.state, 'request_id', None)
        )
        
        return MedicationLogResponse.model_validate(medication_log)
        
    except Exception as e:
        # Record error metrics
        record_error("medication_log_create_error", "error")
        record_database_query("medication_log_create", time.time() - start_time, "error")
        
        # Log error with context
        logger.error(
            "Failed to create medication log",
            user_id=user_id,
            medication_name=medication_data.medication_name,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=round((time.time() - start_time) * 1000, 2),
            request_id=getattr(request.state, 'request_id', None)
        )
        
        # Re-raise as HTTP exception
        if isinstance(e, HTTPException):
            raise
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create medication log"
            )


@router.get(
    "/logs/medications",
    response_model=List[MedicationLogResponse],
    summary="List medication logs",
    description="Get a list of medication logs for the authenticated user"
)
@track_user_action("medication_log_list")
async def list_medication_logs(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of records"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering")
) -> List[MedicationLogResponse]:
    """List medication logs for the authenticated user."""
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Listing medication logs",
        user_id=user_id,
        limit=limit,
        offset=offset,
        start_date=start_date.isoformat() if start_date else None,
        end_date=end_date.isoformat() if end_date else None,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        # Build query
        query = db.query(MedicationLog).filter(MedicationLog.user_id == user_id)
        
        # Apply date filters
        if start_date:
            query = query.filter(MedicationLog.taken_at >= start_date)
        if end_date:
            query = query.filter(MedicationLog.taken_at <= end_date)
        
        # Execute query with timing
        db_start = time.time()
        logs = query.order_by(desc(MedicationLog.taken_at)).offset(offset).limit(limit).all()
        db_duration = time.time() - db_start
        
        # Record metrics
        record_database_query("medication_log_list", db_duration, "success")
        record_user_action("medication_logs_viewed", str(user_id))
        
        # Log successful query
        total_duration = time.time() - start_time
        logger.info(
            "Medication logs retrieved successfully",
            user_id=user_id,
            count=len(logs),
            limit=limit,
            offset=offset,
            total_duration_ms=round(total_duration * 1000, 2),
            db_duration_ms=round(db_duration * 1000, 2),
            request_id=getattr(request.state, 'request_id', None)
        )
        
        return [MedicationLogResponse.model_validate(log) for log in logs]
        
    except Exception as e:
        # Record error metrics
        record_error("medication_log_list_error", "error")
        record_database_query("medication_log_list", time.time() - start_time, "error")
        
        # Log error
        logger.error(
            "Failed to list medication logs",
            user_id=user_id,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=round((time.time() - start_time) * 1000, 2),
            request_id=getattr(request.state, 'request_id', None)
        )
        
        # Re-raise as HTTP exception
        if isinstance(e, HTTPException):
            raise
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve medication logs"
            )


@router.get(
    "/logs/medications/{log_id}",
    response_model=MedicationLogResponse,
    summary="Get medication log",
    description="Get a specific medication log by ID"
)
async def get_medication_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> MedicationLogResponse:
    """Get a specific medication log by ID."""
    
    log = db.query(MedicationLog).filter(
        and_(
            MedicationLog.id == log_id,
            MedicationLog.user_id == current_user["user_id"]
        )
    ).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication log not found"
        )
    
    return MedicationLogResponse.model_validate(log)


@router.put(
    "/logs/medications/{log_id}",
    response_model=MedicationLogResponse,
    summary="Update medication log",
    description="Update a specific medication log by ID"
)
async def update_medication_log(
    log_id: int,
    update_data: MedicationLogUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> MedicationLogResponse:
    """Update a specific medication log."""
    
    log = db.query(MedicationLog).filter(
        and_(
            MedicationLog.id == log_id,
            MedicationLog.user_id == current_user["user_id"]
        )
    ).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication log not found"
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(log, field, value)
    
    db.commit()
    db.refresh(log)
    
    logger.info(
        "Medication log updated",
        user_id=current_user["user_id"],
        log_id=log_id
    )
    
    return MedicationLogResponse.model_validate(log)


@router.delete(
    "/logs/medications/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete medication log",
    description="Delete a specific medication log by ID"
)
async def delete_medication_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific medication log."""
    
    log = db.query(MedicationLog).filter(
        and_(
            MedicationLog.id == log_id,
            MedicationLog.user_id == current_user["user_id"]
        )
    ).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication log not found"
        )
    
    db.delete(log)
    db.commit()
    
    logger.info(
        "Medication log deleted",
        user_id=current_user["user_id"],
        log_id=log_id
    )


# Symptom Logs endpoints
@router.post(
    "/logs/symptoms",
    response_model=SymptomLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create symptom log",
    description="Create a new symptom log entry for the authenticated user"
)
@track_user_action("symptom_log_create")
async def create_symptom_log(
    symptom_data: SymptomLogCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> SymptomLogResponse:
    """Create a new symptom log entry."""
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Creating symptom log",
        user_id=user_id,
        symptom_name=symptom_data.symptom_name,
        severity=symptom_data.severity,
        started_at=symptom_data.started_at,
        duration_minutes=symptom_data.duration_minutes,
        has_triggers=bool(symptom_data.triggers),
        impact_rating=symptom_data.impact_rating,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        # Create symptom log
        symptom_log = SymptomLog(
            user_id=user_id,
            symptom_name=symptom_data.symptom_name,
            severity=symptom_data.severity,
            started_at=symptom_data.started_at,
            ended_at=symptom_data.ended_at,
            logged_at=datetime.now(timezone.utc),
            duration_minutes=symptom_data.duration_minutes,
            triggers=symptom_data.triggers,
            location=symptom_data.location,
            notes=symptom_data.notes,
            impact_rating=symptom_data.impact_rating
        )
        
        db_start = time.time()
        db.add(symptom_log)
        db.commit()
        db.refresh(symptom_log)
        db_duration = time.time() - db_start
        
        # Record database metrics
        record_database_query("symptom_log_create", db_duration, "success")
        
        # Record business metrics
        record_user_action("symptom_logged", str(user_id))
        
        # Log successful creation with timing
        total_duration = time.time() - start_time
        logger.info(
            "Symptom log created successfully",
            user_id=user_id,
            log_id=symptom_log.id,
            symptom_name=symptom_data.symptom_name,
            severity=symptom_data.severity,
            total_duration_ms=round(total_duration * 1000, 2),
            db_duration_ms=round(db_duration * 1000, 2),
            request_id=getattr(request.state, 'request_id', None)
        )
        
        return SymptomLogResponse.model_validate(symptom_log)
        
    except Exception as e:
        # Record error metrics
        record_error("symptom_log_create_error", "error")
        record_database_query("symptom_log_create", time.time() - start_time, "error")
        
        # Log error with context
        logger.error(
            "Failed to create symptom log",
            user_id=user_id,
            symptom_name=symptom_data.symptom_name,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=round((time.time() - start_time) * 1000, 2),
            request_id=getattr(request.state, 'request_id', None)
        )
        
        # Re-raise as HTTP exception
        if isinstance(e, HTTPException):
            raise
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create symptom log"
            )


@router.get(
    "/logs/symptoms",
    response_model=List[SymptomLogResponse],
    summary="List symptom logs",
    description="Get a list of symptom logs for the authenticated user"
)
async def list_symptom_logs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of records"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering")
) -> List[SymptomLogResponse]:
    """List symptom logs for the authenticated user."""
    
    logger.info(
        "Listing symptom logs",
        user_id=current_user["user_id"],
        limit=limit,
        offset=offset
    )
    
    # Build query
    query = db.query(SymptomLog).filter(SymptomLog.user_id == current_user["user_id"])
    
    # Apply date filters
    if start_date:
        query = query.filter(SymptomLog.started_at >= start_date)
    if end_date:
        query = query.filter(SymptomLog.started_at <= end_date)
    
    # Apply pagination and ordering
    logs = query.order_by(desc(SymptomLog.started_at)).offset(offset).limit(limit).all()
    
    return [SymptomLogResponse.model_validate(log) for log in logs]


@router.get(
    "/logs/symptoms/{log_id}",
    response_model=SymptomLogResponse,
    summary="Get symptom log",
    description="Get a specific symptom log by ID"
)
async def get_symptom_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> SymptomLogResponse:
    """Get a specific symptom log by ID."""
    
    log = db.query(SymptomLog).filter(
        and_(
            SymptomLog.id == log_id,
            SymptomLog.user_id == current_user["user_id"]
        )
    ).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symptom log not found"
        )
    
    return SymptomLogResponse.model_validate(log)


@router.put(
    "/logs/symptoms/{log_id}",
    response_model=SymptomLogResponse,
    summary="Update symptom log",
    description="Update a specific symptom log by ID"
)
async def update_symptom_log(
    log_id: int,
    update_data: SymptomLogUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> SymptomLogResponse:
    """Update a specific symptom log."""
    
    log = db.query(SymptomLog).filter(
        and_(
            SymptomLog.id == log_id,
            SymptomLog.user_id == current_user["user_id"]
        )
    ).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symptom log not found"
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(log, field, value)
    
    db.commit()
    db.refresh(log)
    
    logger.info(
        "Symptom log updated",
        user_id=current_user["user_id"],
        log_id=log_id
    )
    
    return SymptomLogResponse.model_validate(log)


@router.delete(
    "/logs/symptoms/{log_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete symptom log",
    description="Delete a specific symptom log by ID"
)
async def delete_symptom_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a specific symptom log."""
    
    log = db.query(SymptomLog).filter(
        and_(
            SymptomLog.id == log_id,
            SymptomLog.user_id == current_user["user_id"]
        )
    ).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symptom log not found"
        )
    
    db.delete(log)
    db.commit()
    
    logger.info(
        "Symptom log deleted",
        user_id=current_user["user_id"],
        log_id=log_id
    )


# Summary endpoint for landing page
@router.get(
    "/logs/summary",
    response_model=LogSummaryResponse,
    summary="Get logs summary",
    description="Get a summary of recent logs for the landing page"
)
async def get_logs_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> LogSummaryResponse:
    """Get a summary of recent logs for the landing page."""
    
    from datetime import timedelta
    
    user_id = current_user["user_id"]
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    logger.info("Getting logs summary", user_id=user_id)
    
    # Get recent medication logs (last 5)
    recent_medications = (
        db.query(MedicationLog)
        .filter(MedicationLog.user_id == user_id)
        .order_by(desc(MedicationLog.taken_at))
        .limit(5)
        .all()
    )
    
    # Get recent symptom logs (last 5)
    recent_symptoms = (
        db.query(SymptomLog)
        .filter(SymptomLog.user_id == user_id)
        .order_by(desc(SymptomLog.started_at))
        .limit(5)
        .all()
    )
    
    # Count today's logs
    total_medications_today = (
        db.query(MedicationLog)
        .filter(
            and_(
                MedicationLog.user_id == user_id,
                MedicationLog.taken_at >= today_start
            )
        )
        .count()
    )
    
    total_symptoms_today = (
        db.query(SymptomLog)
        .filter(
            and_(
                SymptomLog.user_id == user_id,
                SymptomLog.started_at >= today_start
            )
        )
        .count()
    )
    
    return LogSummaryResponse(
        recent_medications=[MedicationLogResponse.model_validate(log) for log in recent_medications],
        recent_symptoms=[SymptomLogResponse.model_validate(log) for log in recent_symptoms],
        total_medications_today=total_medications_today,
        total_symptoms_today=total_symptoms_today
    )


# Example usage and testing
if __name__ == "__main__":
    print("✅ Logs API router created successfully")
    print("Available endpoints:")
    print("- POST /logs/medications - Create medication log")
    print("- GET /logs/medications - List medication logs")
    print("- GET /logs/medications/{id} - Get medication log")
    print("- PUT /logs/medications/{id} - Update medication log")
    print("- DELETE /logs/medications/{id} - Delete medication log")
    print("- POST /logs/symptoms - Create symptom log")
    print("- GET /logs/symptoms - List symptom logs")
    print("- GET /logs/symptoms/{id} - Get symptom log")
    print("- PUT /logs/symptoms/{id} - Update symptom log")
    print("- DELETE /logs/symptoms/{id} - Delete symptom log")
    print("- GET /logs/summary - Get logs summary for landing page")
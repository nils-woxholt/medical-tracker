"""
Medical Context API Router

This module provides REST API endpoints for condition and doctor management
as well as passport functionality in the SaaS Medical Tracker application.
"""

import time
from datetime import datetime, timezone
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.services.medical_context_service import MedicalContextService
from app.schemas.medical_context import (
    ConditionCreate,
    ConditionResponse,
    ConditionUpdate,
    DoctorCreate,
    DoctorResponse,
    DoctorUpdate,
    DoctorConditionLinkCreate,
    DoctorConditionLinkResponse,
    PassportResponse,
    PassportItem,
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


def get_medical_context_service(db: Session = Depends(get_db)) -> MedicalContextService:
    """Dependency to get medical context service instance."""
    return MedicalContextService(db)


# Condition endpoints
@router.post(
    "/conditions",
    response_model=ConditionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create condition",
    description="Create a new medical condition for the authenticated user",
    tags=["conditions"]
)
@track_user_action("condition_create")
async def create_condition(
    condition_data: ConditionCreate,
    request: Request,
    service: MedicalContextService = Depends(get_medical_context_service),
    current_user: dict = Depends(get_current_user)
) -> ConditionResponse:
    """Create a new medical condition."""
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Creating condition",
        user_id=user_id,
        condition_name=condition_data.name,
        is_active=condition_data.is_active,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        condition = service.create_condition(condition_data, user_id)
        
        # Record metrics
        record_user_action("condition_created", user_id)
        record_database_query("condition", "create", time.time() - start_time)
        
        logger.info(
            "Condition created successfully",
            user_id=user_id,
            condition_id=condition.id,
            condition_name=condition.name,
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        
        return condition
        
    except HTTPException:
        # Re-raise HTTP exceptions (e.g., validation errors)
        raise
    except Exception as e:
        # Record error and return 500
        record_error("condition_creation_error", str(e))
        logger.error(
            "Failed to create condition",
            user_id=user_id,
            condition_name=condition_data.name,
            error=str(e),
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create condition"
        )


@router.get(
    "/conditions",
    response_model=List[ConditionResponse],
    summary="List conditions",
    description="Get all conditions for the authenticated user",
    tags=["conditions"]
)
@track_user_action("condition_list")
async def list_conditions(
    request: Request,
    active_only: bool = Query(False, description="Only return active conditions"),
    service: MedicalContextService = Depends(get_medical_context_service),
    current_user: dict = Depends(get_current_user)
) -> List[ConditionResponse]:
    """Get all conditions for the authenticated user."""
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Listing conditions",
        user_id=user_id,
        active_only=active_only,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        conditions = service.get_user_conditions(user_id, active_only=active_only)
        
        # Record metrics
        record_user_action("conditions_listed", user_id)
        record_database_query("condition", "list", time.time() - start_time)
        
        logger.info(
            "Conditions retrieved successfully",
            user_id=user_id,
            count=len(conditions),
            active_only=active_only,
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        
        return conditions
        
    except Exception as e:
        # Record error and return 500
        record_error("condition_list_error", str(e))
        logger.error(
            "Failed to list conditions",
            user_id=user_id,
            error=str(e),
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conditions"
        )


@router.get(
    "/conditions/{condition_id}",
    response_model=ConditionResponse,
    summary="Get condition",
    description="Get a specific condition by ID",
    tags=["conditions"]
)
@track_user_action("condition_get")
async def get_condition(
    condition_id: str,
    request: Request,
    service: MedicalContextService = Depends(get_medical_context_service),
    current_user: dict = Depends(get_current_user)
) -> ConditionResponse:
    """Get a specific condition by ID."""
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Getting condition",
        user_id=user_id,
        condition_id=condition_id,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        condition = service.get_condition_by_id(condition_id, user_id)
        
        if not condition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Condition with ID '{condition_id}' not found"
            )
        
        # Record metrics
        record_user_action("condition_retrieved", user_id)
        record_database_query("condition", "get", time.time() - start_time)
        
        logger.info(
            "Condition retrieved successfully",
            user_id=user_id,
            condition_id=condition_id,
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        
        return condition
        
    except HTTPException:
        # Re-raise HTTP exceptions (e.g., 404)
        raise
    except Exception as e:
        # Record error and return 500
        record_error("condition_get_error", str(e))
        logger.error(
            "Failed to get condition",
            user_id=user_id,
            condition_id=condition_id,
            error=str(e),
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve condition"
        )


@router.patch(
    "/conditions/{condition_id}",
    response_model=ConditionResponse,
    summary="Update condition",
    description="Update a specific condition",
    tags=["conditions"]
)
@track_user_action("condition_update")
async def update_condition(
    condition_id: str,
    update_data: ConditionUpdate,
    request: Request,
    service: MedicalContextService = Depends(get_medical_context_service),
    current_user: dict = Depends(get_current_user)
) -> ConditionResponse:
    """Update a specific condition."""
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Updating condition",
        user_id=user_id,
        condition_id=condition_id,
        update_fields=list(update_data.model_dump(exclude_unset=True).keys()),
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        condition = service.update_condition(condition_id, user_id, update_data)
        
        if not condition:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Condition with ID '{condition_id}' not found"
            )
        
        # Record metrics
        record_user_action("condition_updated", user_id)
        record_database_query("condition", "update", time.time() - start_time)
        
        logger.info(
            "Condition updated successfully",
            user_id=user_id,
            condition_id=condition_id,
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        
        return condition
        
    except HTTPException:
        # Re-raise HTTP exceptions (e.g., validation errors)
        raise
    except Exception as e:
        # Record error and return 500
        record_error("condition_update_error", str(e))
        logger.error(
            "Failed to update condition",
            user_id=user_id,
            condition_id=condition_id,
            error=str(e),
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update condition"
        )


@router.delete(
    "/conditions/{condition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete condition", 
    description="Delete (deactivate) a specific condition",
    tags=["conditions"]
)
@track_user_action("condition_delete")
async def delete_condition(
    condition_id: str,
    request: Request,
    service: MedicalContextService = Depends(get_medical_context_service),
    current_user: dict = Depends(get_current_user)
):
    """Delete (deactivate) a specific condition."""
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Deleting condition",
        user_id=user_id,
        condition_id=condition_id,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        deleted = service.delete_condition(condition_id, user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Condition with ID '{condition_id}' not found"
            )
        
        # Record metrics
        record_user_action("condition_deleted", user_id)
        record_database_query("condition", "delete", time.time() - start_time)
        
        logger.info(
            "Condition deleted successfully",
            user_id=user_id,
            condition_id=condition_id,
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (e.g., 404)
        raise
    except Exception as e:
        # Record error and return 500
        record_error("condition_delete_error", str(e))
        logger.error(
            "Failed to delete condition",
            user_id=user_id,
            condition_id=condition_id,
            error=str(e),
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete condition"
        )


# Doctor endpoints
@router.post(
    "/doctors",
    response_model=DoctorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create doctor",
    description="Create a new doctor record for the authenticated user",
    tags=["doctors"]
)
@track_user_action("doctor_create")
async def create_doctor(
    doctor_data: DoctorCreate,
    request: Request,
    service: MedicalContextService = Depends(get_medical_context_service),
    current_user: dict = Depends(get_current_user)
) -> DoctorResponse:
    """Create a new doctor record."""
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Creating doctor",
        user_id=user_id,
        doctor_name=doctor_data.name,
        specialty=doctor_data.specialty,
        is_active=doctor_data.is_active,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        doctor = service.create_doctor(doctor_data, user_id)
        
        # Record metrics
        record_user_action("doctor_created", user_id)
        record_database_query("doctor", "create", time.time() - start_time)
        
        logger.info(
            "Doctor created successfully",
            user_id=user_id,
            doctor_id=doctor.id,
            doctor_name=doctor.name,
            specialty=doctor.specialty,
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        
        return doctor
        
    except HTTPException:
        # Re-raise HTTP exceptions (e.g., validation errors)
        raise
    except Exception as e:
        # Record error and return 500
        record_error("doctor_creation_error", str(e))
        logger.error(
            "Failed to create doctor",
            user_id=user_id,
            doctor_name=doctor_data.name,
            error=str(e),
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create doctor"
        )


@router.get(
    "/doctors",
    response_model=List[DoctorResponse],
    summary="List doctors",
    description="Get all doctors for the authenticated user",
    tags=["doctors"]
)
@track_user_action("doctor_list")
async def list_doctors(
    request: Request,
    active_only: bool = Query(False, description="Only return active doctors"),
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    service: MedicalContextService = Depends(get_medical_context_service),
    current_user: dict = Depends(get_current_user)
) -> List[DoctorResponse]:
    """Get all doctors for the authenticated user."""
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Listing doctors",
        user_id=user_id,
        active_only=active_only,
        specialty=specialty,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        doctors = service.get_user_doctors(user_id, active_only=active_only, specialty=specialty)
        
        # Record metrics
        record_user_action("doctors_listed", user_id)
        record_database_query("doctor", "list", time.time() - start_time)
        
        logger.info(
            "Doctors retrieved successfully",
            user_id=user_id,
            count=len(doctors),
            active_only=active_only,
            specialty=specialty,
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        
        return doctors
        
    except Exception as e:
        # Record error and return 500
        record_error("doctor_list_error", str(e))
        logger.error(
            "Failed to list doctors",
            user_id=user_id,
            error=str(e),
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve doctors"
        )


@router.get(
    "/doctors/{doctor_id}",
    response_model=DoctorResponse,
    summary="Get doctor",
    description="Get a specific doctor by ID",
    tags=["doctors"]
)
@track_user_action("doctor_get")
async def get_doctor(
    doctor_id: str,
    request: Request,
    service: MedicalContextService = Depends(get_medical_context_service),
    current_user: dict = Depends(get_current_user)
) -> DoctorResponse:
    """Get a specific doctor by ID."""
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Getting doctor",
        user_id=user_id,
        doctor_id=doctor_id,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        doctor = service.get_doctor_by_id(doctor_id, user_id)
        
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID '{doctor_id}' not found"
            )
        
        # Record metrics
        record_user_action("doctor_retrieved", user_id)
        record_database_query("doctor", "get", time.time() - start_time)
        
        logger.info(
            "Doctor retrieved successfully",
            user_id=user_id,
            doctor_id=doctor_id,
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        
        return doctor
        
    except HTTPException:
        # Re-raise HTTP exceptions (e.g., 404)
        raise
    except Exception as e:
        # Record error and return 500
        record_error("doctor_get_error", str(e))
        logger.error(
            "Failed to get doctor",
            user_id=user_id,
            doctor_id=doctor_id,
            error=str(e),
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve doctor"
        )


@router.patch(
    "/doctors/{doctor_id}",
    response_model=DoctorResponse,
    summary="Update doctor",
    description="Update a specific doctor",
    tags=["doctors"]
)
@track_user_action("doctor_update")
async def update_doctor(
    doctor_id: str,
    update_data: DoctorUpdate,
    request: Request,
    service: MedicalContextService = Depends(get_medical_context_service),
    current_user: dict = Depends(get_current_user)
) -> DoctorResponse:
    """Update a specific doctor."""
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Updating doctor",
        user_id=user_id,
        doctor_id=doctor_id,
        update_fields=list(update_data.model_dump(exclude_unset=True).keys()),
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        doctor = service.update_doctor(doctor_id, user_id, update_data)
        
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID '{doctor_id}' not found"
            )
        
        # Record metrics
        record_user_action("doctor_updated", user_id)
        record_database_query("doctor", "update", time.time() - start_time)
        
        logger.info(
            "Doctor updated successfully",
            user_id=user_id,
            doctor_id=doctor_id,
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        
        return doctor
        
    except HTTPException:
        # Re-raise HTTP exceptions (e.g., validation errors)
        raise
    except Exception as e:
        # Record error and return 500
        record_error("doctor_update_error", str(e))
        logger.error(
            "Failed to update doctor",
            user_id=user_id,
            doctor_id=doctor_id,
            error=str(e),
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update doctor"
        )


@router.delete(
    "/doctors/{doctor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete doctor",
    description="Delete (deactivate) a specific doctor",
    tags=["doctors"]
)
@track_user_action("doctor_delete")
async def delete_doctor(
    doctor_id: str,
    request: Request,
    service: MedicalContextService = Depends(get_medical_context_service),
    current_user: dict = Depends(get_current_user)
):
    """Delete (deactivate) a specific doctor."""
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Deleting doctor",
        user_id=user_id,
        doctor_id=doctor_id,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        deleted = service.delete_doctor(doctor_id, user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor with ID '{doctor_id}' not found"
            )
        
        # Record metrics
        record_user_action("doctor_deleted", user_id)
        record_database_query("doctor", "delete", time.time() - start_time)
        
        logger.info(
            "Doctor deleted successfully",
            user_id=user_id,
            doctor_id=doctor_id,
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (e.g., 404)
        raise
    except Exception as e:
        # Record error and return 500
        record_error("doctor_delete_error", str(e))
        logger.error(
            "Failed to delete doctor",
            user_id=user_id,
            doctor_id=doctor_id,
            error=str(e),
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete doctor"
        )


# Doctor-Condition linking endpoints
@router.post(
    "/doctors/link-condition",
    response_model=DoctorConditionLinkResponse,
    status_code=status.HTTP_200_OK,
    summary="Link doctor to condition",
    description="Create a link between a doctor and a condition",
    tags=["doctors", "conditions"]
)
@track_user_action("doctor_condition_link")
async def link_doctor_to_condition(
    link_data: DoctorConditionLinkCreate,
    request: Request,
    service: MedicalContextService = Depends(get_medical_context_service),
    current_user: dict = Depends(get_current_user)
) -> DoctorConditionLinkResponse:
    """Create a link between a doctor and a condition."""
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Linking doctor to condition",
        user_id=user_id,
        doctor_id=link_data.doctor_id,
        condition_id=link_data.condition_id,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        link = service.link_doctor_to_condition(link_data, user_id)
        
        # Record metrics
        record_user_action("doctor_condition_linked", user_id)
        record_database_query("doctor_condition_link", "create", time.time() - start_time)
        
        logger.info(
            "Doctor linked to condition successfully",
            user_id=user_id,
            doctor_id=link_data.doctor_id,
            condition_id=link_data.condition_id,
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        
        return link
        
    except HTTPException:
        # Re-raise HTTP exceptions (e.g., validation errors)
        raise
    except Exception as e:
        # Record error and return 500
        record_error("doctor_condition_link_error", str(e))
        logger.error(
            "Failed to link doctor to condition",
            user_id=user_id,
            doctor_id=link_data.doctor_id,
            condition_id=link_data.condition_id,
            error=str(e),
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to link doctor to condition"
        )


@router.delete(
    "/doctors/{doctor_id}/conditions/{condition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlink doctor from condition",
    description="Remove the link between a doctor and a condition",
    tags=["doctors", "conditions"]
)
@track_user_action("doctor_condition_unlink")
async def unlink_doctor_from_condition(
    doctor_id: str,
    condition_id: str,
    request: Request,
    service: MedicalContextService = Depends(get_medical_context_service),
    current_user: dict = Depends(get_current_user)
):
    """Remove the link between a doctor and a condition."""
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Unlinking doctor from condition",
        user_id=user_id,
        doctor_id=doctor_id,
        condition_id=condition_id,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        unlinked = service.unlink_doctor_from_condition(doctor_id, condition_id, user_id)
        
        if not unlinked:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Link between doctor '{doctor_id}' and condition '{condition_id}' not found"
            )
        
        # Record metrics
        record_user_action("doctor_condition_unlinked", user_id)
        record_database_query("doctor_condition_link", "delete", time.time() - start_time)
        
        logger.info(
            "Doctor unlinked from condition successfully",
            user_id=user_id,
            doctor_id=doctor_id,
            condition_id=condition_id,
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (e.g., 404)
        raise
    except Exception as e:
        # Record error and return 500
        record_error("doctor_condition_unlink_error", str(e))
        logger.error(
            "Failed to unlink doctor from condition",
            user_id=user_id,
            doctor_id=doctor_id,
            condition_id=condition_id,
            error=str(e),
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlink doctor from condition"
        )


# Passport endpoint
@router.get(
    "/passport",
    response_model=List[PassportItem],
    summary="Get medical passport",
    description="Get aggregated view of conditions with linked doctors (list of items)",
    tags=["passport"]
)
@track_user_action("passport_get")
async def get_passport(
    request: Request,
    service: MedicalContextService = Depends(get_medical_context_service),
    current_user: dict = Depends(get_current_user)
) -> List[PassportItem]:
    """Get aggregated view of conditions with linked doctors.

    Contract expects a raw list of passport items rather than an object
    wrapper. Previously returned ``PassportResponse`` with counts; we now
    return ``List[PassportItem]`` directly for contract compliance while
    still logging aggregate metrics.
    """
    
    start_time = time.time()
    user_id = current_user["user_id"]
    
    logger.info(
        "Getting passport",
        user_id=user_id,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        passport_response = service.get_user_passport(user_id)
        passport_items = passport_response.passport
        
        # Record metrics
        record_user_action("passport_retrieved", user_id)
        record_database_query("passport", "get", time.time() - start_time)
        
        logger.info(
            "Passport retrieved successfully",
            user_id=user_id,
            total_conditions=passport_response.total_conditions,
            total_doctors=passport_response.total_doctors,
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        
        return passport_items
        
    except Exception as e:
        # Record error and return 500
        record_error("passport_get_error", str(e))
        logger.error(
            "Failed to get passport",
            user_id=user_id,
            error=str(e),
            duration_ms=round((time.time() - start_time) * 1000, 2)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve passport"
        )
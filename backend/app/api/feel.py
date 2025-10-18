"""
Feel vs Yesterday API Router

This module provides REST API endpoints for feel vs yesterday analysis
in the SaaS Medical Tracker application.
"""

import time
from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.schemas.logs import FeelVsYesterdayResponse
from app.services.feel_service import FeelVsYesterdayService
from app.telemetry.metrics import (
    record_user_action,
    record_database_query,
    record_error,
    track_user_action,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get(
    "/feel-vs-yesterday",
    response_model=FeelVsYesterdayResponse,
    summary="Feel vs yesterday analysis",
    description="Analyze how the user feels today compared to yesterday based on medication and symptom logs"
)
@track_user_action("feel_analysis_request")
async def feel_vs_yesterday(
    request: Request,
    target_date: Optional[datetime] = Query(
        None,
        description="Date to compare against (defaults to today). Format: YYYY-MM-DDTHH:MM:SS"
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> FeelVsYesterdayResponse:
    """
    Analyze how the user feels today compared to yesterday.
    
    This endpoint analyzes medication effectiveness, symptom severity,
    and overall patterns to provide a meaningful comparison between
    today and yesterday.
    
    The analysis considers:
    - Medication effectiveness ratings
    - Medication side effects
    - Symptom severity levels
    - Symptom impact ratings
    - Overall log counts
    
    Returns a status of 'better', 'same', 'worse', or 'unknown' along
    with a confidence score and human-readable summary.
    """
    
    start_time = time.time()
    user_id = current_user["user_id"]
    analysis_date = target_date or datetime.now(timezone.utc)
    
    logger.info(
        "Analyzing feel vs yesterday",
        user_id=user_id,
        target_date=analysis_date.date().isoformat(),
        analysis_date_iso=analysis_date.isoformat(),
        request_id=getattr(request.state, 'request_id', None)
    )
    
    try:
        # Initialize service and perform analysis
        service_start = time.time()
        feel_service = FeelVsYesterdayService(db)
        result = feel_service.analyze_feel_vs_yesterday(user_id, analysis_date)
        service_duration = time.time() - service_start
        
        # Record business metrics
        record_user_action("feel_analysis_completed", str(user_id))
        record_database_query("feel_analysis", service_duration, "success")
        
        # Log successful analysis
        total_duration = time.time() - start_time
        logger.info(
            "Feel vs yesterday analysis completed",
            user_id=user_id,
            status=result.status,
            confidence=result.confidence,
            has_summary=bool(result.summary),
            medication_logs_count=result.medication_logs_count if hasattr(result, 'medication_logs_count') else None,
            symptom_logs_count=result.symptom_logs_count if hasattr(result, 'symptom_logs_count') else None,
            total_duration_ms=round(total_duration * 1000, 2),
            service_duration_ms=round(service_duration * 1000, 2),
            request_id=getattr(request.state, 'request_id', None)
        )
        
        return result
        
    except Exception as e:
        # Record error metrics
        record_error("feel_analysis_error", "error")
        record_database_query("feel_analysis", time.time() - start_time, "error")
        
        # Log error with context
        logger.error(
            "Failed to analyze feel vs yesterday",
            user_id=user_id,
            target_date=analysis_date.date().isoformat(),
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
                detail="Failed to analyze feel vs yesterday"
            )


@router.get(
    "/feel-vs-yesterday/history",
    response_model=list[FeelVsYesterdayResponse],
    summary="Feel vs yesterday history",
    description="Get feel vs yesterday analysis for multiple days"
)
async def feel_vs_yesterday_history(
    days: int = Query(
        default=7,
        ge=1,
        le=30,
        description="Number of days to analyze (1-30)"
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> list[FeelVsYesterdayResponse]:
    """
    Get feel vs yesterday analysis for multiple days.
    
    This endpoint provides historical feel vs yesterday analysis
    for the specified number of days, allowing users to see
    trends in their condition over time.
    """
    
    user_id = current_user["user_id"]
    
    logger.info(
        "Getting feel vs yesterday history",
        user_id=user_id,
        days=days
    )
    
    # Initialize service
    feel_service = FeelVsYesterdayService(db)
    results = []
    
    # Analyze each day
    for i in range(days):
        from datetime import timedelta
        analysis_date = datetime.now(timezone.utc) - timedelta(days=i)
        
        try:
            result = feel_service.analyze_feel_vs_yesterday(user_id, analysis_date)
            results.append(result)
        except Exception as e:
            logger.warning(
                "Failed to analyze day",
                user_id=user_id,
                date=analysis_date.date().isoformat(),
                error=str(e)
            )
            # Continue with other days
            continue
    
    logger.info(
        "Feel vs yesterday history completed",
        user_id=user_id,
        results_count=len(results)
    )
    
    return results


# Health check endpoint for the feel service
@router.get(
    "/feel-vs-yesterday/health",
    summary="Feel service health check",
    description="Check if the feel vs yesterday service is working correctly"
)
async def feel_service_health_check(
    db: Session = Depends(get_db)
) -> dict:
    """
    Health check for the feel vs yesterday service.
    
    This endpoint can be used to verify that the service
    is working correctly and can access the database.
    """
    
    try:
        # Try to initialize the service
        feel_service = FeelVsYesterdayService(db)
        
        # Test basic functionality
        from datetime import timedelta
        test_date = datetime.now(timezone.utc) - timedelta(days=1)
        
        # This should work even with no data
        result = feel_service._get_date_boundaries(test_date)
        
        return {
            "status": "healthy",
            "service": "FeelVsYesterdayService",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_date_boundaries": {
                "start": result[0].isoformat(),
                "end": result[1].isoformat()
            }
        }
        
    except Exception as e:
        logger.error(
            "Feel service health check failed",
            error=str(e),
            error_type=type(e).__name__
        )
        
        return {
            "status": "unhealthy",
            "service": "FeelVsYesterdayService", 
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }


# Example usage and testing
if __name__ == "__main__":
    print("✅ Feel vs Yesterday API router created successfully")
    print("Available endpoints:")
    print("- GET /feel-vs-yesterday - Analyze feel vs yesterday")
    print("- GET /feel-vs-yesterday/history - Get historical analysis")
    print("- GET /feel-vs-yesterday/health - Service health check")
    print("")
    print("Analysis considers:")
    print("- Medication effectiveness ratings")
    print("- Medication side effects severity")
    print("- Symptom severity levels")
    print("- Symptom impact ratings")
    print("- Overall log counts")
    print("")
    print("Returns status: 'better' | 'same' | 'worse' | 'unknown'")
"""
Web Vitals Collection API

Collects and stores Core Web Vitals metrics from the frontend:
- Largest Contentful Paint (LCP)
- First Input Delay (FID) 
- Cumulative Layout Shift (CLS)
- First Contentful Paint (FCP)
- Time to First Byte (TTFB)
- Total Blocking Time (TBT)

Usage:
    POST /api/v1/telemetry/web-vitals
    {
        "lcp": 1234,
        "fid": 56,
        "cls": 0.02,
        "fcp": 987,
        "ttfb": 234,
        "tbt": 123,
        "url": "/dashboard",
        "user_agent": "Mozilla/5.0...",
        "connection_type": "4g"
    }
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field, validator
from sqlmodel import SQLModel, Field as SQLField, select
import structlog

from app.core.dependencies import get_current_user_id, get_db_session
from app.core.telemetry.metrics import web_vitals_counter, web_vitals_histogram
from app.models.base import BaseEntity


logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/telemetry", tags=["telemetry"])


class WebVitalsModel(BaseEntity, table=True):
    """Database model for web vitals metrics"""
    __tablename__ = "web_vitals"
    
    # Core Web Vitals
    lcp: Optional[float] = SQLField(description="Largest Contentful Paint (ms)")
    fid: Optional[float] = SQLField(description="First Input Delay (ms)")
    cls: Optional[float] = SQLField(description="Cumulative Layout Shift")
    
    # Additional Performance Metrics  
    fcp: Optional[float] = SQLField(description="First Contentful Paint (ms)")
    ttfb: Optional[float] = SQLField(description="Time to First Byte (ms)")
    tbt: Optional[float] = SQLField(description="Total Blocking Time (ms)")
    
    # Context Information
    url: str = SQLField(description="Page URL where metrics were collected")
    user_agent: Optional[str] = SQLField(description="Browser user agent string")
    connection_type: Optional[str] = SQLField(description="Network connection type")
    viewport_width: Optional[int] = SQLField(description="Viewport width in pixels")
    viewport_height: Optional[int] = SQLField(description="Viewport height in pixels")
    
    # Performance Navigation Timing
    navigation_type: Optional[str] = SQLField(description="Navigation type (navigate, reload, back_forward)")
    page_load_time: Optional[float] = SQLField(description="Total page load time (ms)")
    dom_content_loaded: Optional[float] = SQLField(description="DOMContentLoaded time (ms)")
    
    # User Context
    user_id: str = SQLField(foreign_key="users.id", index=True)
    session_id: Optional[str] = SQLField(description="Frontend session ID")


class WebVitalsCreate(BaseModel):
    """Schema for creating web vitals record"""
    
    # Core Web Vitals (at least one required)
    lcp: Optional[float] = Field(None, ge=0, le=30000, description="Largest Contentful Paint (ms)")
    fid: Optional[float] = Field(None, ge=0, le=5000, description="First Input Delay (ms)")
    cls: Optional[float] = Field(None, ge=0, le=5, description="Cumulative Layout Shift")
    
    # Additional metrics
    fcp: Optional[float] = Field(None, ge=0, le=30000, description="First Contentful Paint (ms)")
    ttfb: Optional[float] = Field(None, ge=0, le=30000, description="Time to First Byte (ms)")
    tbt: Optional[float] = Field(None, ge=0, le=30000, description="Total Blocking Time (ms)")
    
    # Required context
    url: str = Field(..., max_length=2048, description="Page URL")
    user_agent: Optional[str] = Field(None, max_length=1024)
    connection_type: Optional[str] = Field(None, max_length=32)
    
    # Viewport information
    viewport_width: Optional[int] = Field(None, ge=0, le=10000)
    viewport_height: Optional[int] = Field(None, ge=0, le=10000)
    
    # Navigation context
    navigation_type: Optional[str] = Field(None, max_length=32)
    page_load_time: Optional[float] = Field(None, ge=0, le=300000)
    dom_content_loaded: Optional[float] = Field(None, ge=0, le=300000)
    
    # Session tracking
    session_id: Optional[str] = Field(None, max_length=128)
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format and security"""
        if not v or len(v.strip()) == 0:
            raise ValueError("URL cannot be empty")
        
        # Basic security: prevent data URLs and javascript URLs
        if v.lower().startswith(('data:', 'javascript:', 'vbscript:')):
            raise ValueError("Invalid URL scheme")
        
        return v.strip()
    
    @validator('connection_type')
    def validate_connection_type(cls, v):
        """Validate connection type"""
        if v is None:
            return v
        
        valid_types = {'slow-2g', '2g', '3g', '4g', '5g', 'wifi', 'ethernet', 'unknown'}
        if v.lower() not in valid_types:
            return 'unknown'
        
        return v.lower()
    
    @validator('navigation_type')
    def validate_navigation_type(cls, v):
        """Validate navigation type"""
        if v is None:
            return v
        
        valid_types = {'navigate', 'reload', 'back_forward', 'prerender'}
        if v.lower() not in valid_types:
            return 'navigate'
        
        return v.lower()


class WebVitalsResponse(BaseModel):
    """Response schema for web vitals"""
    id: str
    lcp: Optional[float]
    fid: Optional[float] 
    cls: Optional[float]
    fcp: Optional[float]
    ttfb: Optional[float]
    tbt: Optional[float]
    url: str
    user_agent: Optional[str]
    connection_type: Optional[str]
    viewport_width: Optional[int]
    viewport_height: Optional[int]
    navigation_type: Optional[str]
    page_load_time: Optional[float]
    dom_content_loaded: Optional[float]
    session_id: Optional[str]
    created_at: datetime


class WebVitalsSummary(BaseModel):
    """Summary statistics for web vitals"""
    total_samples: int
    time_period: str
    
    # Core Web Vitals averages
    avg_lcp: Optional[float]
    avg_fid: Optional[float] 
    avg_cls: Optional[float]
    
    # Performance grade (based on thresholds)
    lcp_grade: str  # good, needs_improvement, poor
    fid_grade: str
    cls_grade: str
    overall_grade: str
    
    # Top pages by volume
    top_pages: List[Dict[str, Any]]
    
    # Device/connection breakdown
    connection_breakdown: Dict[str, int]
    viewport_breakdown: Dict[str, int]


def calculate_web_vitals_grade(lcp: Optional[float], fid: Optional[float], cls: Optional[float]) -> Dict[str, str]:
    """Calculate performance grades based on Core Web Vitals thresholds"""
    
    def grade_lcp(value: Optional[float]) -> str:
        if value is None:
            return "unknown"
        if value <= 2500:
            return "good" 
        elif value <= 4000:
            return "needs_improvement"
        else:
            return "poor"
    
    def grade_fid(value: Optional[float]) -> str:
        if value is None:
            return "unknown"
        if value <= 100:
            return "good"
        elif value <= 300:
            return "needs_improvement" 
        else:
            return "poor"
    
    def grade_cls(value: Optional[float]) -> str:
        if value is None:
            return "unknown"
        if value <= 0.1:
            return "good"
        elif value <= 0.25:
            return "needs_improvement"
        else:
            return "poor"
    
    lcp_grade = grade_lcp(lcp)
    fid_grade = grade_fid(fid)
    cls_grade = grade_cls(cls)
    
    # Overall grade is worst of the three
    grades_priority = {"good": 0, "needs_improvement": 1, "poor": 2, "unknown": -1}
    valid_grades = [g for g in [lcp_grade, fid_grade, cls_grade] if g != "unknown"]
    
    if not valid_grades:
        overall_grade = "unknown"
    else:
        overall_grade = max(valid_grades, key=lambda g: grades_priority[g])
    
    return {
        "lcp_grade": lcp_grade,
        "fid_grade": fid_grade, 
        "cls_grade": cls_grade,
        "overall_grade": overall_grade
    }


async def record_web_vitals_metrics(vitals: WebVitalsCreate):
    """Record web vitals metrics to monitoring system"""
    
    # Update Prometheus metrics
    labels = {
        "url": vitals.url,
        "connection_type": vitals.connection_type or "unknown"
    }
    
    web_vitals_counter.labels(**labels).inc()
    
    if vitals.lcp is not None:
        web_vitals_histogram.labels(metric="lcp", **labels).observe(vitals.lcp)
    
    if vitals.fid is not None:
        web_vitals_histogram.labels(metric="fid", **labels).observe(vitals.fid)
    
    if vitals.cls is not None:
        web_vitals_histogram.labels(metric="cls", **labels).observe(vitals.cls * 1000)  # Scale for histogram
    
    if vitals.fcp is not None:
        web_vitals_histogram.labels(metric="fcp", **labels).observe(vitals.fcp)
    
    if vitals.ttfb is not None:
        web_vitals_histogram.labels(metric="ttfb", **labels).observe(vitals.ttfb)


@router.post("/web-vitals", response_model=WebVitalsResponse)
async def collect_web_vitals(
    vitals: WebVitalsCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db_session=Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Collect Core Web Vitals and performance metrics from frontend
    
    This endpoint receives performance metrics from the browser's Performance API
    and stores them for analysis and monitoring.
    """
    
    # Validate at least one core vital is provided
    if vitals.lcp is None and vitals.fid is None and vitals.cls is None:
        raise HTTPException(
            status_code=400,
            detail="At least one Core Web Vital (LCP, FID, or CLS) must be provided"
        )
    
    try:
        # Create web vitals record
        web_vitals = WebVitalsModel(
            **vitals.dict(),
            user_id=user_id,
            created_at=datetime.now(timezone.utc)
        )
        
        db_session.add(web_vitals)
        db_session.commit()
        db_session.refresh(web_vitals)
        
        # Record metrics in background
        background_tasks.add_task(record_web_vitals_metrics, vitals)
        
        # Log structured event
        logger.info(
            "web_vitals_collected",
            user_id=user_id,
            url=vitals.url,
            lcp=vitals.lcp,
            fid=vitals.fid,
            cls=vitals.cls,
            connection_type=vitals.connection_type,
            viewport_width=vitals.viewport_width,
            session_id=vitals.session_id
        )
        
        return WebVitalsResponse(
            id=web_vitals.id,
            **vitals.dict(),
            created_at=web_vitals.created_at
        )
        
    except Exception as e:
        logger.error(
            "web_vitals_collection_failed",
            user_id=user_id,
            error=str(e),
            url=vitals.url
        )
        db_session.rollback()
        raise HTTPException(status_code=500, detail="Failed to save web vitals data")


@router.get("/web-vitals/summary", response_model=WebVitalsSummary)
async def get_web_vitals_summary(
    days: int = 7,
    page: Optional[str] = None,
    db_session=Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Get Web Vitals summary statistics for the current user
    
    Provides aggregated performance metrics and grades over the specified time period.
    """
    
    try:
        # Build query with time filter
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        query = select(WebVitalsModel).where(
            WebVitalsModel.user_id == user_id,
            WebVitalsModel.created_at >= since_date
        )
        
        # Optional page filter
        if page:
            query = query.where(WebVitalsModel.url.contains(page))
        
        results = db_session.exec(query).all()
        
        if not results:
            return WebVitalsSummary(
                total_samples=0,
                time_period=f"{days} days",
                avg_lcp=None,
                avg_fid=None,
                avg_cls=None,
                lcp_grade="unknown",
                fid_grade="unknown", 
                cls_grade="unknown",
                overall_grade="unknown",
                top_pages=[],
                connection_breakdown={},
                viewport_breakdown={}
            )
        
        # Calculate averages
        lcp_values = [r.lcp for r in results if r.lcp is not None]
        fid_values = [r.fid for r in results if r.fid is not None]
        cls_values = [r.cls for r in results if r.cls is not None]
        
        avg_lcp = sum(lcp_values) / len(lcp_values) if lcp_values else None
        avg_fid = sum(fid_values) / len(fid_values) if fid_values else None
        avg_cls = sum(cls_values) / len(cls_values) if cls_values else None
        
        # Calculate grades
        grades = calculate_web_vitals_grade(avg_lcp, avg_fid, avg_cls)
        
        # Top pages by sample count
        page_counts = {}
        connection_counts = {}
        viewport_counts = {}
        
        for result in results:
            # Page breakdown
            page_counts[result.url] = page_counts.get(result.url, 0) + 1
            
            # Connection breakdown
            conn_type = result.connection_type or "unknown"
            connection_counts[conn_type] = connection_counts.get(conn_type, 0) + 1
            
            # Viewport breakdown (categorized)
            if result.viewport_width:
                if result.viewport_width < 768:
                    viewport_category = "mobile"
                elif result.viewport_width < 1024:
                    viewport_category = "tablet"
                else:
                    viewport_category = "desktop"
                viewport_counts[viewport_category] = viewport_counts.get(viewport_category, 0) + 1
        
        # Sort pages by count and take top 10
        top_pages = [
            {"url": url, "samples": count}
            for url, count in sorted(page_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return WebVitalsSummary(
            total_samples=len(results),
            time_period=f"{days} days",
            avg_lcp=round(avg_lcp, 1) if avg_lcp else None,
            avg_fid=round(avg_fid, 1) if avg_fid else None,
            avg_cls=round(avg_cls, 3) if avg_cls else None,
            lcp_grade=grades["lcp_grade"],
            fid_grade=grades["fid_grade"],
            cls_grade=grades["cls_grade"], 
            overall_grade=grades["overall_grade"],
            top_pages=top_pages,
            connection_breakdown=connection_counts,
            viewport_breakdown=viewport_counts
        )
        
    except Exception as e:
        logger.error(
            "web_vitals_summary_failed",
            user_id=user_id,
            days=days,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to generate web vitals summary")


@router.delete("/web-vitals")
async def clear_web_vitals(
    older_than_days: int = 30,
    db_session=Depends(get_db_session),
    user_id: str = Depends(get_current_user_id)
):
    """
    Clear old web vitals data for the current user
    
    Useful for data retention and privacy compliance.
    """
    
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        
        # Delete old records
        query = select(WebVitalsModel).where(
            WebVitalsModel.user_id == user_id,
            WebVitalsModel.created_at < cutoff_date
        )
        
        old_records = db_session.exec(query).all()
        
        for record in old_records:
            db_session.delete(record)
        
        db_session.commit()
        
        logger.info(
            "web_vitals_cleared",
            user_id=user_id,
            records_deleted=len(old_records),
            older_than_days=older_than_days
        )
        
        return {
            "message": f"Cleared {len(old_records)} web vitals records older than {older_than_days} days"
        }
        
    except Exception as e:
        logger.error(
            "web_vitals_clear_failed",
            user_id=user_id,
            error=str(e)
        )
        db_session.rollback()
        raise HTTPException(status_code=500, detail="Failed to clear web vitals data")
"""
API Routes Module

This module provides the main API routing structure for the SaaS Medical Tracker.
It includes route organization, API versioning, and endpoint registration.
"""

from typing import Any, Dict

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.schemas import HealthCheckResponse

# Import actual router implementations
from app.api.feel import router as feel_router
from app.api.logs import router as logs_router
from app.api.medical_context import router as medical_context_router
from app.api.v1.endpoints.medications import router as medications_actual_router

logger = structlog.get_logger(__name__)
settings = get_settings()

# Create the main API router
api_router = APIRouter()

# API Version 1 router
api_v1_router = APIRouter(prefix="/api/v1")


# Health Check Endpoints
@api_v1_router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint for service monitoring.
    
    Returns:
        HealthCheckResponse: Service health status
    """
    from datetime import datetime

    from app.models.base import check_database_health

    # Check database connectivity
    db_healthy = check_database_health()

    # Determine overall status
    overall_status = "healthy" if db_healthy else "unhealthy"

    logger.info(
        "Health check performed",
        status=overall_status,
        database_healthy=db_healthy
    )

    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.VERSION,
        database=db_healthy
    )


@api_v1_router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint.
    
    Returns:
        Dict: Readiness status
    """
    from app.models.base import check_database_health

    # Check if all dependencies are ready
    db_ready = check_database_health()

    if not db_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready - database unavailable"
        )

    return {"status": "ready"}


@api_v1_router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        Dict: Liveness status
    """
    # Basic liveness check - just return OK if we can process requests
    return {"status": "alive"}


# Metrics endpoint (basic placeholder)
@api_v1_router.get("/metrics")
async def metrics() -> Dict[str, Any]:
    """Basic metrics endpoint without external psutil dependency.

    Tests only assert presence of top-level keys and (optionally) some system
    metrics. We'll attempt psutil import; if unavailable, we gracefully fall
    back to a minimal payload so the endpoint never raises ModuleNotFoundError.
    """
    import os
    from datetime import datetime

    memory_total = None
    memory_available = None
    memory_percent = None
    disk_total = None
    disk_free = None
    disk_percent = None

    try:
        import psutil  # type: ignore
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        memory_total = memory_info.total
        memory_available = memory_info.available
        memory_percent = memory_info.percent
        disk_total = disk_info.total
        disk_free = disk_info.free
        disk_percent = round((disk_info.used / disk_info.total) * 100, 2)
    except Exception as e:  # noqa: BLE001
        logger.warning("System metrics collection unavailable", error=str(e))

    payload: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat(),
        "application": {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        },
        "process": {
            "pid": os.getpid(),
        },
    }

    # Only include system section if we gathered any metrics.
    if memory_total is not None:
        payload["system"] = {
            "memory_total": memory_total,
            "memory_available": memory_available,
            "memory_percent": memory_percent,
            "disk_total": disk_total,
            "disk_free": disk_free,
            "disk_percent": disk_percent,
        }

    return payload


# Root redirect
@api_router.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root path to API documentation."""
    return RedirectResponse(url="/docs")


# API Info endpoint
@api_v1_router.get("/info")
async def api_info() -> Dict[str, Any]:
    """
    Get API information and configuration.
    
    Returns basic information about the API for discovery purposes.
    
    Returns:
        Dict: API information
    """
    return {
        "name": settings.PROJECT_NAME,
        "description": settings.PROJECT_DESCRIPTION,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "api_version": "v1",
        "features": {
            "medication_master": settings.ENABLE_MEDICATION_MASTER,
            "health_passport": settings.ENABLE_HEALTH_PASSPORT,
        },
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/api/v1/health",
            "metrics": "/api/v1/metrics",
        }
    }


# Authentication endpoints (placeholder structure)
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/token")
async def login():
    """Login endpoint - placeholder."""
    # This will be implemented in the authentication module
    # We raise HTTPException; the handler will transform 501 differently if needed.
    # To satisfy tests expecting 'detail' plus 'error'/'message', embed compound structure.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication endpoints not yet implemented"
    )


@auth_router.post("/register")
async def register():
    """Registration endpoint - placeholder."""
    # This will be implemented in the authentication module
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication endpoints not yet implemented"
    )


@auth_router.post("/refresh")
async def refresh_token():
    """Token refresh endpoint - placeholder."""
    # This will be implemented in the authentication module
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication endpoints not yet implemented"
    )


# Users endpoints (placeholder structure)
users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("/me")
async def get_current_user():
    """Get current user profile - placeholder."""
    # This will be implemented with user management
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User endpoints not yet implemented"
    )


@users_router.put("/me")
async def update_current_user():
    """Update current user profile - placeholder."""
    # This will be implemented with user management
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User endpoints not yet implemented"
    )


# Medications endpoints are now implemented in v1/endpoints/medications.py
# We'll include the actual router below


# Symptoms endpoints (placeholder structure)
symptoms_router = APIRouter(prefix="/symptoms", tags=["Symptoms"])


@symptoms_router.get("/")
async def list_symptom_logs():
    """List user symptom logs - placeholder."""
    # This will be implemented in symptoms module
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Symptom endpoints not yet implemented"
    )


@symptoms_router.post("/")
async def create_symptom_log():
    """Create new symptom log - placeholder."""
    # This will be implemented in symptoms module
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Symptom endpoints not yet implemented"
    )


# Register all routers with the main API v1 router
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(medications_actual_router)  # Actual medication endpoints
api_v1_router.include_router(symptoms_router)

# Register Phase 3 US1 routers
api_v1_router.include_router(logs_router, tags=["Logs"])
api_v1_router.include_router(feel_router, tags=["Feel Analysis"])

# Register Phase 5 US3 routers (versioned)
api_v1_router.include_router(medical_context_router, tags=["Medical Context"])

# Contract tests expect unprefixed paths (/conditions, /doctors, /passport).
# Expose medical context router at root level as well for backward/contract compatibility.
api_router.include_router(medical_context_router, tags=["Medical Context (root)"])

# Register the main API v1 router with the main API router
api_router.include_router(api_v1_router)


def get_router() -> APIRouter:
    """
    Get the configured main API router.
    
    Returns:
        APIRouter: Main API router with all endpoints
    """
    return api_router


# Route discovery utility
def get_route_list() -> list:
    """
    Get a list of all registered routes for debugging/documentation.
    
    Returns:
        list: List of route information
    """
    routes = []

    def extract_routes(router: APIRouter, prefix: str = ""):
        for route in router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                # It's an actual endpoint route
                routes.append({
                    "path": prefix + route.path,
                    "methods": list(route.methods),
                    "name": route.name,
                    "tags": getattr(route, 'tags', [])
                })
            elif hasattr(route, 'router'):
                # It's a sub-router
                sub_prefix = prefix + getattr(route, 'prefix', '')
                extract_routes(route.router, sub_prefix)

    extract_routes(api_router)
    return routes


# Example usage and testing
if __name__ == "__main__":
    # Print all registered routes
    routes = get_route_list()

    print("✅ API Routes configured")
    print(f"Total routes: {len(routes)}")
    print("\nRegistered routes:")

    for route in routes:
        methods = ", ".join(route["methods"])
        tags = ", ".join(route["tags"]) if route["tags"] else "No tags"
        print(f"  {methods:20} {route['path']:40} ({tags})")

    print("\nAPI structure:")
    print("- Root: / -> redirects to /docs")
    print("- API v1: /api/v1/")
    print("  - Health: /api/v1/health")
    print("  - Info: /api/v1/info")
    print("  - Auth: /api/v1/auth/*")
    print("  - Users: /api/v1/users/*")
    print("  - Medications: /api/v1/medications/*")
    print("  - Symptoms: /api/v1/symptoms/*")
    print("- Metrics: /api/v1/metrics")
    print("- Documentation: /docs, /redoc")

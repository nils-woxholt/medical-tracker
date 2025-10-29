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
from app.api.logs_minimal import router as logs_minimal_router  # minimal test-only root exposure
# from app.api.logs import router as logs_full_router  # disabled pending create_medication_log field analysis issue
from app.api.medical_context import router as medical_context_router
from app.api.v1.endpoints.medications import router as medications_actual_router
# Use new session-based auth router (Phase 3) instead of legacy token endpoints for login/logout
from app.api.auth import auth_router as auth_session_router
from app.api.auth import versioned_auth_router
from app.api.auth_identity import router as identity_router  # Phase 2 identity endpoint (/auth/me)

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

    # Check database connectivity (returns DatabaseHealthStatus dataclass-like object)
    db_status = check_database_health()
    db_healthy_bool = bool(getattr(db_status, "status", None) == "healthy")

    # Determine overall status
    overall_status = "healthy" if db_healthy_bool else "unhealthy"

    logger.info(
        "Health check performed",
        status=overall_status,
        database_healthy=db_status,
        database_response_time_ms=getattr(db_status, "response_time_ms", None),
        database_error=getattr(db_status, "error", None)
    )

    # Return boolean per schema; additional details not in schema intentionally omitted
    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.VERSION,
        database=db_healthy_bool
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


# Users endpoints (still placeholder; retained until implemented properly)
users_router = APIRouter(prefix="/users", tags=["Users"])

@users_router.get("/me")
async def get_current_user_placeholder():  # distinct name to avoid conflict with dependency
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="User endpoints not yet implemented")

@users_router.put("/me")
async def update_current_user_placeholder():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="User endpoints not yet implemented")


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


# Register all routers with the main API v1 router (exclude functional auth router to preserve 501 placeholders under /api/v1/auth/*)
# Expose minimal logs under versioned path but require authentication to satisfy /api/v1 unauthorized contract tests.
from app.core.dependencies import get_authenticated_user
api_v1_router.include_router(logs_minimal_router, dependencies=[Depends(get_authenticated_user)])
api_v1_router.include_router(users_router)
api_v1_router.include_router(medications_actual_router)  # Actual medication endpoints (versioned)
api_v1_router.include_router(symptoms_router)

# Backward-compat placeholder endpoints expected by existing tests (return 501)
@api_v1_router.post("/auth/token", include_in_schema=False)
async def _placeholder_auth_token():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Authentication endpoints not yet implemented")


@api_v1_router.post("/auth/refresh", include_in_schema=False)
async def _placeholder_auth_refresh():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Authentication endpoints not yet implemented")

# Register Phase 3 US1 routers
# api_v1_router.include_router(logs_full_router, tags=["Logs"])  # disabled pending fix
api_v1_router.include_router(feel_router, tags=["Feel Analysis"])

# Register Phase 5 US3 routers (versioned)
api_v1_router.include_router(medical_context_router, tags=["Medical Context"])

# Contract tests expect some unprefixed paths (/conditions, /doctors, /passport, /medications).
# Expose medical context router and medications router at root level as well for backward/contract compatibility.
api_router.include_router(medical_context_router, tags=["Medical Context (root)"])
api_router.include_router(medications_actual_router, tags=["Medications (root)"])
# Expose minimal logs endpoints at root AND versioned path for backward compatibility tests
api_router.include_router(logs_minimal_router, tags=["Logs (root, legacy)"])
# Expose auth session router at root level for integration tests expecting /auth/login
api_router.include_router(auth_session_router, tags=["Auth (root)"])
api_router.include_router(identity_router, tags=["Auth Identity (root)"])  # New lightweight identity endpoint
# Contract/integration tests call /logs/medications without version prefix.
# Expose logs router at root level for backward/contract compatibility.

# Register the main API v1 router with the main API router
api_router.include_router(api_v1_router)

# Include legacy versioned auth placeholder routes for backward compatibility tests
api_router.include_router(versioned_auth_router)


def get_router() -> APIRouter:
    """
    Get the configured main API router.
    
    Returns:
        APIRouter: Main API router with all endpoints
    """
    return api_router


# Route discovery utility
def get_route_list() -> list:
    """Return list of registered routes with safe attribute access.

    Lint previously complained about BaseRoute missing attributes when accessed
    blindly. We now use getattr with defaults and only include entries that look
    like standard APIRoute instances.
    """
    from fastapi.routing import APIRoute
    collected = []

    def walk(router: APIRouter, prefix: str = ""):
        for r in router.routes:
            # Normal FastAPI route
            if isinstance(r, APIRoute):
                collected.append({
                    "path": prefix + getattr(r, 'path', ''),
                    "methods": list(getattr(r, 'methods', [])),
                    "name": getattr(r, 'name', None),
                    "tags": getattr(r, 'tags', [])
                })
            # Nested router include (Mount or sub-APIRouter) - FastAPI uses r.app with .routes
            nested_router = getattr(r, 'router', None) or getattr(getattr(r, 'app', None), 'router', None)
            if nested_router and hasattr(nested_router, 'routes'):
                sub_prefix = prefix + getattr(r, 'path', '')
                walk(nested_router, sub_prefix)

    walk(api_router)
    return collected


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

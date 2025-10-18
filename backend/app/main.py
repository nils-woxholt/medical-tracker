"""
SaaS Medical Tracker - Main FastAPI Application

This module contains the main FastAPI application factory and configuration.
It sets up the API routes, middleware, and database connections.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI

from app.api import get_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.middleware import setup_exception_handlers, setup_middleware
from app.models.base import init_database
from app.telemetry.metrics import setup_metrics

# Initialize structured logging
setup_logging()
logger = structlog.get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan event handler for startup and shutdown operations.
    
    This function handles:
    - Database initialization on startup
    - Resource cleanup on shutdown
    - Logging of application lifecycle events
    """
    # Startup
    logger.info("🚀 Starting SaaS Medical Tracker API", version=settings.VERSION)

    try:
        # Initialize database
        init_database()
        logger.info("✅ Database initialized successfully")

        # Metrics system is already initialized during app creation
        # (no need to call setup_metrics here again)

        # TODO: Initialize other services (Redis, etc.)
        logger.info("✅ Application startup completed")

    except Exception as e:
        logger.error("❌ Failed to initialize application", error=str(e))
        raise

    yield  # Application runs here

    # Shutdown
    logger.info("🛑 Shutting down SaaS Medical Tracker API")
    # TODO: Cleanup resources (close DB connections, etc.)
    logger.info("✅ Application shutdown completed")


def create_app() -> FastAPI:
    """
    FastAPI application factory.
    
    Creates and configures a FastAPI application instance with:
    - API routes and middleware
    - CORS configuration
    - Error handlers
    - Health checks
    - OpenAPI documentation
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENVIRONMENT != "production" else None,
        docs_url=f"{settings.API_V1_STR}/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url=f"{settings.API_V1_STR}/redoc" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )

    # Setup middleware (CORS, security headers, request ID, timing, metrics, etc.)
    setup_middleware(app)

    # Setup metrics collection (includes metrics middleware)
    setup_metrics(app)

    # Setup exception handlers (validation, HTTP, general)
    setup_exception_handlers(app)

    # Health check and root endpoints are now handled by the API router

    # Include API routes
    main_router = get_router()
    app.include_router(main_router)

    # Exception handlers are now managed by the middleware module

    logger.info("✅ FastAPI application created successfully")
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    # For development only
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None,  # Use our custom logging
    )

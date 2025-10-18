"""
FastAPI Exception Handlers and Custom Middleware

This module provides centralized exception handling and middleware components
for the SaaS Medical Tracker application, including request ID tracking,
timing, CORS, and comprehensive error management.
"""

import time
import uuid
from typing import Optional

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.settings import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request ID to each request.
    
    The request ID can be used for tracing and debugging purposes.
    It's added to the response headers and made available to all handlers.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add request ID."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Add to request state for access in handlers
        request.state.request_id = request_id

        # Add to structlog context for automatic logging
        with structlog.contextvars.bound_contextvars(request_id=request_id):
            # Process the request
            response = await call_next(request)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to measure and log request processing time.
    
    Logs request timing information and adds timing headers to responses.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and measure timing."""
        start_time = time.time()

        # Get request info for logging
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        logger.info(
            "Request started",
            method=method,
            url=url,
            client_ip=client_ip,
            user_agent=user_agent,
        )

        try:
            # Process the request
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)

            # Log successful request
            logger.info(
                "Request completed",
                method=method,
                url=url,
                status_code=response.status_code,
                process_time_seconds=round(process_time, 4),
            )

            return response

        except Exception as e:
            # Calculate processing time even for errors
            process_time = time.time() - start_time

            # Log error
            logger.error(
                "Request failed",
                method=method,
                url=url,
                process_time_seconds=round(process_time, 4),
                error=str(e),
                error_type=type(e).__name__,
            )

            # Re-raise to let error handlers process it
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Implements common security headers to protect against various attacks.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers."""
        response = await call_next(request)

        # Add security headers
        response.headers.update({
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",

            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",

            # Prevent page from being displayed in frame
            "X-Frame-Options": "DENY",

            # HSTS header (only in production with HTTPS)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
            if getattr(settings, 'ENVIRONMENT', 'development') == "production" else "",

            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",

            # Content Security Policy (basic)
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'"
        })

        return response


class TracingHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle distributed tracing headers.
    
    Supports standard tracing headers for request correlation across services:
    - X-Trace-Id: Unique identifier for the entire request trace
    - X-Span-Id: Unique identifier for this service span
    - X-Parent-Span-Id: Parent span ID from upstream service
    - X-Correlation-Id: Business correlation identifier
    - X-Request-Id: Service-specific request identifier
    
    Also supports OpenTelemetry standard headers:
    - traceparent: W3C Trace Context header
    - tracestate: W3C Trace Context state
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and propagate tracing headers."""
        
        # Extract incoming tracing headers
        trace_id = self._get_trace_id(request)
        parent_span_id = self._get_parent_span_id(request)
        correlation_id = self._get_correlation_id(request)
        
        # Generate new span ID for this service
        span_id = str(uuid.uuid4())
        
        # Store tracing context in request state
        request.state.trace_id = trace_id
        request.state.span_id = span_id
        request.state.parent_span_id = parent_span_id
        request.state.correlation_id = correlation_id
        
        # Add to structlog context for automatic logging
        with structlog.contextvars.bound_contextvars(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            correlation_id=correlation_id
        ):
            # Process the request
            response = await call_next(request)
            
            # Add tracing headers to response
            response.headers.update({
                "X-Trace-Id": trace_id,
                "X-Span-Id": span_id,
                "X-Correlation-Id": correlation_id
            })
            
            if parent_span_id:
                response.headers["X-Parent-Span-Id"] = parent_span_id
            
            # Log trace completion
            logger.debug(
                "trace_completed",
                trace_id=trace_id,
                span_id=span_id,
                method=request.method,
                url=str(request.url.path),
                status_code=response.status_code
            )
            
            return response
    
    def _get_trace_id(self, request: Request) -> str:
        """Extract or generate trace ID."""
        # Check for existing trace ID in various header formats
        trace_id = (
            request.headers.get("X-Trace-Id") or
            request.headers.get("trace-id") or 
            request.headers.get("X-B3-TraceId") or
            self._extract_w3c_trace_id(request) or
            str(uuid.uuid4())
        )
        return trace_id
    
    def _get_parent_span_id(self, request: Request) -> Optional[str]:
        """Extract parent span ID from headers."""
        return (
            request.headers.get("X-Span-Id") or
            request.headers.get("span-id") or
            request.headers.get("X-B3-SpanId") or
            self._extract_w3c_parent_id(request)
        )
    
    def _get_correlation_id(self, request: Request) -> str:
        """Extract or generate correlation ID."""
        correlation_id = (
            request.headers.get("X-Correlation-Id") or
            request.headers.get("correlation-id") or
            request.headers.get("X-Request-ID") or
            str(uuid.uuid4())
        )
        return correlation_id
    
    def _extract_w3c_trace_id(self, request: Request) -> Optional[str]:
        """Extract trace ID from W3C traceparent header."""
        traceparent = request.headers.get("traceparent")
        if traceparent:
            try:
                # W3C traceparent format: version-trace_id-parent_id-trace_flags
                parts = traceparent.split("-")
                if len(parts) >= 2:
                    return parts[1]  # trace_id is the second part
            except Exception:
                pass
        return None
    
    def _extract_w3c_parent_id(self, request: Request) -> Optional[str]:
        """Extract parent span ID from W3C traceparent header."""
        traceparent = request.headers.get("traceparent")
        if traceparent:
            try:
                # W3C traceparent format: version-trace_id-parent_id-trace_flags
                parts = traceparent.split("-")
                if len(parts) >= 3:
                    return parts[2]  # parent_id is the third part
            except Exception:
                pass
        return None


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle authentication context.
    
    Extracts and validates authentication tokens, making user context
    available to request handlers.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and handle authentication."""
        # Extract authorization header
        authorization = request.headers.get("Authorization")

        # Initialize auth context
        request.state.user_id = None
        request.state.user_email = None
        request.state.is_authenticated = False

        # Skip auth for public endpoints
        public_paths = [
            "/docs", "/redoc", "/openapi.json",
            "/health", "/metrics", "/",
            "/api/v1/auth/token",
            "/api/v1/auth/register"
        ]

        path = request.url.path
        if any(path.startswith(public) for public in public_paths):
            return await call_next(request)

        # Process authentication if present
        if authorization:
            try:
                from app.core.auth import decode_access_token, validate_token_format

                # Extract and validate token
                token = validate_token_format(authorization)
                payload = decode_access_token(token)

                # Set authentication context
                request.state.user_id = payload.get("user_id")
                request.state.user_email = payload.get("sub")
                request.state.is_authenticated = True

                logger.debug(
                    "Authentication successful",
                    user_email=request.state.user_email,
                    privacy_filtered=True
                )

            except Exception as e:
                logger.warning(
                    "Authentication failed",
                    error=str(e),
                    privacy_filtered=True
                )
                # Continue without authentication - let endpoint handlers decide

        return await call_next(request)


# Exception Handlers - These are now handled in app.core.errors
# The functions below are kept for backward compatibility but should use
# the centralized error handling system from app.core.errors


# Exception handlers are now centralized in app.core.errors


def setup_middleware(app: FastAPI) -> None:
    """
    Configure all middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    logger.info("Setting up middleware")

    # Trusted Host Middleware (should be first) - only in production
    allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', None)
    if allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )

    # CORS Middleware
    cors_origins = getattr(settings, 'BACKEND_CORS_ORIGINS', ["http://localhost:3000", "http://localhost:8000"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in cors_origins] if isinstance(cors_origins, list) else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"]
    )

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Distributed tracing headers (should be early for request correlation)
    app.add_middleware(TracingHeadersMiddleware)

    # Request ID (should be early for logging)
    app.add_middleware(RequestIDMiddleware)

    # Timing (should be early to measure full request time)
    app.add_middleware(TimingMiddleware)

    # Authentication (should be after request ID for logging)
    app.add_middleware(AuthenticationMiddleware)

    logger.info("Middleware setup completed")


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Configure all exception handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    logger.info("Setting up exception handlers")

    # Use centralized error handling from app.core.errors
    from app.core.errors import register_exception_handlers
    register_exception_handlers(app)

    logger.info("Exception handlers setup completed")


# Utility functions for request context
def get_request_id(request: Request) -> Optional[str]:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", None)


def get_user_id(request: Request) -> Optional[str]:
    """Get authenticated user ID from request state."""
    return getattr(request.state, "user_id", None)


def get_user_email(request: Request) -> Optional[str]:
    """Get authenticated user email from request state."""
    return getattr(request.state, "user_email", None)


def is_authenticated(request: Request) -> bool:
    """Check if request is authenticated."""
    return getattr(request.state, "is_authenticated", False)


def get_trace_id(request: Request) -> Optional[str]:
    """Get trace ID from request state."""
    return getattr(request.state, "trace_id", None)


def get_span_id(request: Request) -> Optional[str]:
    """Get span ID from request state."""
    return getattr(request.state, "span_id", None)


def get_correlation_id(request: Request) -> Optional[str]:
    """Get correlation ID from request state."""
    return getattr(request.state, "correlation_id", None)


def get_tracing_context(request: Request) -> dict:
    """Get all tracing context from request state."""
    return {
        "trace_id": get_trace_id(request),
        "span_id": get_span_id(request),
        "parent_span_id": getattr(request.state, "parent_span_id", None),
        "correlation_id": get_correlation_id(request),
        "request_id": get_request_id(request)
    }


# Example usage and testing
if __name__ == "__main__":
    from fastapi import FastAPI

    # Create test app
    app = FastAPI()

    # Setup middleware and handlers
    setup_middleware(app)
    setup_exception_handlers(app)

    @app.get("/test")
    async def test_endpoint(request: Request):
        """Test endpoint for middleware testing."""
        return {
            "message": "Test successful",
            "request_id": get_request_id(request),
            "user_id": get_user_id(request),
            "authenticated": is_authenticated(request)
        }

    print("✅ Middleware and exception handlers configured")
    print("Test app created with middleware stack:")
    print("- Trusted Host Middleware")
    print("- CORS Middleware")
    print("- Security Headers Middleware")
    print("- Request ID Middleware")
    print("- Timing Middleware")
    print("- Authentication Middleware")
    print("- Exception Handlers: Validation, HTTP, General")

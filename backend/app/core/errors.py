"""
Global Exception Handlers and Error Response Models

This module provides comprehensive error handling for the FastAPI application,
including custom exceptions, standardized error responses, and global exception
handlers for consistent error management.
"""

import traceback
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# =============================================================================
# Error Categories and Types
# =============================================================================

class ErrorCategory(str, Enum):
    """Categories of errors that can occur in the application."""

    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    RATE_LIMIT = "rate_limit"
    INTERNAL_SERVER = "internal_server"
    CLIENT_ERROR = "client_error"


class ErrorCode(str, Enum):
    """Specific error codes for detailed error identification."""

    # Validation Errors (4000-4099)
    INVALID_INPUT = "INVALID_INPUT_4001"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD_4002"
    INVALID_FORMAT = "INVALID_FORMAT_4003"
    VALUE_OUT_OF_RANGE = "VALUE_OUT_OF_RANGE_4004"

    # Authentication Errors (4100-4199)
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS_4101"
    TOKEN_EXPIRED = "TOKEN_EXPIRED_4102"
    TOKEN_INVALID = "TOKEN_INVALID_4103"
    TOKEN_MISSING = "TOKEN_MISSING_4104"

    # Authorization Errors (4200-4299)
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS_4201"
    RESOURCE_ACCESS_DENIED = "RESOURCE_ACCESS_DENIED_4202"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED_4203"

    # Not Found Errors (4300-4399)
    USER_NOT_FOUND = "USER_NOT_FOUND_4301"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND_4302"
    ENDPOINT_NOT_FOUND = "ENDPOINT_NOT_FOUND_4303"

    # Business Logic Errors (4400-4499)
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE_4401"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION_4402"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION_4403"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED_4404"

    # External Service Errors (5000-5099)
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR_5001"
    EXTERNAL_SERVICE_TIMEOUT = "EXTERNAL_SERVICE_TIMEOUT_5002"
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE_5003"

    # Database Errors (5100-5199)
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR_5101"
    DATABASE_QUERY_ERROR = "DATABASE_QUERY_ERROR_5102"
    DATABASE_CONSTRAINT_VIOLATION = "DATABASE_CONSTRAINT_VIOLATION_5103"

    # Rate Limiting (4290-4299)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED_4291"

    # Internal Server Errors (5200+)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR_5200"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR_5201"
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR_5299"


# =============================================================================
# Error Response Models
# =============================================================================

class ErrorDetail(BaseModel):
    """Detailed information about a specific error."""

    field: Optional[str] = Field(None, description="Field name that caused the error")
    message: str = Field(..., description="Human-readable error message")
    code: Optional[str] = Field(None, description="Machine-readable error code")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional error context")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }
        json_schema_extra = {
            "example": {
                "field": "email",
                "message": "Invalid email format",
                "code": "INVALID_FORMAT_4003",
                "context": {"provided_value": "invalid-email"}
            }
        }


class ErrorResponse(BaseModel):
    """Standardized error response format for all API endpoints."""

    error: bool = Field(True, description="Always true for error responses")
    message: str = Field(..., description="High-level error description")
    code: str = Field(..., description="Machine-readable error code")
    category: ErrorCategory = Field(..., description="Error category")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error occurrence timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    path: Optional[str] = Field(None, description="API endpoint path where error occurred")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }
        json_schema_extra = {
            "example": {
                "error": True,
                "message": "Validation failed",
                "code": "INVALID_INPUT_4001",
                "category": "validation",
                "details": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "code": "INVALID_FORMAT_4003"
                    }
                ],
                "timestamp": "2024-01-01T12:00:00Z",
                "request_id": "req_123456789",
                "path": "/api/v1/users"
            }
        }


# =============================================================================
# Custom Exceptions
# =============================================================================

class BaseAppException(Exception):
    """Base exception class for all application-specific exceptions."""

    def __init__(
        self,
        message: str,
        code: ErrorCode,
        category: ErrorCategory,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[List[ErrorDetail]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.category = category
        self.status_code = status_code
        self.details = details or []
        self.context = context or {}

    def to_error_response(
        self,
        request_id: Optional[str] = None,
        path: Optional[str] = None
    ) -> ErrorResponse:
        """Convert exception to standardized error response."""
        return ErrorResponse(
            message=self.message,
            code=self.code.value,
            category=self.category,
            details=self.details,
            request_id=request_id,
            path=path
        )


class ValidationError(BaseAppException):
    """Exception for input validation errors."""

    def __init__(
        self,
        message: str = "Validation failed",
        code: ErrorCode = ErrorCode.INVALID_INPUT,
        details: Optional[List[ErrorDetail]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.VALIDATION,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class AuthenticationError(BaseAppException):
    """Exception for authentication failures."""

    def __init__(
        self,
        message: str = "Authentication failed",
        code: ErrorCode = ErrorCode.INVALID_CREDENTIALS
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.AUTHENTICATION,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(BaseAppException):
    """Exception for authorization failures."""

    def __init__(
        self,
        message: str = "Access denied",
        code: ErrorCode = ErrorCode.INSUFFICIENT_PERMISSIONS
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.AUTHORIZATION,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundError(BaseAppException):
    """Exception for resource not found errors."""

    def __init__(
        self,
        message: str = "Resource not found",
        code: ErrorCode = ErrorCode.RESOURCE_NOT_FOUND,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        context = {}
        if resource_type:
            context["resource_type"] = resource_type
        if resource_id:
            context["resource_id"] = resource_id

        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            context=context
        )


class BusinessLogicError(BaseAppException):
    """Exception for business logic violations."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.BUSINESS_RULE_VIOLATION,
        status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY
    ):
        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.BUSINESS_LOGIC,
            status_code=status_code
        )


class ExternalServiceError(BaseAppException):
    """Exception for external service errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.EXTERNAL_API_ERROR,
        service_name: Optional[str] = None
    ):
        context = {}
        if service_name:
            context["service_name"] = service_name

        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.EXTERNAL_SERVICE,
            status_code=status.HTTP_502_BAD_GATEWAY,
            context=context
        )


class DatabaseError(BaseAppException):
    """Exception for database-related errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.DATABASE_QUERY_ERROR,
        operation: Optional[str] = None
    ):
        context = {}
        if operation:
            context["operation"] = operation

        super().__init__(
            message=message,
            code=code,
            category=ErrorCategory.DATABASE,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            context=context
        )


class RateLimitError(BaseAppException):
    """Exception for rate limiting violations."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        context = {}
        if retry_after:
            context["retry_after"] = retry_after

        super().__init__(
            message=message,
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            category=ErrorCategory.RATE_LIMIT,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            context=context
        )


# =============================================================================
# Global Exception Handlers
# =============================================================================

def get_request_info(request: Request) -> tuple:
    """Extract request information for error logging."""
    request_id = getattr(request.state, 'request_id', None)
    path = request.url.path
    method = request.method
    return request_id, path, method


async def base_app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """Handle all custom application exceptions."""
    request_id, path, method = get_request_info(request)

    logger.error(
        "Application exception occurred",
        error_code=exc.code.value,
        error_category=exc.category.value,
        error_message=exc.message,
        status_code=exc.status_code,
        request_id=request_id,
        path=path,
        method=method,
        context=exc.context
    )

    error_response = exc.to_error_response(request_id=request_id, path=path)

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json'),
        headers={"X-Request-ID": request_id} if request_id else None
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPExceptions."""
    request_id, path, method = get_request_info(request)

    # Map HTTP status codes to error codes and categories
    if exc.status_code == 404:
        error_code = ErrorCode.ENDPOINT_NOT_FOUND
        category = ErrorCategory.NOT_FOUND
    elif exc.status_code == 401:
        error_code = ErrorCode.TOKEN_MISSING
        category = ErrorCategory.AUTHENTICATION
    elif exc.status_code == 403:
        error_code = ErrorCode.INSUFFICIENT_PERMISSIONS
        category = ErrorCategory.AUTHORIZATION
    elif exc.status_code == 429:
        error_code = ErrorCode.RATE_LIMIT_EXCEEDED
        category = ErrorCategory.RATE_LIMIT
    elif 400 <= exc.status_code < 500:
        error_code = ErrorCode.INVALID_INPUT
        category = ErrorCategory.CLIENT_ERROR
    else:
        error_code = ErrorCode.INTERNAL_SERVER_ERROR
        category = ErrorCategory.INTERNAL_SERVER

    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        request_id=request_id,
        path=path,
        method=method
    )

    error_response = ErrorResponse(
        message=str(exc.detail) if exc.detail else f"HTTP {exc.status_code}",
        code=error_code.value,
        category=category,
        request_id=request_id,
        path=path
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json'),
        headers={"X-Request-ID": request_id} if request_id else None
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI validation errors."""
    request_id, path, method = get_request_info(request)

    # Convert validation errors to our format
    details = []
    for error in exc.errors():
        field_path = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body'/'query' prefix
        detail = ErrorDetail(
            field=field_path if field_path else None,
            message=error["msg"],
            code=ErrorCode.INVALID_FORMAT.value,
            context={"type": error["type"], "input": error.get("input")}
        )
        details.append(detail)

    logger.warning(
        "Validation error occurred",
        validation_errors=exc.errors(),
        request_id=request_id,
        path=path,
        method=method
    )

    error_response = ErrorResponse(
        message="Request validation failed",
        code=ErrorCode.INVALID_INPUT.value,
        category=ErrorCategory.VALIDATION,
        details=details,
        request_id=request_id,
        path=path
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode='json'),
        headers={"X-Request-ID": request_id} if request_id else None
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    request_id, path, method = get_request_info(request)

    logger.error(
        "Unhandled exception occurred",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        traceback=traceback.format_exc(),
        request_id=request_id,
        path=path,
        method=method
    )

    error_response = ErrorResponse(
        message="An unexpected error occurred",
        code=ErrorCode.UNEXPECTED_ERROR.value,
        category=ErrorCategory.INTERNAL_SERVER,
        request_id=request_id,
        path=path
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json'),
        headers={"X-Request-ID": request_id} if request_id else None
    )


# =============================================================================
# Exception Handler Registration
# =============================================================================

def register_exception_handlers(app) -> None:
    """Register all exception handlers with the FastAPI app."""

    # Register custom exception handlers
    app.add_exception_handler(BaseAppException, base_app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered successfully")


# =============================================================================
# Utility Functions
# =============================================================================

def create_validation_error(field: str, message: str, value: Any = None) -> ValidationError:
    """Create a validation error with proper formatting."""
    detail = ErrorDetail(
        field=field,
        message=message,
        code=ErrorCode.INVALID_FORMAT.value,
        context={"provided_value": value} if value is not None else None
    )

    return ValidationError(
        message=f"Validation failed for field '{field}'",
        details=[detail]
    )


def create_not_found_error(resource_type: str, resource_id: str) -> NotFoundError:
    """Create a not found error with proper formatting."""
    return NotFoundError(
        message=f"{resource_type.title()} not found",
        code=ErrorCode.RESOURCE_NOT_FOUND,
        resource_type=resource_type,
        resource_id=resource_id
    )


def create_duplicate_error(resource_type: str, field: str) -> BusinessLogicError:
    """Create a duplicate resource error."""
    return BusinessLogicError(
        message=f"{resource_type.title()} with this {field} already exists",
        code=ErrorCode.DUPLICATE_RESOURCE,
        status_code=status.HTTP_409_CONFLICT
    )


if __name__ == "__main__":
    print("✅ Error handling system loaded")
    print("Features:")
    print("- BaseAppException: Custom exception base class")
    print("- ErrorResponse: Standardized error response format")
    print("- Exception handlers: Global handlers for all exception types")
    print("- Error codes: Comprehensive error code system")
    print("- Logging: Structured error logging with context")
    print("- Utilities: Helper functions for common error scenarios")

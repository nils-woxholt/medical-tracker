"""
Tests for Global Exception Handlers and Error Response Models

This module tests the error handling system including:
- Custom exception classes and hierarchy
- Error response model validation
- Exception handler behavior
- Error code mapping and categorization
- Structured error logging
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.core.errors import (
    AuthenticationError,
    AuthorizationError,
    # Exceptions
    BaseAppException,
    BusinessLogicError,
    DatabaseError,
    # Enums
    ErrorCategory,
    ErrorCode,
    # Models
    ErrorDetail,
    ErrorResponse,
    ExternalServiceError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    # Handlers
    base_app_exception_handler,
    create_duplicate_error,
    create_not_found_error,
    # Utilities
    create_validation_error,
    generic_exception_handler,
    get_request_info,
    http_exception_handler,
    register_exception_handlers,
    validation_exception_handler,
)


class TestErrorEnums:
    """Test error category and code enums."""

    def test_error_categories(self):
        """Test error category enum values."""
        assert ErrorCategory.VALIDATION == "validation"
        assert ErrorCategory.AUTHENTICATION == "authentication"
        assert ErrorCategory.AUTHORIZATION == "authorization"
        assert ErrorCategory.NOT_FOUND == "not_found"
        assert ErrorCategory.BUSINESS_LOGIC == "business_logic"
        assert ErrorCategory.EXTERNAL_SERVICE == "external_service"
        assert ErrorCategory.DATABASE == "database"
        assert ErrorCategory.RATE_LIMIT == "rate_limit"
        assert ErrorCategory.INTERNAL_SERVER == "internal_server"
        assert ErrorCategory.CLIENT_ERROR == "client_error"

    def test_error_codes_format(self):
        """Test error code format and values."""
        # Validation errors (4000-4099)
        assert ErrorCode.INVALID_INPUT == "INVALID_INPUT_4001"
        assert ErrorCode.MISSING_REQUIRED_FIELD == "MISSING_REQUIRED_FIELD_4002"

        # Authentication errors (4100-4199)
        assert ErrorCode.INVALID_CREDENTIALS == "INVALID_CREDENTIALS_4101"
        assert ErrorCode.TOKEN_EXPIRED == "TOKEN_EXPIRED_4102"

        # Authorization errors (4200-4299)
        assert ErrorCode.INSUFFICIENT_PERMISSIONS == "INSUFFICIENT_PERMISSIONS_4201"

        # Not found errors (4300-4399)
        assert ErrorCode.USER_NOT_FOUND == "USER_NOT_FOUND_4301"
        assert ErrorCode.RESOURCE_NOT_FOUND == "RESOURCE_NOT_FOUND_4302"

        # Business logic errors (4400-4499)
        assert ErrorCode.DUPLICATE_RESOURCE == "DUPLICATE_RESOURCE_4401"

        # External service errors (5000-5099)
        assert ErrorCode.EXTERNAL_API_ERROR == "EXTERNAL_API_ERROR_5001"

        # Database errors (5100-5199)
        assert ErrorCode.DATABASE_CONNECTION_ERROR == "DATABASE_CONNECTION_ERROR_5101"

        # Rate limiting
        assert ErrorCode.RATE_LIMIT_EXCEEDED == "RATE_LIMIT_EXCEEDED_4291"

        # Internal server errors
        assert ErrorCode.INTERNAL_SERVER_ERROR == "INTERNAL_SERVER_ERROR_5200"


class TestErrorModels:
    """Test error response models."""

    def test_error_detail_creation(self):
        """Test ErrorDetail model creation and validation."""
        detail = ErrorDetail(
            field="email",
            message="Invalid email format",
            code="INVALID_FORMAT_4003",
            context={"provided_value": "invalid-email"}
        )

        assert detail.field == "email"
        assert detail.message == "Invalid email format"
        assert detail.code == "INVALID_FORMAT_4003"
        assert detail.context["provided_value"] == "invalid-email"

    def test_error_detail_minimal(self):
        """Test ErrorDetail with minimal required fields."""
        detail = ErrorDetail(message="Something went wrong")

        assert detail.field is None
        assert detail.message == "Something went wrong"
        assert detail.code is None
        assert detail.context is None

    def test_error_response_creation(self):
        """Test ErrorResponse model creation."""
        details = [
            ErrorDetail(
                field="email",
                message="Invalid email format",
                code="INVALID_FORMAT_4003"
            )
        ]

        response = ErrorResponse(
            message="Validation failed",
            code="INVALID_INPUT_4001",
            category=ErrorCategory.VALIDATION,
            details=details,
            request_id="req_123",
            path="/api/users"
        )

        assert response.error is True
        assert response.message == "Validation failed"
        assert response.code == "INVALID_INPUT_4001"
        assert response.category == ErrorCategory.VALIDATION
        assert len(response.details) == 1
        assert response.request_id == "req_123"
        assert response.path == "/api/users"
        assert isinstance(response.timestamp, datetime)

    def test_error_response_serialization(self):
        """Test ErrorResponse JSON serialization."""
        response = ErrorResponse(
            message="Test error",
            code="TEST_CODE_4000",
            category=ErrorCategory.VALIDATION
        )

        data = response.model_dump()

        assert data["error"] is True
        assert data["message"] == "Test error"
        assert data["code"] == "TEST_CODE_4000"
        assert data["category"] == "validation"
        assert "timestamp" in data


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_base_app_exception(self):
        """Test BaseAppException creation and properties."""
        exc = BaseAppException(
            message="Test error",
            code=ErrorCode.INVALID_INPUT,
            category=ErrorCategory.VALIDATION,
            status_code=400
        )

        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.code == ErrorCode.INVALID_INPUT
        assert exc.category == ErrorCategory.VALIDATION
        assert exc.status_code == 400
        assert exc.details == []
        assert exc.context == {}

    def test_base_app_exception_to_error_response(self):
        """Test BaseAppException conversion to ErrorResponse."""
        exc = BaseAppException(
            message="Test error",
            code=ErrorCode.INVALID_INPUT,
            category=ErrorCategory.VALIDATION,
            status_code=400
        )

        response = exc.to_error_response(request_id="req_123", path="/test")

        assert response.message == "Test error"
        assert response.code == ErrorCode.INVALID_INPUT.value
        assert response.category == ErrorCategory.VALIDATION
        assert response.request_id == "req_123"
        assert response.path == "/test"

    def test_validation_error(self):
        """Test ValidationError exception."""
        details = [ErrorDetail(field="email", message="Invalid format")]
        exc = ValidationError(message="Validation failed", details=details)

        assert exc.message == "Validation failed"
        assert exc.code == ErrorCode.INVALID_INPUT
        assert exc.category == ErrorCategory.VALIDATION
        assert exc.status_code == 400
        assert len(exc.details) == 1

    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        exc = AuthenticationError(message="Invalid token")

        assert exc.message == "Invalid token"
        assert exc.code == ErrorCode.INVALID_CREDENTIALS
        assert exc.category == ErrorCategory.AUTHENTICATION
        assert exc.status_code == 401

    def test_authorization_error(self):
        """Test AuthorizationError exception."""
        exc = AuthorizationError(message="Access denied")

        assert exc.message == "Access denied"
        assert exc.code == ErrorCode.INSUFFICIENT_PERMISSIONS
        assert exc.category == ErrorCategory.AUTHORIZATION
        assert exc.status_code == 403

    def test_not_found_error(self):
        """Test NotFoundError exception."""
        exc = NotFoundError(
            message="User not found",
            code=ErrorCode.USER_NOT_FOUND,
            resource_type="user",
            resource_id="123"
        )

        assert exc.message == "User not found"
        assert exc.code == ErrorCode.USER_NOT_FOUND
        assert exc.category == ErrorCategory.NOT_FOUND
        assert exc.status_code == 404
        assert exc.context["resource_type"] == "user"
        assert exc.context["resource_id"] == "123"

    def test_business_logic_error(self):
        """Test BusinessLogicError exception."""
        exc = BusinessLogicError(
            message="Operation not allowed",
            code=ErrorCode.BUSINESS_RULE_VIOLATION
        )

        assert exc.message == "Operation not allowed"
        assert exc.code == ErrorCode.BUSINESS_RULE_VIOLATION
        assert exc.category == ErrorCategory.BUSINESS_LOGIC
        assert exc.status_code == 422

    def test_external_service_error(self):
        """Test ExternalServiceError exception."""
        exc = ExternalServiceError(
            message="Payment service unavailable",
            service_name="stripe"
        )

        assert exc.message == "Payment service unavailable"
        assert exc.code == ErrorCode.EXTERNAL_API_ERROR
        assert exc.category == ErrorCategory.EXTERNAL_SERVICE
        assert exc.status_code == 502
        assert exc.context["service_name"] == "stripe"

    def test_database_error(self):
        """Test DatabaseError exception."""
        exc = DatabaseError(
            message="Query failed",
            operation="insert_user"
        )

        assert exc.message == "Query failed"
        assert exc.code == ErrorCode.DATABASE_QUERY_ERROR
        assert exc.category == ErrorCategory.DATABASE
        assert exc.status_code == 500
        assert exc.context["operation"] == "insert_user"

    def test_rate_limit_error(self):
        """Test RateLimitError exception."""
        exc = RateLimitError(retry_after=60)

        assert exc.message == "Rate limit exceeded"
        assert exc.code == ErrorCode.RATE_LIMIT_EXCEEDED
        assert exc.category == ErrorCategory.RATE_LIMIT
        assert exc.status_code == 429
        assert exc.context["retry_after"] == 60


class TestExceptionHandlers:
    """Test exception handler functions."""

    @pytest.fixture
    def mock_request(self):
        """Create mock request for testing."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "POST"
        request.state = Mock()
        request.state.request_id = "req_123"
        return request

    @pytest.mark.asyncio
    async def test_base_app_exception_handler(self, mock_request):
        """Test BaseAppException handler."""
        exc = ValidationError(message="Test validation error")

        with patch('app.core.errors.logger') as mock_logger:
            response = await base_app_exception_handler(mock_request, exc)

            assert isinstance(response, JSONResponse)
            assert response.status_code == 400

            # Check logging
            mock_logger.error.assert_called_once()
            log_call = mock_logger.error.call_args
            assert log_call[1]["error_code"] == ErrorCode.INVALID_INPUT.value
            assert log_call[1]["error_category"] == ErrorCategory.VALIDATION.value

            # Check response content
            content = json.loads(response.body)
            assert content["error"] is True
            assert content["message"] == "Test validation error"
            assert content["code"] == ErrorCode.INVALID_INPUT.value
            assert content["category"] == "validation"
            assert content["request_id"] == "req_123"
            assert content["path"] == "/api/test"

    @pytest.mark.asyncio
    async def test_http_exception_handler_404(self, mock_request):
        """Test HTTPException handler for 404 errors."""
        exc = HTTPException(status_code=404, detail="Endpoint not found")

        with patch('app.core.errors.logger') as mock_logger:
            response = await http_exception_handler(mock_request, exc)

            assert isinstance(response, JSONResponse)
            assert response.status_code == 404

            # Check logging
            mock_logger.warning.assert_called_once()

            # Check response content
            content = json.loads(response.body)
            assert content["error"] is True
            assert content["message"] == "Endpoint not found"
            assert content["code"] == ErrorCode.ENDPOINT_NOT_FOUND.value
            assert content["category"] == "not_found"

    @pytest.mark.asyncio
    async def test_http_exception_handler_401(self, mock_request):
        """Test HTTPException handler for 401 errors."""
        exc = HTTPException(status_code=401, detail="Unauthorized")

        response = await http_exception_handler(mock_request, exc)
        content = json.loads(response.body)

        assert response.status_code == 401
        assert content["code"] == ErrorCode.TOKEN_MISSING.value
        assert content["category"] == "authentication"

    @pytest.mark.asyncio
    async def test_validation_exception_handler(self, mock_request):
        """Test RequestValidationError handler."""
        # Mock validation error
        validation_errors = [
            {
                "loc": ("body", "email"),
                "msg": "field required",
                "type": "value_error.missing",
                "input": {}
            },
            {
                "loc": ("body", "age"),
                "msg": "ensure this value is greater than 0",
                "type": "value_error.number.not_gt",
                "input": -5
            }
        ]

        exc = RequestValidationError(validation_errors)

        with patch('app.core.errors.logger') as mock_logger:
            response = await validation_exception_handler(mock_request, exc)

            assert isinstance(response, JSONResponse)
            assert response.status_code == 422

            # Check logging
            mock_logger.warning.assert_called_once()

            # Check response content
            content = json.loads(response.body)
            assert content["error"] is True
            assert content["message"] == "Request validation failed"
            assert content["code"] == ErrorCode.INVALID_INPUT.value
            assert content["category"] == "validation"
            assert len(content["details"]) == 2

            # Check details
            email_detail = next(d for d in content["details"] if d["field"] == "email")
            assert email_detail["message"] == "field required"

            age_detail = next(d for d in content["details"] if d["field"] == "age")
            assert age_detail["message"] == "ensure this value is greater than 0"

    @pytest.mark.asyncio
    async def test_generic_exception_handler(self, mock_request):
        """Test generic Exception handler."""
        exc = Exception("Unexpected error occurred")

        with patch('app.core.errors.logger') as mock_logger:
            response = await generic_exception_handler(mock_request, exc)

            assert isinstance(response, JSONResponse)
            assert response.status_code == 500

            # Check logging
            mock_logger.error.assert_called_once()
            log_call = mock_logger.error.call_args
            assert log_call[1]["exception_type"] == "Exception"
            assert log_call[1]["exception_message"] == "Unexpected error occurred"

            # Check response content
            content = json.loads(response.body)
            assert content["error"] is True
            assert content["message"] == "An unexpected error occurred"
            assert content["code"] == ErrorCode.UNEXPECTED_ERROR.value
            assert content["category"] == "internal_server"

    def test_get_request_info(self, mock_request):
        """Test request information extraction."""
        request_id, path, method = get_request_info(mock_request)

        assert request_id == "req_123"
        assert path == "/api/test"
        assert method == "POST"

    def test_get_request_info_no_request_id(self):
        """Test request info extraction without request ID."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.state = Mock()
        # Remove request_id attribute to simulate not having one
        del request.state.request_id

        request_id, path, method = get_request_info(request)

        assert request_id is None
        assert path == "/api/test"
        assert method == "GET"


class TestExceptionHandlerRegistration:
    """Test exception handler registration."""

    def test_register_exception_handlers(self):
        """Test exception handler registration with FastAPI app."""
        app = Mock()

        with patch('app.core.errors.logger') as mock_logger:
            register_exception_handlers(app)

            # Verify handlers are registered
            assert app.add_exception_handler.call_count == 4

            # Verify specific handlers
            calls = app.add_exception_handler.call_args_list
            exception_types = [call[0][0] for call in calls]

            assert BaseAppException in exception_types
            assert HTTPException in exception_types
            assert RequestValidationError in exception_types
            assert Exception in exception_types

            # Verify logging
            mock_logger.info.assert_called_once_with("Exception handlers registered successfully")


class TestUtilityFunctions:
    """Test utility functions for common error scenarios."""

    def test_create_validation_error(self):
        """Test validation error creation utility."""
        error = create_validation_error("email", "Invalid format", "invalid-email")

        assert isinstance(error, ValidationError)
        assert error.message == "Validation failed for field 'email'"
        assert len(error.details) == 1

        detail = error.details[0]
        assert detail.field == "email"
        assert detail.message == "Invalid format"
        assert detail.code == ErrorCode.INVALID_FORMAT.value
        assert detail.context["provided_value"] == "invalid-email"

    def test_create_not_found_error(self):
        """Test not found error creation utility."""
        error = create_not_found_error("user", "123")

        assert isinstance(error, NotFoundError)
        assert error.message == "User not found"
        assert error.code == ErrorCode.RESOURCE_NOT_FOUND
        assert error.context["resource_type"] == "user"
        assert error.context["resource_id"] == "123"

    def test_create_duplicate_error(self):
        """Test duplicate resource error creation utility."""
        error = create_duplicate_error("user", "email")

        assert isinstance(error, BusinessLogicError)
        assert error.message == "User with this email already exists"
        assert error.code == ErrorCode.DUPLICATE_RESOURCE
        assert error.status_code == 409


class TestIntegrationWithFastAPI:
    """Test error handling integration with FastAPI."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with error handlers for testing."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/validation-error")
        def validation_error_endpoint():
            raise ValidationError("Test validation error")

        @app.get("/not-found")
        def not_found_endpoint():
            raise NotFoundError("Resource not found")

        @app.get("/business-error")
        def business_error_endpoint():
            raise BusinessLogicError("Business rule violation")

        @app.get("/http-404")
        def http_404_endpoint():
            raise HTTPException(status_code=404, detail="Not found")

        @app.get("/unexpected")
        def unexpected_error_endpoint():
            raise ValueError("Unexpected error")

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_validation_error_response(self, client):
        """Test validation error response format."""
        response = client.get("/validation-error")

        assert response.status_code == 400
        data = response.json()

        assert data["error"] is True
        assert data["message"] == "Test validation error"
        assert data["code"] == ErrorCode.INVALID_INPUT.value
        assert data["category"] == "validation"

    def test_not_found_error_response(self, client):
        """Test not found error response format."""
        response = client.get("/not-found")

        assert response.status_code == 404
        data = response.json()

        assert data["error"] is True
        assert data["message"] == "Resource not found"
        assert data["code"] == ErrorCode.RESOURCE_NOT_FOUND.value
        assert data["category"] == "not_found"

    def test_business_error_response(self, client):
        """Test business logic error response format."""
        response = client.get("/business-error")

        assert response.status_code == 422
        data = response.json()

        assert data["error"] is True
        assert data["message"] == "Business rule violation"
        assert data["code"] == ErrorCode.BUSINESS_RULE_VIOLATION.value
        assert data["category"] == "business_logic"

    def test_http_404_response(self, client):
        """Test HTTP 404 error response format."""
        response = client.get("/http-404")

        assert response.status_code == 404
        data = response.json()

        assert data["error"] is True
        assert data["message"] == "Not found"
        assert data["code"] == ErrorCode.ENDPOINT_NOT_FOUND.value
        assert data["category"] == "not_found"

    def test_unexpected_error_response(self, client):
        """Test unexpected error response format."""
        # With TestClient, unhandled exceptions are raised instead of returning 500 responses
        # This is expected behavior for testing - the handler is still called for logging
        # but the exception propagates up for better test debugging
        with pytest.raises(ValueError, match="Unexpected error"):
            client.get("/unexpected")


if __name__ == "__main__":
    print("✅ Error handling tests loaded")
    print("Test classes:")
    print("- TestErrorEnums: Error categories and codes")
    print("- TestErrorModels: Error response models")
    print("- TestCustomExceptions: Custom exception classes")
    print("- TestExceptionHandlers: Exception handler functions")
    print("- TestExceptionHandlerRegistration: Handler registration")
    print("- TestUtilityFunctions: Helper utilities")
    print("- TestIntegrationWithFastAPI: FastAPI integration testing")

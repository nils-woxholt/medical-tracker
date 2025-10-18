"""
Test Dependency Injection Utilities and Patterns

This module tests the dependency injection system for FastAPI,
including database sessions, authentication, configuration, and service layer
components.
"""

from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from app.core.auth import create_access_token
from app.core.config import get_settings
from app.core.dependencies import (
    Context,
    CurrentUserId,
    OptionalUserId,
    Pagination,
    RequestContext,
    ServiceRegistry,
    SyncDatabase,
    create_custom_dependency,
    get_cached_settings,
    get_client_ip,
    get_current_user_id,
    get_debug_mode,
    get_environment_name,
    get_optional_auth_token,
    get_optional_user_id,
    get_pagination_params,
    get_request_id,
    get_required_auth_token,
    get_service_registry,
    get_user_agent,
    require_permissions,
)


class TestBasicDependencies:
    """Test basic request and utility dependencies."""

    def test_get_request_id(self):
        """Test extracting request ID from request state."""
        # Mock request with request_id in state
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.request_id = "test-request-123"

        request_id = get_request_id(request)
        assert request_id == "test-request-123"

    def test_get_request_id_missing(self):
        """Test handling missing request ID."""
        request = Mock(spec=Request)
        request.state = Mock(spec=[])  # No request_id attribute

        request_id = get_request_id(request)
        assert request_id == "unknown"

    def test_get_user_agent(self):
        """Test extracting User-Agent header."""
        request = Mock(spec=Request)
        request.headers = {"user-agent": "TestClient/1.0"}

        user_agent = get_user_agent(request)
        assert user_agent == "TestClient/1.0"

    def test_get_user_agent_missing(self):
        """Test handling missing User-Agent header."""
        request = Mock(spec=Request)
        request.headers = {}

        user_agent = get_user_agent(request)
        assert user_agent is None

    def test_get_client_ip_direct(self):
        """Test extracting direct client IP."""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.100"

        client_ip = get_client_ip(request)
        assert client_ip == "192.168.1.100"

    def test_get_client_ip_forwarded(self):
        """Test extracting IP from X-Forwarded-For header."""
        request = Mock(spec=Request)
        request.headers = {"x-forwarded-for": "203.0.113.1, 198.51.100.1"}
        request.client = Mock()
        request.client.host = "192.168.1.1"

        client_ip = get_client_ip(request)
        assert client_ip == "203.0.113.1"  # First IP in chain

    def test_get_client_ip_real_ip(self):
        """Test extracting IP from X-Real-IP header."""
        request = Mock(spec=Request)
        request.headers = {"x-real-ip": "203.0.113.2"}
        request.client = Mock()
        request.client.host = "192.168.1.1"

        client_ip = get_client_ip(request)
        assert client_ip == "203.0.113.2"

    def test_get_client_ip_no_client(self):
        """Test handling missing client information."""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = None

        client_ip = get_client_ip(request)
        assert client_ip == "unknown"


class TestConfigurationDependencies:
    """Test configuration-related dependencies."""

    def test_get_cached_settings(self):
        """Test getting cached application settings."""
        settings = get_cached_settings()

        assert settings is not None
        assert hasattr(settings, 'PROJECT_NAME')
        assert hasattr(settings, 'ENVIRONMENT')

    def test_get_environment_name(self):
        """Test getting environment name."""
        env = get_environment_name()

        assert isinstance(env, str)
        assert env in ["development", "testing", "production"]

    def test_get_debug_mode(self):
        """Test getting debug mode status."""
        debug = get_debug_mode()

        assert isinstance(debug, bool)


class TestAuthenticationDependencies:
    """Test authentication-related dependencies."""

    def test_get_optional_auth_token_present(self):
        """Test extracting optional auth token when present."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="test-token-123"
        )

        token = get_optional_auth_token(credentials)
        assert token == "test-token-123"

    def test_get_optional_auth_token_missing(self):
        """Test extracting optional auth token when missing."""
        token = get_optional_auth_token(None)
        assert token is None

    def test_get_optional_auth_token_wrong_scheme(self):
        """Test extracting optional auth token with wrong scheme."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Basic",
            credentials="dGVzdDp0ZXN0"
        )

        token = get_optional_auth_token(credentials)
        assert token is None

    def test_get_required_auth_token_present(self):
        """Test extracting required auth token when present."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="test-token-456"
        )

        token = get_required_auth_token(credentials)
        assert token == "test-token-456"

    def test_get_required_auth_token_missing(self):
        """Test extracting required auth token when missing."""
        with pytest.raises(HTTPException) as exc_info:
            get_required_auth_token(None)

        assert exc_info.value.status_code == 401
        assert "Bearer token required" in exc_info.value.detail

    def test_get_required_auth_token_wrong_scheme(self):
        """Test extracting required auth token with wrong scheme."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Basic",
            credentials="dGVzdDp0ZXN0"
        )

        with pytest.raises(HTTPException) as exc_info:
            get_required_auth_token(credentials)

        assert exc_info.value.status_code == 401

    def test_get_current_user_id_valid(self):
        """Test getting current user ID with valid token."""
        # Create a valid token
        token_data = {"sub": "test@example.com", "user_id": "user123"}
        token = create_access_token(token_data)

        user_id = get_current_user_id(token)
        assert user_id == "user123"

    def test_get_current_user_id_invalid(self):
        """Test getting current user ID with invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id("invalid-token")

        assert exc_info.value.status_code == 401
        assert "Invalid authentication token" in exc_info.value.detail

    def test_get_current_user_id_no_user_id(self):
        """Test getting current user ID when token has no user_id."""
        # Create token without user_id
        token_data = {"sub": "test@example.com"}
        token = create_access_token(token_data)

        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(token)

        assert exc_info.value.status_code == 401
        assert "does not contain user ID" in exc_info.value.detail

    def test_get_optional_user_id_valid(self):
        """Test getting optional user ID with valid token."""
        token_data = {"sub": "test@example.com", "user_id": "user456"}
        token = create_access_token(token_data)

        user_id = get_optional_user_id(token)
        assert user_id == "user456"

    def test_get_optional_user_id_invalid(self):
        """Test getting optional user ID with invalid token."""
        user_id = get_optional_user_id("invalid-token")
        assert user_id is None

    def test_get_optional_user_id_none(self):
        """Test getting optional user ID with no token."""
        user_id = get_optional_user_id(None)
        assert user_id is None


class TestPaginationDependencies:
    """Test pagination-related dependencies."""

    def test_get_pagination_params_default(self):
        """Test getting pagination parameters with defaults."""
        params = get_pagination_params()

        assert params.page == 1
        assert params.per_page == 20
        assert params.offset == 0

    def test_get_pagination_params_custom(self):
        """Test getting pagination parameters with custom values."""
        params = get_pagination_params(page=3, per_page=10)

        assert params.page == 3
        assert params.per_page == 10
        assert params.offset == 20  # (3-1) * 10

    def test_get_pagination_params_invalid_page(self):
        """Test validation of invalid page number."""
        with pytest.raises(HTTPException) as exc_info:
            get_pagination_params(page=0)

        assert exc_info.value.status_code == 400
        assert "Page number must be 1 or greater" in exc_info.value.detail

    def test_get_pagination_params_invalid_per_page(self):
        """Test validation of invalid per_page."""
        with pytest.raises(HTTPException) as exc_info:
            get_pagination_params(per_page=0)

        assert exc_info.value.status_code == 400
        assert "Items per page must be 1 or greater" in exc_info.value.detail

    def test_get_pagination_params_exceeds_max(self):
        """Test validation of per_page exceeding maximum."""
        with pytest.raises(HTTPException) as exc_info:
            get_pagination_params(per_page=200, max_per_page=100)

        assert exc_info.value.status_code == 400
        assert "cannot exceed 100" in exc_info.value.detail


class TestServiceRegistry:
    """Test service registry functionality."""

    def test_service_registry_register_get(self):
        """Test registering and getting services."""
        registry = ServiceRegistry()

        # Mock service
        mock_service = Mock()
        mock_service.name = "test_service"

        # Register service
        registry.register(str, mock_service)

        # Retrieve service
        retrieved = registry.get(str)
        assert retrieved == mock_service
        assert retrieved.name == "test_service"

    def test_service_registry_get_missing(self):
        """Test getting missing service."""
        registry = ServiceRegistry()

        service = registry.get(int)
        assert service is None

    def test_service_registry_clear(self):
        """Test clearing registry."""
        registry = ServiceRegistry()

        # Register service
        registry.register(str, "test")
        assert registry.get(str) == "test"

        # Clear registry
        registry.clear()
        assert registry.get(str) is None

    def test_get_service_registry_global(self):
        """Test getting global service registry."""
        registry1 = get_service_registry()
        registry2 = get_service_registry()

        # Should be the same instance
        assert registry1 is registry2


class TestRequestContext:
    """Test request context composite dependency."""

    def test_request_context_creation(self):
        """Test creating request context."""
        context = RequestContext(
            request_id="req-123",
            user_id="user-456",
            client_ip="192.168.1.1",
            user_agent="TestClient/1.0",
            settings=get_settings()
        )

        assert context.request_id == "req-123"
        assert context.user_id == "user-456"
        assert context.client_ip == "192.168.1.1"
        assert context.user_agent == "TestClient/1.0"
        assert context.is_authenticated is True

    def test_request_context_anonymous(self):
        """Test request context for anonymous user."""
        context = RequestContext(
            request_id="req-789",
            user_id=None,
            client_ip="203.0.113.1",
            user_agent=None,
            settings=get_settings()
        )

        assert context.request_id == "req-789"
        assert context.user_id is None
        assert context.is_authenticated is False

    def test_request_context_to_dict(self):
        """Test converting request context to dictionary."""
        context = RequestContext(
            request_id="req-abc",
            user_id="user-def",
            client_ip="198.51.100.1",
            user_agent="Bot/1.0",
            settings=get_settings()
        )

        context_dict = context.to_dict()

        expected = {
            "request_id": "req-abc",
            "user_id": "user-def",
            "client_ip": "198.51.100.1",
            "user_agent": "Bot/1.0",
            "is_authenticated": True
        }

        assert context_dict == expected


class TestPermissionDependencies:
    """Test permission-related dependencies."""

    def test_require_permissions(self):
        """Test permission requirement decorator."""
        # Create permission dependency
        require_admin = require_permissions("admin", "write")

        # Mock valid user ID
        token_data = {"sub": "admin@example.com", "user_id": "admin123"}
        token = create_access_token(token_data)

        # Should return user ID (placeholder implementation)
        user_id = require_admin(token)
        assert user_id == "admin123"


class TestCustomDependencies:
    """Test custom dependency creation."""

    def test_create_custom_dependency(self):
        """Test creating custom dependency."""
        def get_test_value():
            return "custom_value"

        CustomDep = create_custom_dependency(get_test_value)

        # The annotation should work (this is more of a type check)
        assert CustomDep is not None


@pytest.mark.integration
class TestDependencyIntegration:
    """Test dependency integration with FastAPI."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app with dependencies."""
        app = FastAPI()

        @app.get("/test/sync-db")
        def test_sync_db(db: SyncDatabase):
            return {"db_type": type(db).__name__}

        @app.get("/test/auth-required")
        def test_auth_required(user_id: CurrentUserId):
            return {"user_id": user_id}

        @app.get("/test/auth-optional")
        def test_auth_optional(user_id: OptionalUserId):
            return {"user_id": user_id}

        @app.get("/test/pagination")
        def test_pagination(pagination: Pagination):
            return {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "offset": pagination.offset
            }

        @app.get("/test/context")
        def test_context(ctx: Context):
            return ctx.to_dict()

        return app

    def test_pagination_integration(self, app):
        """Test pagination dependency in FastAPI endpoint."""
        client = TestClient(app)

        # Test default pagination
        response = client.get("/test/pagination")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 20
        assert data["offset"] == 0

        # Test custom pagination
        response = client.get("/test/pagination?page=3&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 3
        assert data["per_page"] == 10
        assert data["offset"] == 20

        # Test invalid pagination
        response = client.get("/test/pagination?page=0")
        assert response.status_code == 400

    def test_auth_optional_integration(self, app):
        """Test optional auth dependency in FastAPI endpoint."""
        client = TestClient(app)

        # Test without token
        response = client.get("/test/auth-optional")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] is None

        # Test with valid token
        token_data = {"sub": "test@example.com", "user_id": "test123"}
        token = create_access_token(token_data)

        response = client.get(
            "/test/auth-optional",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test123"

    def test_auth_required_integration(self, app):
        """Test required auth dependency in FastAPI endpoint."""
        client = TestClient(app)

        # Test without token
        response = client.get("/test/auth-required")
        assert response.status_code == 401

        # Test with invalid token
        response = client.get(
            "/test/auth-required",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

        # Test with valid token
        token_data = {"sub": "test@example.com", "user_id": "test456"}
        token = create_access_token(token_data)

        response = client.get(
            "/test/auth-required",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test456"


if __name__ == "__main__":
    print("✅ Dependency injection tests module loaded")
    print("Test classes:")
    print("- TestBasicDependencies: Request ID, IP, User-Agent extraction")
    print("- TestConfigurationDependencies: Settings and environment")
    print("- TestAuthenticationDependencies: JWT token handling")
    print("- TestPaginationDependencies: Pagination parameter validation")
    print("- TestServiceRegistry: Service registration and retrieval")
    print("- TestRequestContext: Composite request context")
    print("- TestPermissionDependencies: Permission checking")
    print("- TestCustomDependencies: Custom dependency creation")
    print("- TestDependencyIntegration: FastAPI endpoint integration")

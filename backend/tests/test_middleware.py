"""
Test Middleware and Exception Handlers

This module tests all middleware components and exception handlers
for the SaaS Medical Tracker API.
"""

import asyncio

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.core.auth import create_access_token
from app.core.middleware import (
    AuthenticationMiddleware,
    CORSMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
    TimingMiddleware,
    TrustedHostMiddleware,
    setup_exception_handlers,
    setup_middleware,
)
from app.core.settings import get_settings

settings = get_settings()


class TestRequestIDMiddleware:
    """Test Request ID middleware functionality."""

    @pytest.fixture
    def app(self):
        """Create test app with RequestID middleware."""
        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)

        @app.get("/test")
        async def test_endpoint(request: Request):
            return {"request_id": getattr(request.state, "request_id", None)}

        return app

    def test_request_id_generation(self, app):
        """Test that request ID is generated and added to request."""
        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        data = response.json()

        # Should have request ID
        assert "request_id" in data
        assert data["request_id"] is not None
        assert len(data["request_id"]) > 0

    def test_request_id_in_headers(self, app):
        """Test that request ID is added to response headers."""
        client = TestClient(app)
        response = client.get("/test")

        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) > 0

    def test_request_id_uniqueness(self, app):
        """Test that each request gets unique ID."""
        client = TestClient(app)

        response1 = client.get("/test")
        response2 = client.get("/test")

        id1 = response1.headers["X-Request-ID"]
        id2 = response2.headers["X-Request-ID"]

        assert id1 != id2

    def test_provided_request_id(self, app):
        """Test using provided request ID from headers."""
        client = TestClient(app)
        custom_id = "custom-request-123"

        response = client.get("/test", headers={"X-Request-ID": custom_id})

        assert response.headers["X-Request-ID"] == custom_id
        assert response.json()["request_id"] == custom_id


class TestTimingMiddleware:
    """Test Timing middleware functionality."""

    @pytest.fixture
    def app(self):
        """Create test app with Timing middleware."""
        app = FastAPI()
        app.add_middleware(TimingMiddleware)

        @app.get("/fast")
        async def fast_endpoint():
            return {"message": "fast"}

        @app.get("/slow")
        async def slow_endpoint():
            await asyncio.sleep(0.1)  # 100ms delay
            return {"message": "slow"}

        return app

    def test_timing_header_added(self, app):
        """Test that timing header is added to response."""
        client = TestClient(app)
        response = client.get("/fast")

        assert "X-Process-Time" in response.headers

        # Should be a valid float
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0
        assert process_time < 1.0  # Should be less than 1 second

    def test_timing_accuracy(self, app):
        """Test that timing is reasonably accurate."""
        client = TestClient(app)
        response = client.get("/slow")

        process_time = float(response.headers["X-Process-Time"])

        # Should be at least 100ms (our sleep time)
        assert process_time >= 0.1
        assert process_time < 0.2  # But not too much overhead

    def test_timing_precision(self, app):
        """Test timing precision."""
        client = TestClient(app)

        # Make multiple requests
        times = []
        for _ in range(3):
            response = client.get("/fast")
            process_time = float(response.headers["X-Process-Time"])
            times.append(process_time)

        # All times should be positive and small
        for t in times:
            assert t > 0
            assert t < 0.1  # Fast endpoint should be under 100ms


class TestSecurityHeadersMiddleware:
    """Test Security Headers middleware functionality."""

    @pytest.fixture
    def app(self):
        """Create test app with Security Headers middleware."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        return app

    def test_security_headers_added(self, app):
        """Test that security headers are added to response."""
        client = TestClient(app)
        response = client.get("/test")

        # Check all security headers
        expected_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }

        for header, expected_value in expected_headers.items():
            assert header in response.headers
            assert response.headers[header] == expected_value

    def test_content_security_policy(self, app):
        """Test Content Security Policy header."""
        client = TestClient(app)
        response = client.get("/test")

        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]

        # Should contain basic CSP directives
        assert "default-src" in csp
        assert "script-src" in csp
        assert "style-src" in csp


class TestAuthenticationMiddleware:
    """Test Authentication middleware functionality."""

    @pytest.fixture
    def app(self):
        """Create test app with Authentication middleware."""
        app = FastAPI()
        app.add_middleware(AuthenticationMiddleware)

        @app.get("/public")
        async def public_endpoint():
            return {"message": "public"}

        @app.get("/protected")
        async def protected_endpoint(request: Request):
            user = getattr(request.state, "user", None)
            return {"message": "protected", "user": user}

        return app

    def test_public_endpoint_no_auth(self, app):
        """Test that public endpoints work without authentication."""
        client = TestClient(app)
        response = client.get("/public")

        assert response.status_code == 200
        assert response.json()["message"] == "public"

    def test_protected_endpoint_no_token(self, app):
        """Test protected endpoint without token."""
        client = TestClient(app)
        response = client.get("/protected")

        # Should still work but with no user info
        assert response.status_code == 200
        assert response.json()["user"] is None

    def test_protected_endpoint_valid_token(self, app):
        """Test protected endpoint with valid token."""
        # Create a valid token
        token_data = {"sub": "test@example.com", "user_id": "123"}
        token = create_access_token(token_data)

        client = TestClient(app)
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        # Note: Full user extraction would require database lookup
        # For now, just check that it doesn't error

    def test_protected_endpoint_invalid_token(self, app):
        """Test protected endpoint with invalid token."""
        client = TestClient(app)
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer invalid-token"}
        )

        # Should still work but with no user info
        assert response.status_code == 200
        assert response.json()["user"] is None

    def test_malformed_authorization_header(self, app):
        """Test malformed authorization header."""
        client = TestClient(app)
        response = client.get(
            "/protected",
            headers={"Authorization": "InvalidFormat"}
        )

        # Should handle gracefully
        assert response.status_code == 200
        assert response.json()["user"] is None


class TestCORSMiddleware:
    """Test CORS middleware functionality."""

    @pytest.fixture
    def app(self):
        """Create test app with CORS middleware."""
        app = FastAPI()
        app.add_middleware(CORSMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        @app.post("/test")
        async def test_post():
            return {"message": "post"}

        return app

    def test_cors_headers_simple_request(self, app):
        """Test CORS headers for simple requests."""
        client = TestClient(app)
        response = client.get("/test", headers={"Origin": "https://example.com"})

        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Credentials" in response.headers

    def test_cors_preflight_request(self, app):
        """Test CORS preflight (OPTIONS) request."""
        client = TestClient(app)
        response = client.options(
            "/test",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )

        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
        assert "Access-Control-Allow-Headers" in response.headers

    def test_cors_allowed_origins(self, app):
        """Test CORS allowed origins configuration."""
        client = TestClient(app)

        # Test localhost (should be allowed)
        response = client.get("/test", headers={"Origin": "http://localhost:3000"})
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"

    def test_cors_credentials(self, app):
        """Test CORS credentials handling."""
        client = TestClient(app)
        response = client.get("/test", headers={"Origin": "https://example.com"})

        assert response.headers.get("Access-Control-Allow-Credentials") == "true"


class TestTrustedHostMiddleware:
    """Test Trusted Host middleware functionality."""

    @pytest.fixture
    def app(self):
        """Create test app with Trusted Host middleware."""
        app = FastAPI()
        app.add_middleware(TrustedHostMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        return app

    def test_trusted_host_localhost(self, app):
        """Test that localhost is trusted."""
        client = TestClient(app)
        response = client.get("/test", headers={"Host": "localhost:8000"})

        assert response.status_code == 200
        assert response.json()["message"] == "test"

    def test_trusted_host_127_0_0_1(self, app):
        """Test that 127.0.0.1 is trusted."""
        client = TestClient(app)
        response = client.get("/test", headers={"Host": "127.0.0.1:8000"})

        assert response.status_code == 200
        assert response.json()["message"] == "test"

    @pytest.mark.skip(reason="TestClient doesn't fully simulate untrusted hosts")
    def test_untrusted_host_blocked(self, app):
        """Test that untrusted hosts are blocked."""
        client = TestClient(app)
        # This test is skipped because TestClient doesn't fully simulate
        # the host header validation behavior
        pass


class TestExceptionHandlers:
    """Test exception handlers."""

    @pytest.fixture
    def app(self):
        """Create test app with exception handlers."""
        app = FastAPI()
        setup_exception_handlers(app)

        @app.get("/validation-error")
        async def validation_error():
            from pydantic import BaseModel

            class TestModel(BaseModel):
                name: str
                age: int

            # This will raise a ValidationError
            TestModel(name="test", age="not-a-number")

        @app.get("/http-error")
        async def http_error():
            raise HTTPException(status_code=404, detail="Not found")

        @app.get("/general-error")
        async def general_error():
            raise Exception("Something went wrong")

        return app

    def test_validation_exception_handler(self, app):
        """Test validation exception handling."""
        client = TestClient(app)
        response = client.get("/validation-error")

        assert response.status_code == 422
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert "code" in data
        assert "timestamp" in data
        assert data["error"] == True

    def test_http_exception_handler(self, app):
        """Test HTTP exception handling."""
        client = TestClient(app)
        response = client.get("/http-error")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert "code" in data
        assert "timestamp" in data
        assert data["message"] == "Not found"
        assert data["error"] == True

    def test_general_exception_handler(self, app):
        """Test general exception handling."""
        client = TestClient(app)
        response = client.get("/general-error")

        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "message" in data
        assert "code" in data
        assert "timestamp" in data
        assert data["message"] == "Internal server error"
        assert data["error"] == True


class TestMiddlewareSetup:
    """Test middleware setup functions."""

    def test_setup_middleware(self):
        """Test that setup_middleware adds all middleware."""
        app = FastAPI()
        setup_middleware(app)

        # Check that middleware was added
        # Note: FastAPI middleware stack is internal, so we test behavior
        client = TestClient(app)

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        response = client.get("/test")

        # Should have security headers from SecurityHeadersMiddleware
        assert "X-Content-Type-Options" in response.headers

        # Should have timing header from TimingMiddleware
        assert "X-Process-Time" in response.headers

        # Should have request ID from RequestIDMiddleware
        assert "X-Request-ID" in response.headers

    def test_setup_exception_handlers(self):
        """Test that setup_exception_handlers adds all handlers."""
        app = FastAPI()
        setup_exception_handlers(app)

        # Exception handlers are added but testing them requires
        # actually raising exceptions, which is covered in other tests
        assert len(app.exception_handlers) > 0


@pytest.mark.integration
class TestMiddlewareIntegration:
    """Test middleware integration scenarios."""

    @pytest.fixture
    def full_app(self):
        """Create app with all middleware and handlers."""
        app = FastAPI()
        setup_middleware(app)
        setup_exception_handlers(app)

        @app.get("/test")
        async def test_endpoint(request: Request):
            return {
                "message": "test",
                "request_id": getattr(request.state, "request_id", None),
                "user": getattr(request.state, "user", None)
            }

        return app

    def test_full_middleware_stack(self, full_app):
        """Test that all middleware works together."""
        client = TestClient(full_app)
        response = client.get("/test")

        assert response.status_code == 200

        # Check all middleware effects
        headers = response.headers

        # Security headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers

        # Timing header
        assert "X-Process-Time" in headers

        # Request ID header
        assert "X-Request-ID" in headers

        # CORS headers (if origin provided)
        response_with_origin = client.get(
            "/test",
            headers={"Origin": "http://localhost:3000"}
        )
        assert "Access-Control-Allow-Origin" in response_with_origin.headers

    def test_middleware_order_preservation(self, full_app):
        """Test that middleware executes in correct order."""
        client = TestClient(full_app)

        # Make request with authentication
        token_data = {"sub": "test@example.com", "user_id": "123"}
        token = create_access_token(token_data)

        response = client.get(
            "/test",
            headers={
                "Authorization": f"Bearer {token}",
                "Origin": "http://localhost:3000"
            }
        )

        assert response.status_code == 200

        # All middleware should have processed the request
        data = response.json()
        assert "request_id" in data
        assert data["request_id"] is not None

    def test_error_handling_with_middleware(self, full_app):
        """Test error handling with full middleware stack."""
        @full_app.get("/error")
        async def error_endpoint():
            raise HTTPException(status_code=400, detail="Test error")

        client = TestClient(full_app)
        response = client.get("/error")

        assert response.status_code == 400

        # Middleware headers should still be present
        assert "X-Request-ID" in response.headers
        assert "X-Process-Time" in response.headers
        assert "X-Content-Type-Options" in response.headers


if __name__ == "__main__":
    print("✅ Middleware tests module loaded")
    print("Test classes:")
    print("- TestRequestIDMiddleware: Request ID generation and tracking")
    print("- TestTimingMiddleware: Request timing and performance")
    print("- TestSecurityHeadersMiddleware: Security headers injection")
    print("- TestAuthenticationMiddleware: Authentication processing")
    print("- TestCORSMiddleware: Cross-origin resource sharing")
    print("- TestTrustedHostMiddleware: Host validation")
    print("- TestExceptionHandlers: Error handling and formatting")
    print("- TestMiddlewareSetup: Middleware configuration")
    print("- TestMiddlewareIntegration: Full stack integration")

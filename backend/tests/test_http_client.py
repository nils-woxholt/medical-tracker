"""
Tests for HTTP Client Configuration and Utilities

This module tests HTTP client functionality including:
- HTTP client configuration and behavior
- Rate limiting with token bucket algorithm
- Retry logic with exponential backoff
- Request/response logging
- Client registry management
- Error handling and timeout behavior
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from app.core.http_client import (
    APIResponseError,
    EnhancedHTTPClient,
    HTTPClientConfig,
    HTTPClientRegistry,
    RateLimitConfig,
    RateLimitExceededError,
    RequestLog,
    ResponseLog,
    RetryConfig,
    TimeoutError,
    TokenBucketRateLimiter,
    create_api_client_config,
    create_client,
    get_client_registry,
    make_simple_request,
)


class TestRetryConfig:
    """Test retry configuration validation."""

    def test_valid_retry_config(self):
        """Test valid retry configuration."""
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            max_delay=30.0,
            exponential_backoff=True,
            retry_on_status=[429, 500, 502]
        )

        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 30.0
        assert config.exponential_backoff is True
        assert config.retry_on_status == [429, 500, 502]

    def test_retry_config_defaults(self):
        """Test retry configuration defaults."""
        config = RetryConfig()

        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_backoff is True
        assert 429 in config.retry_on_status
        assert 500 in config.retry_on_status

    def test_invalid_max_delay(self):
        """Test validation error for invalid max_delay."""
        with pytest.raises(ValueError, match="max_delay must be greater than base_delay"):
            RetryConfig(base_delay=10.0, max_delay=5.0)


class TestRateLimitConfig:
    """Test rate limit configuration validation."""

    def test_valid_rate_limit_config(self):
        """Test valid rate limit configuration."""
        config = RateLimitConfig(requests_per_second=5.0, burst_size=10)

        assert config.requests_per_second == 5.0
        assert config.burst_size == 10

    def test_rate_limit_config_defaults(self):
        """Test rate limit configuration defaults."""
        config = RateLimitConfig()

        assert config.requests_per_second == 10.0
        assert config.burst_size == 20

    def test_invalid_burst_size(self):
        """Test validation warning for small burst_size."""
        with pytest.raises(ValueError, match="burst_size should be at least requests_per_second"):
            RateLimitConfig(requests_per_second=10.0, burst_size=5)


class TestHTTPClientConfig:
    """Test HTTP client configuration."""

    def test_valid_client_config(self):
        """Test valid HTTP client configuration."""
        config = HTTPClientConfig(
            base_url="https://api.example.com",
            timeout=45.0,
            default_headers={"User-Agent": "TestClient/1.0"},
            verify_ssl=False
        )

        assert config.base_url == "https://api.example.com"
        assert config.timeout == 45.0
        assert config.default_headers["User-Agent"] == "TestClient/1.0"
        assert config.verify_ssl is False

    def test_client_config_defaults(self):
        """Test HTTP client configuration defaults."""
        config = HTTPClientConfig(base_url="https://api.example.com")

        assert config.timeout == 30.0
        assert config.verify_ssl is True
        assert config.follow_redirects is True
        assert config.max_redirects == 5
        assert isinstance(config.retry_config, RetryConfig)


class TestTokenBucketRateLimiter:
    """Test token bucket rate limiter."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = TokenBucketRateLimiter(requests_per_second=5.0, burst_size=10)

        assert limiter.requests_per_second == 5.0
        assert limiter.burst_size == 10
        assert limiter.tokens == 10  # Starts full

    @pytest.mark.asyncio
    async def test_acquire_tokens_success(self):
        """Test successful token acquisition."""
        limiter = TokenBucketRateLimiter(requests_per_second=10.0, burst_size=5)

        # Should be able to acquire tokens from initial burst
        assert await limiter.acquire(1) is True
        assert await limiter.acquire(2) is True
        assert await limiter.acquire(1) is True
        # Allow for small floating point differences
        assert abs(limiter.tokens - 1) < 0.1

    @pytest.mark.asyncio
    async def test_acquire_tokens_exhausted(self):
        """Test token acquisition when bucket is exhausted."""
        limiter = TokenBucketRateLimiter(requests_per_second=10.0, burst_size=2)

        # Exhaust tokens
        assert await limiter.acquire(2) is True
        assert limiter.tokens == 0

        # Should fail when no tokens available
        assert await limiter.acquire(1) is False

    @pytest.mark.asyncio
    async def test_token_refill_over_time(self):
        """Test token bucket refills over time."""
        limiter = TokenBucketRateLimiter(requests_per_second=2.0, burst_size=5)

        # Exhaust all tokens
        await limiter.acquire(5)
        assert limiter.tokens == 0

        # Wait and check refill
        with patch('app.core.http_client.time.time') as mock_time:
            original_time = limiter.last_update
            # Mock 1 second elapsed
            mock_time.side_effect = [original_time + 1.0]

            # Should refill 2 tokens (2 tokens/second * 1 second)
            assert await limiter.acquire(1) is True
            # Reset for second call
            mock_time.side_effect = [original_time + 1.0]
            assert await limiter.acquire(1) is True

    @pytest.mark.asyncio
    async def test_wait_for_tokens(self):
        """Test waiting for tokens to become available."""
        limiter = TokenBucketRateLimiter(requests_per_second=10.0, burst_size=1)

        # Exhaust tokens
        await limiter.acquire(1)

        # Mock time to simulate token refill
        with patch('asyncio.sleep') as mock_sleep:
            with patch.object(limiter, 'acquire', side_effect=[False, False, True]):
                await limiter.wait_for_tokens(1)

                # Should have called sleep
                assert mock_sleep.call_count >= 1


class TestRequestResponseLogging:
    """Test request and response logging structures."""

    def test_request_log_creation(self):
        """Test request log creation."""
        timestamp = datetime.utcnow()
        log = RequestLog(
            method="POST",
            url="https://api.example.com/users",
            headers={"Content-Type": "application/json"},
            body='{"name": "test"}',
            timestamp=timestamp,
            request_id="req-123"
        )

        assert log.method == "POST"
        assert log.url == "https://api.example.com/users"
        assert log.request_id == "req-123"

    def test_request_log_to_dict(self):
        """Test request log dictionary conversion."""
        timestamp = datetime.utcnow()
        log = RequestLog(
            method="GET",
            url="https://api.example.com/users",
            headers={"Authorization": "Bearer secret", "User-Agent": "TestClient"},
            body=None,
            timestamp=timestamp,
            request_id="req-456"
        )

        result = log.to_dict()

        assert result["method"] == "GET"
        assert result["url"] == "https://api.example.com/users"
        assert "Authorization" not in result["headers"]  # Filtered out
        assert "User-Agent" in result["headers"]
        assert result["body_size"] == 0
        assert result["request_id"] == "req-456"

    def test_response_log_creation(self):
        """Test response log creation."""
        timestamp = datetime.utcnow()
        log = ResponseLog(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body='{"users": []}',
            response_time_ms=150.5,
            timestamp=timestamp,
            request_id="req-789"
        )

        assert log.status_code == 200
        assert log.response_time_ms == 150.5
        assert log.request_id == "req-789"

    def test_response_log_to_dict(self):
        """Test response log dictionary conversion."""
        timestamp = datetime.utcnow()
        log = ResponseLog(
            status_code=404,
            headers={"Content-Type": "application/json"},
            body='{"error": "Not found"}',
            response_time_ms=45.2,
            timestamp=timestamp
        )

        result = log.to_dict()

        assert result["status_code"] == 404
        assert result["body_size"] == len('{"error": "Not found"}')
        assert result["response_time_ms"] == 45.2
        assert result["request_id"] is None


class TestEnhancedHTTPClient:
    """Test enhanced HTTP client functionality."""

    @pytest.fixture
    def basic_config(self):
        """Basic HTTP client configuration for testing."""
        return HTTPClientConfig(
            base_url="https://api.example.com",
            timeout=10.0
        )

    @pytest.fixture
    def rate_limited_config(self):
        """Rate limited HTTP client configuration for testing."""
        return HTTPClientConfig(
            base_url="https://api.example.com",
            rate_limit_config=RateLimitConfig(requests_per_second=2.0, burst_size=3)
        )

    @pytest.mark.asyncio
    async def test_client_initialization(self, basic_config):
        """Test HTTP client initialization."""
        client = EnhancedHTTPClient(basic_config)

        assert client.config == basic_config
        assert client.rate_limiter is None
        assert client._client.base_url == "https://api.example.com"

        await client.close()

    @pytest.mark.asyncio
    async def test_client_with_rate_limiting(self, rate_limited_config):
        """Test HTTP client with rate limiting enabled."""
        client = EnhancedHTTPClient(rate_limited_config)

        assert client.rate_limiter is not None
        assert client.rate_limiter.requests_per_second == 2.0
        assert client.rate_limiter.burst_size == 3

        await client.close()

    @pytest.mark.asyncio
    async def test_context_manager(self, basic_config):
        """Test HTTP client as async context manager."""
        async with EnhancedHTTPClient(basic_config) as client:
            assert client._client is not None

        # Client should be closed after context
        # Just check it doesn't raise an exception

    def test_build_url_relative(self, basic_config):
        """Test URL building with relative endpoints."""
        client = EnhancedHTTPClient(basic_config)

        assert client._build_url("users") == "https://api.example.com/users"
        assert client._build_url("/users") == "https://api.example.com/users"
        assert client._build_url("users/123") == "https://api.example.com/users/123"

    def test_build_url_absolute(self, basic_config):
        """Test URL building with absolute URLs."""
        client = EnhancedHTTPClient(basic_config)

        absolute_url = "https://other-api.com/data"
        assert client._build_url(absolute_url) == absolute_url

    def test_should_retry_logic(self, basic_config):
        """Test retry decision logic."""
        config = HTTPClientConfig(
            base_url="https://api.example.com",
            retry_config=RetryConfig(max_retries=2, retry_on_status=[500, 502])
        )
        client = EnhancedHTTPClient(config)

        # Should retry on configured status codes
        assert client._should_retry(500, 0) is True
        assert client._should_retry(502, 1) is True

        # Should not retry on other status codes
        assert client._should_retry(404, 0) is False
        assert client._should_retry(200, 0) is False

        # Should not retry after max attempts
        assert client._should_retry(500, 2) is False

    def test_calculate_delay_exponential(self, basic_config):
        """Test exponential backoff delay calculation."""
        config = HTTPClientConfig(
            base_url="https://api.example.com",
            retry_config=RetryConfig(
                base_delay=1.0,
                max_delay=10.0,
                exponential_backoff=True
            )
        )
        client = EnhancedHTTPClient(config)

        assert client._calculate_delay(0) == 1.0  # 1.0 * 2^0
        assert client._calculate_delay(1) == 2.0  # 1.0 * 2^1
        assert client._calculate_delay(2) == 4.0  # 1.0 * 2^2
        assert client._calculate_delay(10) == 10.0  # Capped at max_delay

    def test_calculate_delay_linear(self, basic_config):
        """Test linear backoff delay calculation."""
        config = HTTPClientConfig(
            base_url="https://api.example.com",
            retry_config=RetryConfig(
                base_delay=2.0,
                exponential_backoff=False
            )
        )
        client = EnhancedHTTPClient(config)

        assert client._calculate_delay(0) == 2.0
        assert client._calculate_delay(1) == 2.0
        assert client._calculate_delay(5) == 2.0

    @pytest.mark.asyncio
    async def test_successful_request(self, basic_config):
        """Test successful HTTP request."""
        client = EnhancedHTTPClient(basic_config)

        # Mock httpx client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"success": true}'
        mock_response.json.return_value = {"success": True}

        with patch.object(client._client, 'request', return_value=mock_response):
            response = await client.get("/users")

            assert response.status_code == 200
            assert response.json() == {"success": True}

        await client.close()

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rate_limited_config):
        """Test rate limit exceeded error."""
        client = EnhancedHTTPClient(rate_limited_config)

        # Mock rate limiter to return False
        with patch.object(client.rate_limiter, 'acquire', return_value=False):
            with pytest.raises(RateLimitExceededError):
                await client.get("/users")

        await client.close()

    @pytest.mark.asyncio
    async def test_api_error_response(self, basic_config):
        """Test API error response handling."""
        client = EnhancedHTTPClient(basic_config)

        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {}
        mock_response.text = "Not Found"
        mock_response.json.return_value = {"error": "User not found"}

        with patch.object(client._client, 'request', return_value=mock_response):
            with pytest.raises(APIResponseError) as exc_info:
                await client.get("/users/999")

            assert exc_info.value.status_code == 404
            assert "Not Found" in str(exc_info.value)

        await client.close()

    @pytest.mark.asyncio
    async def test_timeout_error(self, basic_config):
        """Test timeout error handling."""
        client = EnhancedHTTPClient(basic_config)

        # Mock timeout exception
        with patch.object(client._client, 'request', side_effect=httpx.TimeoutException("Timeout")):
            with pytest.raises(TimeoutError):
                await client.get("/slow-endpoint")

        await client.close()

    @pytest.mark.asyncio
    async def test_request_methods(self, basic_config):
        """Test different HTTP methods."""
        client = EnhancedHTTPClient(basic_config)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = "OK"

        with patch.object(client, '_make_request', return_value=mock_response) as mock_make_request:
            # Test GET
            await client.get("/users", params={"limit": 10})
            mock_make_request.assert_called_with("GET", "/users", params={"limit": 10}, headers=None)

            # Test POST
            await client.post("/users", json={"name": "test"})
            mock_make_request.assert_called_with("POST", "/users", json={"name": "test"}, data=None, headers=None)

            # Test PUT
            await client.put("/users/1", json={"name": "updated"})
            mock_make_request.assert_called_with("PUT", "/users/1", json={"name": "updated"}, data=None, headers=None)

            # Test PATCH
            await client.patch("/users/1", json={"email": "new@example.com"})
            mock_make_request.assert_called_with("PATCH", "/users/1", json={"email": "new@example.com"}, data=None, headers=None)

            # Test DELETE
            await client.delete("/users/1")
            mock_make_request.assert_called_with("DELETE", "/users/1", headers=None)

        await client.close()


class TestHTTPClientRegistry:
    """Test HTTP client registry functionality."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = HTTPClientRegistry()

        assert len(registry._clients) == 0
        assert registry.list_clients() == []

    def test_register_client(self):
        """Test client registration."""
        registry = HTTPClientRegistry()
        config = HTTPClientConfig(base_url="https://api.example.com")

        registry.register("test_client", config)

        assert "test_client" in registry._clients
        assert registry.get("test_client") is not None
        assert "test_client" in registry.list_clients()

    def test_register_duplicate_client(self):
        """Test registering duplicate client name."""
        registry = HTTPClientRegistry()
        config1 = HTTPClientConfig(base_url="https://api1.example.com")
        config2 = HTTPClientConfig(base_url="https://api2.example.com")

        registry.register("duplicate", config1)
        registry.register("duplicate", config2)  # Should overwrite

        client = registry.get("duplicate")
        assert client.config.base_url == "https://api2.example.com"

    def test_get_nonexistent_client(self):
        """Test getting nonexistent client."""
        registry = HTTPClientRegistry()

        assert registry.get("nonexistent") is None

    def test_remove_client(self):
        """Test client removal."""
        registry = HTTPClientRegistry()
        config = HTTPClientConfig(base_url="https://api.example.com")

        registry.register("to_remove", config)
        assert registry.get("to_remove") is not None

        registry.remove("to_remove")
        assert registry.get("to_remove") is None
        assert "to_remove" not in registry.list_clients()

    @pytest.mark.asyncio
    async def test_close_all_clients(self):
        """Test closing all registered clients."""
        registry = HTTPClientRegistry()
        config1 = HTTPClientConfig(base_url="https://api1.example.com")
        config2 = HTTPClientConfig(base_url="https://api2.example.com")

        registry.register("client1", config1)
        registry.register("client2", config2)

        # Mock client close methods
        client1 = registry.get("client1")
        client2 = registry.get("client2")

        with patch.object(client1, 'close') as mock_close1:
            with patch.object(client2, 'close') as mock_close2:
                await registry.close_all()

                mock_close1.assert_called_once()
                mock_close2.assert_called_once()
                assert len(registry._clients) == 0


class TestConvenienceFunctions:
    """Test convenience functions and utilities."""

    def test_create_api_client_config(self):
        """Test API client configuration creation."""
        config = create_api_client_config(
            base_url="https://api.example.com",
            api_key="test-key",
            timeout=45.0,
            rate_limit_rps=5.0,
            max_retries=2
        )

        assert config.base_url == "https://api.example.com"
        assert config.timeout == 45.0
        assert config.default_headers["X-API-Key"] == "test-key"
        assert config.rate_limit_config.requests_per_second == 5.0
        assert config.retry_config.max_retries == 2

    def test_create_api_client_config_minimal(self):
        """Test API client configuration with minimal parameters."""
        config = create_api_client_config(base_url="https://api.example.com")

        assert config.base_url == "https://api.example.com"
        assert config.timeout == 30.0  # Default
        assert config.rate_limit_config is None
        assert config.retry_config.max_retries == 3  # Default

    @pytest.mark.asyncio
    async def test_create_client_context_manager(self):
        """Test create_client context manager."""
        config = HTTPClientConfig(base_url="https://api.example.com")

        async with create_client(config) as client:
            assert isinstance(client, EnhancedHTTPClient)
            assert client.config.base_url == "https://api.example.com"

        # Client should be closed after context

    @pytest.mark.asyncio
    async def test_make_simple_request(self):
        """Test make_simple_request convenience function."""
        mock_response_data = {"users": [{"id": 1, "name": "test"}]}

        with patch('app.core.http_client.create_client') as mock_create_client:
            # Mock the context manager and client
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_client._make_request.return_value = mock_response

            # Setup context manager mock
            mock_create_client.return_value.__aenter__.return_value = mock_client

            result = await make_simple_request("GET", "https://api.example.com/users")

            assert result == mock_response_data
            mock_client._make_request.assert_called_once_with("GET", "https://api.example.com/users")

    def test_get_client_registry_singleton(self):
        """Test client registry singleton behavior."""
        registry1 = get_client_registry()
        registry2 = get_client_registry()

        assert registry1 is registry2  # Same instance


if __name__ == "__main__":
    print("✅ HTTP client tests loaded")
    print("Test classes:")
    print("- TestRetryConfig: Configuration validation")
    print("- TestRateLimitConfig: Rate limiting setup")
    print("- TestHTTPClientConfig: Client configuration")
    print("- TestTokenBucketRateLimiter: Rate limiting algorithm")
    print("- TestRequestResponseLogging: Request/response logging")
    print("- TestEnhancedHTTPClient: Main client functionality")
    print("- TestHTTPClientRegistry: Client management")
    print("- TestConvenienceFunctions: Utility functions")

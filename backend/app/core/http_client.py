"""
HTTP Client Configuration and External API Integration Utilities

This module provides HTTP client utilities, external API integration patterns,
rate limiting, timeout handling, and request/response logging for third-party
service integration.
"""

import asyncio
import json
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional
from urllib.parse import urljoin

import httpx
import structlog
from pydantic import BaseModel, Field, validator

from app.core.config import get_settings

settings = get_settings()
logger = structlog.get_logger(__name__)


class HTTPClientError(Exception):
    """Base exception for HTTP client errors."""
    pass


class RateLimitExceededError(HTTPClientError):
    """Raised when rate limit is exceeded."""
    pass


class TimeoutError(HTTPClientError):
    """Raised when request times out."""
    pass


class APIResponseError(HTTPClientError):
    """Raised when API returns error response."""
    def __init__(self, status_code: int, message: str, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


# =============================================================================
# Configuration Models
# =============================================================================

class RetryConfig(BaseModel):
    """Configuration for retry behavior."""
    max_retries: int = Field(default=3, ge=0, le=10)
    base_delay: float = Field(default=1.0, gt=0)
    max_delay: float = Field(default=60.0, gt=0)
    exponential_backoff: bool = Field(default=True)
    retry_on_status: List[int] = Field(default_factory=lambda: [429, 500, 502, 503, 504])

    @validator('max_delay')
    def max_delay_must_be_greater_than_base(cls, v, values):
        if 'base_delay' in values and v <= values['base_delay']:
            raise ValueError('max_delay must be greater than base_delay')
        return v


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting."""
    requests_per_second: float = Field(default=10.0, gt=0)
    burst_size: int = Field(default=20, gt=0)

    @validator('burst_size')
    def burst_size_reasonable(cls, v, values):
        if 'requests_per_second' in values and v < values['requests_per_second']:
            raise ValueError('burst_size should be at least requests_per_second')
        return v


class HTTPClientConfig(BaseModel):
    """Configuration for HTTP client behavior."""
    base_url: str
    timeout: float = Field(default=30.0, gt=0)
    default_headers: Dict[str, str] = Field(default_factory=dict)
    retry_config: RetryConfig = Field(default_factory=RetryConfig)
    rate_limit_config: Optional[RateLimitConfig] = None
    verify_ssl: bool = Field(default=True)
    follow_redirects: bool = Field(default=True)
    max_redirects: int = Field(default=5, ge=0)

    class Config:
        arbitrary_types_allowed = True


# =============================================================================
# Rate Limiter
# =============================================================================

class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for controlling request rates.
    
    This implementation allows burst requests up to burst_size,
    then limits to requests_per_second rate.
    """

    def __init__(self, requests_per_second: float, burst_size: int):
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            bool: True if tokens acquired, False if rate limited
        """
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update

            # Add tokens based on elapsed time
            tokens_to_add = elapsed * self.requests_per_second
            self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            else:
                return False

    async def wait_for_tokens(self, tokens: int = 1) -> None:
        """
        Wait until tokens are available.
        
        Args:
            tokens: Number of tokens needed
        """
        while not await self.acquire(tokens):
            # Calculate wait time
            wait_time = tokens / self.requests_per_second
            await asyncio.sleep(min(wait_time, 1.0))  # Max 1 second wait


# =============================================================================
# Request/Response Logging
# =============================================================================

@dataclass
class RequestLog:
    """Log entry for HTTP request."""
    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[str]
    timestamp: datetime
    request_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for structured logging."""
        headers = {}
        if self.headers:
            headers = {k: v for k, v in self.headers.items()
                      if k.lower() not in ["authorization", "x-api-key"]}  # Filter sensitive headers

        return {
            "method": self.method,
            "url": self.url,
            "headers": headers,
            "body_size": len(self.body) if self.body else 0,
            "timestamp": self.timestamp.isoformat(),
            "request_id": self.request_id
        }


@dataclass
class ResponseLog:
    """Log entry for HTTP response."""
    status_code: int
    headers: Dict[str, str]
    body: Optional[str]
    response_time_ms: float
    timestamp: datetime
    request_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for structured logging."""
        return {
            "status_code": self.status_code,
            "headers": dict(self.headers),
            "body_size": len(self.body) if self.body else 0,
            "response_time_ms": self.response_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "request_id": self.request_id
        }


# =============================================================================
# HTTP Client
# =============================================================================

class EnhancedHTTPClient:
    """
    Enhanced HTTP client with retry, rate limiting, and comprehensive logging.
    
    Features:
    - Automatic retries with exponential backoff
    - Rate limiting with token bucket algorithm
    - Comprehensive request/response logging
    - Timeout handling
    - Error handling with context
    """

    def __init__(self, config: HTTPClientConfig):
        self.config = config
        self.rate_limiter = None

        if config.rate_limit_config:
            self.rate_limiter = TokenBucketRateLimiter(
                config.rate_limit_config.requests_per_second,
                config.rate_limit_config.burst_size
            )

        # Create httpx client
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
            headers=config.default_headers,
            verify=config.verify_ssl,
            follow_redirects=config.follow_redirects,
            max_redirects=config.max_redirects
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith(('http://', 'https://')):
            return endpoint
        return urljoin(self.config.base_url.rstrip('/') + '/', endpoint.lstrip('/'))

    def _should_retry(self, status_code: int, attempt: int) -> bool:
        """Check if request should be retried."""
        if attempt >= self.config.retry_config.max_retries:
            return False
        return status_code in self.config.retry_config.retry_on_status

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay before retry."""
        if self.config.retry_config.exponential_backoff:
            delay = self.config.retry_config.base_delay * (2 ** attempt)
        else:
            delay = self.config.retry_config.base_delay

        return min(delay, self.config.retry_config.max_delay)

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with retry and rate limiting.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters
            
        Returns:
            httpx.Response: HTTP response
            
        Raises:
            RateLimitExceededError: If rate limited
            TimeoutError: If request times out
            APIResponseError: If API returns error
        """
        url = self._build_url(endpoint)
        request_id = kwargs.pop('request_id', None)

        # Apply rate limiting
        if self.rate_limiter:
            if not await self.rate_limiter.acquire():
                logger.warning("Rate limit exceeded", url=url, request_id=request_id)
                raise RateLimitExceededError("Rate limit exceeded")

        # Log request
        request_headers = kwargs.get('headers', {}) or {}
        request_body = kwargs.get('json') or kwargs.get('data') or ""
        if isinstance(request_body, dict):
            request_body = json.dumps(request_body)

        request_log = RequestLog(
            method=method.upper(),
            url=url,
            headers=request_headers,
            body=str(request_body) if request_body else None,
            timestamp=datetime.utcnow(),
            request_id=request_id
        )

        logger.info("HTTP request started", **request_log.to_dict())

        attempt = 0
        start_time = time.time()

        while True:
            try:
                response = await self._client.request(method, url, **kwargs)
                response_time_ms = (time.time() - start_time) * 1000

                # Log response
                response_log = ResponseLog(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=response.text if response.status_code >= 400 else None,
                    response_time_ms=response_time_ms,
                    timestamp=datetime.utcnow(),
                    request_id=request_id
                )

                logger.info("HTTP response received", **response_log.to_dict())

                # Check if retry is needed
                if self._should_retry(response.status_code, attempt):
                    attempt += 1
                    delay = self._calculate_delay(attempt)

                    logger.warning(
                        "Request failed, retrying",
                        status_code=response.status_code,
                        attempt=attempt,
                        delay=delay,
                        url=url,
                        request_id=request_id
                    )

                    await asyncio.sleep(delay)
                    start_time = time.time()  # Reset timer for retry
                    continue

                # Check for client/server errors
                if response.status_code >= 400:
                    error_data = None
                    try:
                        error_data = response.json()
                    except (json.JSONDecodeError, ValueError):
                        pass

                    raise APIResponseError(
                        response.status_code,
                        f"HTTP {response.status_code}: {response.text[:200]}",
                        error_data
                    )

                return response

            except httpx.TimeoutException as e:
                if self._should_retry(0, attempt):  # Treat timeout as retryable
                    attempt += 1
                    delay = self._calculate_delay(attempt)

                    logger.warning(
                        "Request timeout, retrying",
                        attempt=attempt,
                        delay=delay,
                        url=url,
                        request_id=request_id,
                        error=str(e)
                    )

                    await asyncio.sleep(delay)
                    start_time = time.time()
                    continue

                logger.error("Request timeout", url=url, request_id=request_id, error=str(e))
                raise TimeoutError(f"Request timeout: {str(e)}")

            except httpx.RequestError as e:
                logger.error("Request error", url=url, request_id=request_id, error=str(e))
                raise HTTPClientError(f"Request error: {str(e)}")

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make GET request."""
        return await self._make_request(
            "GET",
            endpoint,
            params=params,
            headers=headers,
            **kwargs
        )

    async def post(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make POST request."""
        return await self._make_request(
            "POST",
            endpoint,
            json=json,
            data=data,
            headers=headers,
            **kwargs
        )

    async def put(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make PUT request."""
        return await self._make_request(
            "PUT",
            endpoint,
            json=json,
            data=data,
            headers=headers,
            **kwargs
        )

    async def patch(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make PATCH request."""
        return await self._make_request(
            "PATCH",
            endpoint,
            json=json,
            data=data,
            headers=headers,
            **kwargs
        )

    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make DELETE request."""
        return await self._make_request(
            "DELETE",
            endpoint,
            headers=headers,
            **kwargs
        )


# =============================================================================
# Client Factory and Registry
# =============================================================================

class HTTPClientRegistry:
    """Registry for managing multiple HTTP clients."""

    def __init__(self):
        self._clients: Dict[str, EnhancedHTTPClient] = {}

    def register(self, name: str, config: HTTPClientConfig) -> None:
        """Register a new HTTP client."""
        if name in self._clients:
            logger.warning("Overwriting existing HTTP client", client_name=name)

        self._clients[name] = EnhancedHTTPClient(config)
        logger.info("HTTP client registered", client_name=name, base_url=config.base_url)

    def get(self, name: str) -> Optional[EnhancedHTTPClient]:
        """Get HTTP client by name."""
        return self._clients.get(name)

    def remove(self, name: str) -> None:
        """Remove HTTP client."""
        if name in self._clients:
            del self._clients[name]
            logger.info("HTTP client removed", client_name=name)

    async def close_all(self) -> None:
        """Close all registered clients."""
        for name, client in self._clients.items():
            try:
                await client.close()
                logger.info("HTTP client closed", client_name=name)
            except Exception as e:
                logger.error("Error closing HTTP client", client_name=name, error=str(e))

        self._clients.clear()

    def list_clients(self) -> List[str]:
        """List all registered client names."""
        return list(self._clients.keys())


# Global client registry
_client_registry = HTTPClientRegistry()


def get_client_registry() -> HTTPClientRegistry:
    """Get global HTTP client registry."""
    return _client_registry


@asynccontextmanager
async def create_client(config: HTTPClientConfig) -> AsyncGenerator[EnhancedHTTPClient, None]:
    """
    Create temporary HTTP client with automatic cleanup.
    
    Args:
        config: HTTP client configuration
        
    Yields:
        EnhancedHTTPClient: Configured HTTP client
        
    Example:
        config = HTTPClientConfig(base_url="https://api.example.com")
        async with create_client(config) as client:
            response = await client.get("/users")
            return response.json()
    """
    client = EnhancedHTTPClient(config)
    try:
        yield client
    finally:
        await client.close()


# =============================================================================
# Convenience Functions
# =============================================================================

def create_api_client_config(
    base_url: str,
    api_key: Optional[str] = None,
    timeout: float = 30.0,
    rate_limit_rps: Optional[float] = None,
    max_retries: int = 3
) -> HTTPClientConfig:
    """
    Create API client configuration with common defaults.
    
    Args:
        base_url: Base URL for the API
        api_key: API key for authentication
        timeout: Request timeout in seconds
        rate_limit_rps: Rate limit in requests per second
        max_retries: Maximum number of retries
        
    Returns:
        HTTPClientConfig: Configured HTTP client
        
    Example:
        config = create_api_client_config(
            base_url="https://api.example.com",
            api_key="your-api-key",
            rate_limit_rps=10.0
        )
    """
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    rate_limit_config = None
    if rate_limit_rps:
        rate_limit_config = RateLimitConfig(
            requests_per_second=rate_limit_rps,
            burst_size=int(rate_limit_rps * 2)  # Allow 2x burst
        )

    return HTTPClientConfig(
        base_url=base_url,
        timeout=timeout,
        default_headers=headers,
        retry_config=RetryConfig(max_retries=max_retries),
        rate_limit_config=rate_limit_config
    )


async def make_simple_request(
    method: str,
    url: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Make simple HTTP request without client setup.
    
    Args:
        method: HTTP method
        url: Full URL
        **kwargs: Additional request parameters
        
    Returns:
        Dict: JSON response data
        
    Example:
        data = await make_simple_request("GET", "https://api.example.com/users")
        print(data["users"])
    """
    config = HTTPClientConfig(base_url="")

    async with create_client(config) as client:
        response = await client._make_request(method, url, **kwargs)
        return response.json()


# =============================================================================
# Integration with FastAPI
# =============================================================================

async def startup_http_clients() -> None:
    """
    Initialize HTTP clients on application startup.
    
    Add this to your FastAPI lifespan or startup event.
    """
    registry = get_client_registry()

    # Example: Register external API clients
    if hasattr(settings, 'EXTERNAL_API_URL') and settings.EXTERNAL_API_URL:
        external_config = create_api_client_config(
            base_url=settings.EXTERNAL_API_URL,
            api_key=getattr(settings, 'EXTERNAL_API_KEY', None),
            rate_limit_rps=10.0
        )
        registry.register("external_api", external_config)

    logger.info("HTTP clients initialized",
               clients=registry.list_clients())


async def shutdown_http_clients() -> None:
    """
    Clean up HTTP clients on application shutdown.
    
    Add this to your FastAPI lifespan or shutdown event.
    """
    registry = get_client_registry()
    await registry.close_all()
    logger.info("HTTP clients shut down")


if __name__ == "__main__":
    print("✅ HTTP client utilities loaded")
    print("Features:")
    print("- EnhancedHTTPClient: Retry, rate limiting, logging")
    print("- HTTPClientRegistry: Client management")
    print("- TokenBucketRateLimiter: Request rate control")
    print("- Configuration models: HTTPClientConfig, RetryConfig, RateLimitConfig")
    print("- Integration functions: startup_http_clients, shutdown_http_clients")

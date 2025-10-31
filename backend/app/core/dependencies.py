"""
Dependency Injection Utilities and Patterns

This module provides comprehensive dependency injection patterns for FastAPI,
including database sessions, authentication, configuration, and service layer
components following FastAPI best practices.
"""

from functools import lru_cache
from typing import Annotated, AsyncGenerator, Generator, Optional

import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

import app.schemas as schemas
from app.core.auth import decode_access_token, extract_user_id_from_token
from app.core.config import Settings, get_settings
from app.models.base import DatabaseManager, get_database

logger = structlog.get_logger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


class DependencyError(Exception):
    """Base exception for dependency injection errors."""
    pass


class AuthenticationRequiredError(DependencyError):
    """Raised when authentication is required but not provided."""
    pass


class PermissionDeniedError(DependencyError):
    """Raised when user lacks required permissions."""
    pass


# =============================================================================
# Core Dependencies
# =============================================================================

def get_request_id(request: Request) -> str:
    """
    Extract request ID from the request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Request ID for correlation
        
    Example:
        @app.get("/example")
        async def endpoint(request_id: Annotated[str, Depends(get_request_id)]):
            logger.info("Processing request", request_id=request_id)
            return {"request_id": request_id}
    """
    return getattr(request.state, "request_id", "unknown")


def get_user_agent(request: Request) -> Optional[str]:
    """
    Extract User-Agent header from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Optional[str]: User-Agent string or None
    """
    return request.headers.get("user-agent")


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Client IP address
        
    Note:
        Handles X-Forwarded-For and X-Real-IP headers for proxy scenarios.
    """
    # Check for forwarded IP headers (proxy scenarios)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"


# =============================================================================
# Configuration Dependencies
# =============================================================================

@lru_cache()
def get_cached_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: Application configuration
        
    Note:
        Uses LRU cache to avoid re-parsing environment variables on each request.
        Cache is cleared when the process restarts.
    """
    return get_settings()


def get_environment_name() -> str:
    """
    Get current environment name.
    
    Returns:
        str: Environment name (development, testing, production)
    """
    settings = get_cached_settings()
    return settings.ENVIRONMENT


def get_debug_mode() -> bool:
    """
    Check if debug mode is enabled.
    
    Returns:
        bool: True if debug mode is enabled
    """
    settings = get_cached_settings()
    return settings.DEBUG


# =============================================================================
# Database Dependencies
# =============================================================================

def get_sync_db_session() -> Generator[Session, None, None]:
    """
    Get synchronous database session dependency.
    
    Yields:
        Session: SQLAlchemy synchronous session
        
    Example:
        @app.get("/users")
        def get_users(db: Annotated[Session, Depends(get_sync_db_session)]):
            return db.query(User).all()
    """
    db_manager = get_database()
    # Use SQLModel Session directly for typing consistency
    wrapper = db_manager.get_session()
    session = next(iter(wrapper))  # underlying Session instance
    try:
        yield session  # type: ignore[misc]
    except Exception as e:
        logger.error("Database session error", error=str(e))
        session.rollback()
        raise
    finally:
        session.close()


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get asynchronous database session dependency.
    
    Yields:
        AsyncSession: SQLAlchemy asynchronous session
        
    Example:
        @app.get("/users")
        async def get_users(db: Annotated[AsyncSession, Depends(get_async_db_session)]):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    db_manager = get_database()
    async with db_manager.get_async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error("Async database session error", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db_manager() -> DatabaseManager:
    """
    Get database manager dependency.
    
    Returns:
        DatabaseManager: Database connection manager
        
    Example:
        @app.get("/health/db")
        def db_health(manager: Annotated[DatabaseManager, Depends(get_db_manager)]):
            return manager.check_health()
    """
    return get_database()


# =============================================================================
# Authentication Dependencies
# =============================================================================

def get_optional_auth_token(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)]
) -> Optional[str]:
    """
    Extract optional authentication token from request.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        Optional[str]: JWT token if provided, None otherwise
        
    Example:
        @app.get("/profile")
        def profile(token: Annotated[Optional[str], Depends(get_optional_auth_token)]):
            if token:
                # User is authenticated
                return get_user_profile(token)
            else:
                # Public endpoint
                return {"message": "Not authenticated"}
    """
    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials
    return None


def get_required_auth_token(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)]
) -> str:
    """
    Extract required authentication token from request.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        str: JWT token
        
    Raises:
        HTTPException: If no valid token is provided
        
    Example:
        @app.get("/protected")
        def protected_endpoint(token: Annotated[str, Depends(get_required_auth_token)]):
            # User is guaranteed to be authenticated
            return {"message": "Access granted"}
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


def get_current_user_id(
    token: Annotated[str, Depends(get_required_auth_token)]
) -> str:
    """
    Get current authenticated user ID from JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        str: User ID
        
    Raises:
        HTTPException: If token is invalid or doesn't contain user ID
        
    Example:
        @app.get("/me")
        def get_me(user_id: Annotated[str, Depends(get_current_user_id)]):
            return {"user_id": user_id}
    """
    try:
        payload = decode_access_token(token)
    except Exception as e:
        logger.warning("Invalid authentication token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id

# ------------------------------------------------------------------
# Lean Mode Fallback: allow session cookie-based auth when bearer token
# not supplied. This preserves legacy bearer token paths while enabling
# cookie-only flows for UI interactions.
# ------------------------------------------------------------------
from fastapi import Request

def get_current_user_id_or_session(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)]
) -> str:
    """Return current user id from either bearer token or session middleware.

    Order of resolution:
      1. Bearer token (strict) if provided.
      2. request.state.user_id set by SessionMiddleware or AuthenticationMiddleware.

    Raises 401 if neither present.
    """
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
        try:
            payload = decode_access_token(token)
            user_id = payload.get("user_id")
            if user_id:
                return user_id
        except Exception:
            # Fall through to session lookup
            pass
    # Session cookie path
    sid_user = getattr(request.state, "user_id", None)
    if sid_user:
        return sid_user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Convenience Annotated alias
CurrentUserIdOrSession = Annotated[str, Depends(get_current_user_id_or_session)]


def get_optional_user_id(
    token: Annotated[Optional[str], Depends(get_optional_auth_token)]
) -> Optional[str]:
    """
    Get optional authenticated user ID from JWT token.
    
    Args:
        token: JWT token (optional)
        
    Returns:
        Optional[str]: User ID if authenticated, None otherwise
        
    Example:
        @app.get("/content")
        def get_content(user_id: Annotated[Optional[str], Depends(get_optional_user_id)]):
            if user_id:
                return get_personalized_content(user_id)
            else:
                return get_public_content()
    """
    if not token:
        return None

    try:
        user_id = extract_user_id_from_token(token)
        return user_id
    except Exception:
        # Token is invalid, but this is optional dependency
        return None


# =============================================================================
# Pagination Dependencies
# =============================================================================

def get_pagination_params(
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100,
    search: Optional[str] = None
) -> schemas.PaginationParams:
    """
    Get pagination parameters with validation.
    
    Args:
        page: Page number (1-based)
        per_page: Items per page
        max_per_page: Maximum allowed items per page
        
    Returns:
        PaginationParams: Validated pagination parameters
        
    Raises:
        HTTPException: If parameters are invalid
        
    Example:
        @app.get("/items")
        def get_items(
            pagination: Annotated[schemas.PaginationParams, Depends(get_pagination_params)]
        ):
            return get_paginated_items(pagination.page, pagination.per_page)
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be 1 or greater"
        )

    if per_page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Items per page must be 1 or greater"
        )

    if per_page > max_per_page:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Items per page cannot exceed {max_per_page}"
        )

    params = schemas.PaginationParams(
        page=page,
        page_size=per_page,  # alias wired via Field(alias="page_size")
        offset=(page - 1) * per_page,
        search=search,
    )
    return params


# =============================================================================
# Service Layer Dependencies
# =============================================================================

class ServiceRegistry:
    """
    Registry for service layer dependencies.
    
    This allows for dependency injection of service classes
    and can be extended for testing with mock services.
    """

    def __init__(self):
        self._services = {}

    def register(self, service_type: type, service_instance: object):
        """Register a service instance for a given type."""
        self._services[service_type] = service_instance

    def get(self, service_type: type):
        """Get a service instance by type."""
        return self._services.get(service_type)

    def clear(self):
        """Clear all registered services."""
        self._services.clear()


# Global service registry
_service_registry = ServiceRegistry()


def get_service_registry() -> ServiceRegistry:
    """
    Get the global service registry.
    
    Returns:
        ServiceRegistry: Global service registry
        
    Example:
        # In main.py or startup
        registry = get_service_registry()
        registry.register(UserService, UserService(db_manager))
        
        # In endpoint
        def endpoint(registry: Annotated[ServiceRegistry, Depends(get_service_registry)]):
            user_service = registry.get(UserService)
            return user_service.get_users()
    """
    return _service_registry


# =============================================================================
# Composite Dependencies
# =============================================================================

class RequestContext:
    """
    Composite dependency that provides common request context.
    
    Combines multiple dependencies into a single object for convenience.
    """

    def __init__(
        self,
        request_id: str,
        user_id: Optional[str],
        client_ip: str,
        user_agent: Optional[str],
        settings: Settings
    ):
        self.request_id = request_id
        self.user_id = user_id
        self.client_ip = client_ip
        self.user_agent = user_agent
        self.settings = settings

    @property
    def is_authenticated(self) -> bool:
        """Check if the request is from an authenticated user."""
        return self.user_id is not None

    def to_dict(self) -> dict:
        """Convert context to dictionary for logging."""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "is_authenticated": self.is_authenticated
        }


def get_request_context(
    request_id: Annotated[str, Depends(get_request_id)],
    user_id: Annotated[Optional[str], Depends(get_optional_user_id)],
    client_ip: Annotated[str, Depends(get_client_ip)],
    user_agent: Annotated[Optional[str], Depends(get_user_agent)],
    settings: Annotated[Settings, Depends(get_cached_settings)]
) -> RequestContext:
    """
    Get complete request context dependency.
    
    Args:
        request_id: Request correlation ID
        user_id: Authenticated user ID (optional)
        client_ip: Client IP address
        user_agent: User agent string
        settings: Application settings
        
    Returns:
        RequestContext: Complete request context
        
    Example:
        @app.get("/example")
        def endpoint(ctx: Annotated[RequestContext, Depends(get_request_context)]):
            logger.info("Request received", **ctx.to_dict())
            if ctx.is_authenticated:
                return f"Hello user {ctx.user_id}"
            else:
                return "Hello anonymous user"
    """
    return RequestContext(
        request_id=request_id,
        user_id=user_id,
        client_ip=client_ip,
        user_agent=user_agent,
        settings=settings
    )


# =============================================================================
# Dependency Aliases
# =============================================================================

# Type aliases for common dependencies
SyncDatabase = Annotated[Session, Depends(get_sync_db_session)]
AsyncDatabase = Annotated[AsyncSession, Depends(get_async_db_session)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
OptionalUserId = Annotated[Optional[str], Depends(get_optional_user_id)]
RequestId = Annotated[str, Depends(get_request_id)]
Pagination = Annotated[schemas.PaginationParams, Depends(get_pagination_params)]
Context = Annotated[RequestContext, Depends(get_request_context)]
AppSettings = Annotated[Settings, Depends(get_cached_settings)]

# =============================================================================
# Utility Functions
# =============================================================================

def require_permissions(*permissions: str):
    """
    Decorator factory for requiring specific permissions.
    
    Args:
        *permissions: Required permission names
        
    Returns:
        Dependency function that checks permissions
        
    Example:
        require_admin = require_permissions("admin")
        
        @app.delete("/users/{user_id}")
        def delete_user(
            user_id: str,
            current_user: Annotated[str, Depends(require_admin)]
        ):
            # User has admin permission
            delete_user_by_id(user_id)
    
    Note:
        This is a placeholder implementation. In a real application,
        you would check user permissions against a database or external service.
    """
    def permission_dependency(
        token: Annotated[str, Depends(get_required_auth_token)]
    ) -> str:
        try:
            payload = decode_access_token(token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Placeholder permission check (always passes)
        logger.info("Permission check", user_id=user_id, required_permissions=permissions)
        return user_id

    return permission_dependency


def create_custom_dependency(dependency_func):
    """
    Helper to create custom dependency with proper typing.
    
    Args:
        dependency_func: Function to use as dependency
        
    Returns:
        Annotated dependency type
        
    Example:
        def get_custom_service():
            return CustomService()
        
        CustomService = create_custom_dependency(get_custom_service)
        
        @app.get("/endpoint")
        def endpoint(service: CustomService):
            return service.do_something()
    """
    return Annotated[type(dependency_func()), Depends(dependency_func)]


# =============================================================================
# Convenience Aliases and Additional Functions
# =============================================================================

def get_current_user(
    token: Annotated[Optional[str], Depends(get_optional_auth_token)]
) -> dict:
    """
    Get current authenticated user information from JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        dict: User information including user_id and email
        
    Example:
        @app.get("/profile")
        def get_profile(user: dict = Depends(get_current_user)):
            return {"user_id": user["user_id"], "email": user["email"]}
    """
    if not token:
        logger.info("No auth token provided; using demo user context")
        return {
            "user_id": "demo-user",
            "email": "demo@example.com",
        }

    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        user_email = payload.get("sub")  # Standard JWT claim for subject (email)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "user_id": user_id,
            "email": user_email,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Invalid authentication token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_authenticated_user(
    token: Annotated[Optional[str], Depends(get_optional_auth_token)]
) -> dict:
    """Strict variant of get_current_user that requires authentication.

    Returns user context if a valid Bearer token is provided; otherwise raises 401.
    Used for endpoints whose contract requires 401 Unauthorized when no token is supplied.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        user_email = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "user_id": user_id,
            "email": user_email,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Invalid authentication token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Database session alias for convenience  
get_db = get_sync_db_session


# =============================================================================
# Service Layer Dependencies
# =============================================================================

def get_medication_service(db: Session = Depends(get_sync_db_session)):
    """
    Get medication service instance with database session.
    
    Args:
        db: Database session dependency
        
    Returns:
        MedicationService: Configured medication service instance
    """
    from app.services.medication import MedicationService
    # Cast to sqlmodel Session type for constructor expectations
    return MedicationService(db)  # type: ignore[arg-type]


if __name__ == "__main__":
    print("✅ Dependency injection utilities loaded")
    print("Available dependencies:")
    print("- Database: SyncDatabase, AsyncDatabase, get_db")
    print("- Authentication: CurrentUserId, OptionalUserId, get_current_user")
    print("- Request: RequestId, Context, Pagination")
    print("- Configuration: AppSettings")
    print("- Services: ServiceRegistry")

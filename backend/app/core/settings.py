"""
Application Settings Configuration

This module handles environment configuration and application settings
for the SaaS Medical Tracker application using Pydantic Settings.

Features:
- Environment-based configuration
- Type validation and conversion
- Default values for development
- Support for .env files
- Security-focused settings
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic.networks import AnyHttpUrl

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # =============================================================================
    # Application Settings
    # =============================================================================

    APP_NAME: str = "SaaS Medical Tracker"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # =============================================================================
    # Server Settings
    # =============================================================================

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # =============================================================================
    # Database Settings
    # =============================================================================

    DATABASE_URL: str = "sqlite:///./app.db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # =============================================================================
    # Security Settings
    # =============================================================================

    SECRET_KEY: str = "your-secret-key-change-in-production"

    # NOTE: Legacy JWT configuration retained for potential future token-based flows.
    # Current auth design uses opaque, server-stored session identifiers (FR-013, FR-015, FR-017).
    JWT_SECRET_KEY: str = "your-jwt-secret-change-in-production"  # JWT signing secret used for access tokens
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Rolling renewal window (activity refresh)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # Longer-lived refresh token window (if refresh implemented)

    # Password hashing
    PASSWORD_MIN_LENGTH: int = 8
    BCRYPT_ROUNDS: int = 12

    # =============================================================================
    # CORS Settings
    # =============================================================================

    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from environment string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # =============================================================================
    # Security Headers and Middleware
    # =============================================================================

    TRUSTED_HOSTS: Optional[List[str]] = None
    ALLOWED_HOSTS: List[str] = ["*"]

    @field_validator("TRUSTED_HOSTS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_host_list(cls, v):
        """Parse host list from environment string."""
        if v is None:
            return None
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    # Security headers
    ENABLE_HSTS: bool = False
    CSP_POLICY: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

    # Session settings
    SESSION_SECRET_KEY: Optional[str] = None
    SESSION_MAX_AGE: int = 86400  # 24 hours
    # Authentication/session control constants (feature: login functionality)
    IDLE_SESSION_TIMEOUT_MINUTES: int = 30  # FR-013: Idle timeout (inactivity)
    MAX_FAILED_LOGINS: int = 5              # FR-015: Lockout threshold
    LOCKOUT_DURATION_MINUTES: int = 15      # FR-015: Lockout duration

    # =============================================================================
    # Logging and Monitoring
    # =============================================================================

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    LOG_REQUEST_BODY: bool = False
    LOG_RESPONSE_BODY: bool = False
    LOG_MAX_BODY_SIZE: int = 1024

    # Performance monitoring
    SLOW_REQUEST_THRESHOLD: float = 1.0
    LOG_SLOW_REQUESTS: bool = True

    # Structured logging
    SERVICE_NAME: str = "saas-medical-tracker"
    COMPONENT_NAME: str = "backend"

    # =============================================================================
    # Rate Limiting
    # =============================================================================

    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # =============================================================================
    # Email Settings (for notifications)
    # =============================================================================

    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # =============================================================================
    # External Services
    # =============================================================================

    # Redis (for caching and sessions)
    REDIS_URL: Optional[str] = None
    REDIS_ENABLED: bool = False

    # Sentry (error monitoring)
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENABLED: bool = False

    # =============================================================================
    # API Settings
    # =============================================================================

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SaaS Medical Tracker API"

    # OpenAPI configuration
    OPENAPI_URL: str = "/openapi.json"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"

    # =============================================================================
    # Testing Settings
    # =============================================================================

    TESTING: bool = False
    TEST_DATABASE_URL: Optional[str] = None

    # =============================================================================
    # Validators and Configuration
    # =============================================================================

    @field_validator("SECRET_KEY", "JWT_SECRET_KEY")
    @classmethod
    def validate_secret_keys(cls, v):
        """Validate that secret keys are secure in production."""
        if v.startswith("your-") and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("Secret keys must be changed in production")
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v or not v.startswith(("sqlite://", "postgresql://", "mysql://")):
            raise ValueError("DATABASE_URL must be a valid database connection string")
        return v

    class Config:
        """Pydantic configuration."""
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() in ("development", "dev", "local")

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT.lower() in ("production", "prod")

    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.TESTING or self.ENVIRONMENT.lower() in ("test", "testing")


# =============================================================================
# Settings Instance and Cache
# =============================================================================

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    This function creates and caches a Settings instance,
    ensuring the same configuration is used throughout the application.
    """
    return Settings()


# =============================================================================
# Environment Detection Helpers
# =============================================================================

def is_development() -> bool:
    """Check if running in development environment."""
    return get_settings().is_development()


def is_production() -> bool:
    """Check if running in production environment."""
    return get_settings().is_production()


def is_testing() -> bool:
    """Check if running in testing environment."""
    return get_settings().is_testing()


# =============================================================================
# Configuration Validation
# =============================================================================

def validate_settings() -> None:
    """
    Validate application settings.
    
    Raises:
        ValueError: If critical settings are misconfigured
    """
    settings = get_settings()

    # Check required production settings
    if settings.is_production():
        required_production_settings = [
            "SECRET_KEY",
            "JWT_SECRET_KEY",
            "DATABASE_URL",
        ]

        for setting_name in required_production_settings:
            value = getattr(settings, setting_name)
            if not value or (isinstance(value, str) and value.startswith("your-")):
                raise ValueError(f"{setting_name} must be set for production")

    # Validate CORS origins
    if settings.BACKEND_CORS_ORIGINS:
        for origin in settings.BACKEND_CORS_ORIGINS:
            if not str(origin).startswith(("http://", "https://")):
                if str(origin) != "*":  # Allow wildcard
                    raise ValueError(f"Invalid CORS origin: {origin}")


# =============================================================================
# Settings Summary for Debugging
# =============================================================================

def get_settings_summary() -> dict:
    """
    Get a summary of current settings for debugging.
    
    Returns:
        Dictionary with non-sensitive settings information
    """
    settings = get_settings()

    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "database_type": settings.DATABASE_URL.split("://")[0] if "://" in settings.DATABASE_URL else "unknown",
        "cors_origins_count": len(settings.BACKEND_CORS_ORIGINS),
        "log_level": settings.LOG_LEVEL,
        "service_name": settings.SERVICE_NAME,
        "component_name": settings.COMPONENT_NAME,
    }


if __name__ == "__main__":
    # Test settings loading
    try:
        settings = get_settings()
        print("✅ Settings loaded successfully")
        print(f"Environment: {settings.ENVIRONMENT}")
        print(f"Database: {settings.DATABASE_URL.split('://')[0]}")
        print(f"Debug mode: {settings.DEBUG}")
        print(f"CORS origins: {len(settings.BACKEND_CORS_ORIGINS)}")

        # Validate settings
        validate_settings()
        print("✅ Settings validation passed")

    except Exception as e:
        print(f"❌ Settings error: {e}")
        raise

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

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # =============================================================================
    # Application Settings
    # =============================================================================

    APP_NAME: str = "SaaS Medical Tracker"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")

    # =============================================================================
    # Server Settings
    # =============================================================================

    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    RELOAD: bool = Field(default=True, env="RELOAD")

    # =============================================================================
    # Database Settings
    # =============================================================================

    DATABASE_URL: str = Field(
        default="sqlite:///./app.db",
        env="DATABASE_URL",
        description="Database connection URL"
    )
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")

    # =============================================================================
    # Security Settings
    # =============================================================================

    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY",
        description="Secret key for cryptographic operations"
    )

    JWT_SECRET_KEY: str = Field(
        default="your-jwt-secret-change-in-production",
        env="JWT_SECRET_KEY",
        description="JWT signing secret"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        env="JWT_REFRESH_TOKEN_EXPIRE_DAYS"
    )

    # Password hashing
    PASSWORD_MIN_LENGTH: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    BCRYPT_ROUNDS: int = Field(default=12, env="BCRYPT_ROUNDS")

    # =============================================================================
    # CORS Settings
    # =============================================================================

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="BACKEND_CORS_ORIGINS",
        description="Allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    CORS_ALLOW_METHODS: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    CORS_ALLOW_HEADERS: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")

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

    TRUSTED_HOSTS: Optional[List[str]] = Field(
        default=None,
        env="TRUSTED_HOSTS",
        description="Trusted host names for production"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["*"],
        env="ALLOWED_HOSTS",
        description="Allowed host names"
    )

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
    ENABLE_HSTS: bool = Field(default=False, env="ENABLE_HSTS")
    CSP_POLICY: str = Field(
        default="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        env="CSP_POLICY"
    )

    # Session settings
    SESSION_SECRET_KEY: Optional[str] = Field(default=None, env="SESSION_SECRET_KEY")
    SESSION_MAX_AGE: int = Field(default=86400, env="SESSION_MAX_AGE")  # 24 hours

    # =============================================================================
    # Logging and Monitoring
    # =============================================================================

    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")  # json or text
    LOG_REQUEST_BODY: bool = Field(default=False, env="LOG_REQUEST_BODY")
    LOG_RESPONSE_BODY: bool = Field(default=False, env="LOG_RESPONSE_BODY")
    LOG_MAX_BODY_SIZE: int = Field(default=1024, env="LOG_MAX_BODY_SIZE")

    # Performance monitoring
    SLOW_REQUEST_THRESHOLD: float = Field(default=1.0, env="SLOW_REQUEST_THRESHOLD")
    LOG_SLOW_REQUESTS: bool = Field(default=True, env="LOG_SLOW_REQUESTS")

    # Structured logging
    SERVICE_NAME: str = Field(default="saas-medical-tracker", env="SERVICE_NAME")
    COMPONENT_NAME: str = Field(default="backend", env="COMPONENT_NAME")

    # =============================================================================
    # Rate Limiting
    # =============================================================================

    RATE_LIMIT_ENABLED: bool = Field(default=False, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    RATE_LIMIT_WINDOW: int = Field(default=60, env="RATE_LIMIT_WINDOW")  # seconds

    # =============================================================================
    # Email Settings (for notifications)
    # =============================================================================

    SMTP_TLS: bool = Field(default=True, env="SMTP_TLS")
    SMTP_PORT: Optional[int] = Field(default=587, env="SMTP_PORT")
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_USER: Optional[str] = Field(default=None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")

    EMAILS_FROM_EMAIL: Optional[str] = Field(default=None, env="EMAILS_FROM_EMAIL")
    EMAILS_FROM_NAME: Optional[str] = Field(default=None, env="EMAILS_FROM_NAME")

    # =============================================================================
    # External Services
    # =============================================================================

    # Redis (for caching and sessions)
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    REDIS_ENABLED: bool = Field(default=False, env="REDIS_ENABLED")

    # Sentry (error monitoring)
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    SENTRY_ENABLED: bool = Field(default=False, env="SENTRY_ENABLED")

    # =============================================================================
    # API Settings
    # =============================================================================

    API_V1_STR: str = Field(default="/api/v1", env="API_V1_STR")
    PROJECT_NAME: str = Field(default="SaaS Medical Tracker API", env="PROJECT_NAME")

    # OpenAPI configuration
    OPENAPI_URL: str = Field(default="/openapi.json", env="OPENAPI_URL")
    DOCS_URL: str = Field(default="/docs", env="DOCS_URL")
    REDOC_URL: str = Field(default="/redoc", env="REDOC_URL")

    # =============================================================================
    # Testing Settings
    # =============================================================================

    TESTING: bool = Field(default=False, env="TESTING")
    TEST_DATABASE_URL: Optional[str] = Field(default=None, env="TEST_DATABASE_URL")

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

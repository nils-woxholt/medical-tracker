"""
Application Configuration Module

This module provides centralized configuration management using Pydantic settings.
It handles environment variables, validation, and provides typed configuration objects.
"""

import json
import os
from functools import lru_cache
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables with the same name.
    For example: PROJECT_NAME="My App" or DATABASE_URL="postgresql://..."
    """

    # Project Information
    PROJECT_NAME: str = "SaaS Medical Tracker"
    PROJECT_DESCRIPTION: str = "Track medications, log symptoms, and manage your health data securely"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security Configuration
    SECRET_KEY: str = "your-secret-key-change-this-in-production-use-openssl-rand-hex-32"
    JWT_SECRET: str = "your-secret-key-change-this-in-production-32-chars-minimum"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database Configuration
    DATABASE_URL: str = "sqlite:///app.db"
    DATABASE_TEST_URL: str = "sqlite:///test.db"

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Security Headers
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_JSON_OUTPUT: bool = False

    # Feature Flags
    ENABLE_MEDICATION_MASTER: bool = False
    ENABLE_HEALTH_PASSPORT: bool = False

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # File Upload Configuration
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIRECTORY: str = "uploads"

    # Email Configuration (for future use)
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # External Services (for future use)
    REDIS_URL: Optional[str] = None

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """
        Parse CORS origins from environment variable.
        
        Accepts comma-separated string or list of URLs.
        """
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []

            if v.startswith("["):
                try:
                    parsed = json.loads(v)
                except json.JSONDecodeError as exc:
                    raise ValueError("Invalid JSON list for BACKEND_CORS_ORIGINS") from exc

                if isinstance(parsed, list):
                    return parsed
                raise ValueError("BACKEND_CORS_ORIGINS must be a list")

            return [i.strip() for i in v.split(",") if i.strip()]

        if isinstance(v, list):
            return v
        raise ValueError(v)

    @field_validator("ALLOWED_HOSTS", mode="before")
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """
        Parse allowed hosts from environment variable.
        
        Accepts comma-separated string or list of hostnames.
        """
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []

            if v.startswith("["):
                try:
                    parsed = json.loads(v)
                except json.JSONDecodeError as exc:
                    raise ValueError("Invalid JSON list for ALLOWED_HOSTS") from exc

                if isinstance(parsed, list):
                    return parsed
                raise ValueError("ALLOWED_HOSTS must be a list")

            return [i.strip() for i in v.split(",") if i.strip()]

        if isinstance(v, list):
            return v
        raise ValueError(v)

    @field_validator("DEBUG", mode="before")
    def parse_debug(cls, v: Union[bool, str]) -> bool:
        """Parse DEBUG setting from string or boolean."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)

    @field_validator("ENABLE_MEDICATION_MASTER", mode="before")
    def parse_medication_master_flag(cls, v: Union[bool, str]) -> bool:
        """Parse ENABLE_MEDICATION_MASTER feature flag."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)

    @field_validator("ENABLE_HEALTH_PASSPORT", mode="before")
    def parse_health_passport_flag(cls, v: Union[bool, str]) -> bool:
        """Parse ENABLE_HEALTH_PASSPORT feature flag."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)

    @field_validator("DATABASE_URL", mode="before")
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v:
            raise ValueError("DATABASE_URL cannot be empty")

        # For development, allow SQLite
        if v.startswith("sqlite"):
            return v

        # For production, require PostgreSQL
        if not v.startswith(("postgresql://", "postgresql+psycopg2://")):
            if os.getenv("ENVIRONMENT", "development") == "production":
                raise ValueError("Production environment requires PostgreSQL database")

        return v

    @field_validator("SECRET_KEY")
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key length for security."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("JWT_SECRET")
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret key length for security."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        return v

    @property
    def ACCESS_TOKEN_EXPIRE_SECONDS(self) -> int:
        """Get access token expiration time in seconds."""
        return self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


class TestSettings(Settings):
    """
    Test-specific settings that override base settings.
    
    Used during testing to ensure isolation and predictable behavior.
    """

    # Test Environment
    ENVIRONMENT: str = "test"
    DEBUG: bool = True

    # Test Database (in-memory SQLite)
    DATABASE_URL: str = "sqlite:///test.db"

    # Relaxed security for testing
    SECRET_KEY: str = "test-secret-key-32-characters-long"
    JWT_SECRET: str = "test-jwt-secret-key-32-characters"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 5  # Short expiry for testing

    # Disable external services in tests
    REDIS_URL: Optional[str] = None
    SMTP_HOST: Optional[str] = None

    # Test-specific logging
    LOG_LEVEL: str = "DEBUG"
    LOG_JSON_OUTPUT: bool = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Uses LRU cache to avoid re-parsing environment variables on every call.
    Cache is cleared when the process restarts.
    
    Returns:
        Settings: Application configuration object
    """
    # Check if we're in test mode
    if os.getenv("TESTING") == "true":
        return TestSettings()

    return Settings()


# Example of how to use settings in other modules
if __name__ == "__main__":
    settings = get_settings()
    print(f"Project: {settings.PROJECT_NAME}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database: {settings.DATABASE_URL}")
    print(f"Debug: {settings.DEBUG}")
    print(f"CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
    print(f"Feature - Medication Master: {settings.ENABLE_MEDICATION_MASTER}")
    print(f"Feature - Health Passport: {settings.ENABLE_HEALTH_PASSPORT}")

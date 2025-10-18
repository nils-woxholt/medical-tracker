"""
Logging Configuration Module

This module provides centralized logging configuration for the SaaS Medical Tracker application.
It uses structlog for structured logging with JSON output suitable for production environments.
"""

import logging
import sys
from typing import Any, Dict, Optional

import structlog
from structlog.types import EventDict, Processor


def add_request_id(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add request ID to log entries when available.
    
    Args:
        logger: The logger instance
        method_name: The log method name
        event_dict: The event dictionary
        
    Returns:
        Updated event dictionary with request ID
    """
    # TODO: Implement request ID extraction from context
    # This would typically come from middleware that sets request context
    event_dict["request_id"] = getattr(event_dict.get("_record", {}), "request_id", None)
    return event_dict


def add_service_info(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add service information to all log entries.
    
    Args:
        logger: The logger instance
        method_name: The log method name
        event_dict: The event dictionary
        
    Returns:
        Updated event dictionary with service info
    """
    event_dict["service"] = "saas-medical-tracker"
    event_dict["component"] = "backend"
    return event_dict


def filter_sensitive_data(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Filter sensitive data from log entries for security and privacy compliance.
    
    Important: This is critical for HIPAA compliance and user privacy.
    
    Args:
        logger: The logger instance
        method_name: The log method name
        event_dict: The event dictionary
        
    Returns:
        Updated event dictionary with sensitive data filtered
    """
    sensitive_fields = {
        "password", "token", "secret", "key", "authorization",
        "ssn", "social_security", "credit_card", "medical_record_number",
        "patient_id", "health_data", "symptoms", "medications"
    }

    def _filter_dict(data: Any) -> Any:
        if isinstance(data, dict):
            return {
                k: "***REDACTED***" if k.lower() in sensitive_fields else _filter_dict(v)
                for k, v in data.items()
            }
        elif isinstance(data, (list, tuple)):
            return [_filter_dict(item) for item in data]
        return data

    return _filter_dict(event_dict)


def setup_logging(
    log_level: str = "INFO",
    json_output: bool = True,
    development_mode: bool = False,
) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Whether to output logs in JSON format
        development_mode: Whether running in development mode (affects formatting)
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure processors based on environment
    processors: list[Processor] = [
        # Add timestamps
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),

        # Add service and request information
        add_service_info,
        add_request_id,

        # Security and privacy filters
        filter_sensitive_data,

        # Stack info for exceptions
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]

    if development_mode and not json_output:
        # Pretty console output for development
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    else:
        # JSON output for production
        processors.extend([
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ])

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )

    # Set up root logger to use structlog
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    root_logger.addHandler(handler)

    # Suppress noisy third-party logs in production
    if not development_mode:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = structlog.get_logger(__name__)
    logger.info(
        "Logging configured successfully",
        log_level=log_level,
        json_output=json_output,
        development_mode=development_mode,
    )


class SecurityAuditLogger:
    """
    Specialized logger for security and audit events.
    
    This logger ensures security-critical events are properly logged
    for compliance and security monitoring.
    """

    def __init__(self):
        self.logger = structlog.get_logger("security")

    def log_authentication_attempt(
        self,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        success: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Log authentication attempts for security monitoring.
        
        Args:
            user_id: User identifier (if known)
            email: User email (will be partially redacted)
            success: Whether authentication was successful
            ip_address: Client IP address
            user_agent: Client user agent
        """
        # Redact email for privacy
        redacted_email = None
        if email:
            parts = email.split("@")
            if len(parts) == 2:
                username = parts[0]
                domain = parts[1]
                redacted_email = f"{username[:3]}***@{domain}"

        self.logger.info(
            "Authentication attempt",
            event_type="auth_attempt",
            user_id=user_id,
            email=redacted_email,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        success: bool = True,
    ):
        """
        Log access to sensitive data for audit trails.
        
        Args:
            user_id: User accessing the data
            resource_type: Type of resource (e.g., 'medical_record', 'medication')
            resource_id: Resource identifier
            action: Action performed (read, create, update, delete)
            success: Whether the action was successful
        """
        self.logger.info(
            "Data access event",
            event_type="data_access",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            success=success,
        )

    def log_privacy_event(
        self,
        user_id: str,
        event_type: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Log privacy-related events (data export, deletion requests, etc.).
        
        Args:
            user_id: User identifier
            event_type: Type of privacy event
            details: Additional event details
        """
        self.logger.info(
            "Privacy event",
            event_type="privacy",
            privacy_event_type=event_type,
            user_id=user_id,
            details=details,
        )


# Global security audit logger instance
security_audit = SecurityAuditLogger()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


# Example usage and testing
if __name__ == "__main__":
    # Setup logging for testing
    setup_logging(log_level="DEBUG", development_mode=True, json_output=False)

    logger = get_logger(__name__)

    # Test various log levels
    logger.debug("Debug message for development")
    logger.info("Application started", version="1.0.0")
    logger.warning("This is a warning message")
    logger.error("An error occurred", error_code=500)

    # Test security audit logging
    security_audit.log_authentication_attempt(
        email="user@example.com",
        success=True,
        ip_address="192.168.1.1",
    )

    security_audit.log_data_access(
        user_id="12345",
        resource_type="medication",
        resource_id="med-001",
        action="read",
    )

    # Test sensitive data filtering
    logger.info(
        "User data processed",
        user_data={
            "name": "John Doe",
            "password": "secret123",  # Should be redacted
            "medication": "Aspirin",  # Should be redacted
            "age": 35,
        }
    )

    print("✅ Logging test completed")

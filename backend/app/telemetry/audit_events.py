"""Audit event type enumerations for authentication flows.

These constants support structured audit logging and metrics tagging.
Referenced by future tasks T016 (recorder) and endpoint implementations.
"""

from enum import Enum

class AuthAuditEvent(str, Enum):
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    REGISTER_SUCCESS = "auth.register.success"
    LOGOUT = "auth.logout"
    LOCKOUT_TRIGGER = "auth.lockout.trigger"
    DEMO_START = "auth.demo.start"

__all__ = ["AuthAuditEvent"]

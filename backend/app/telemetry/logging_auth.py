"""Structured logging helpers specialized for auth flows.

Separates auth domain logging from generic application logging and audit events.
Used for fine-grained observability (performance, decision branches) without
polluting audit trail semantics.
"""

from __future__ import annotations

from typing import Optional
import time
from contextlib import contextmanager
import structlog

logger = structlog.get_logger("auth")

def log_login_attempt(email: str, success: bool, locked: bool = False, remaining_lock_seconds: Optional[int] = None, session_id: str | None = None, user_id: str | None = None, duration_ms: int | None = None, failure_reason: str | None = None, masked_identity: str | None = None) -> None:
    logger.info(
        "auth.login",
        email=email,
        success=success,
        locked=locked,
        remaining_lock_seconds=remaining_lock_seconds,
        session_id=session_id,
        user_id=user_id,
        duration_ms=duration_ms,
        failure_reason=failure_reason,
        masked_identity=masked_identity,
    )

def log_logout(user_id: str | None, session_id: str | None, success: bool = True, duration_ms: int | None = None) -> None:
    logger.info(
        "auth.logout",
        user_id=user_id,
        session_id=session_id,
        success=success,
        duration_ms=duration_ms,
    )

def log_session_created(user_id: str, session_id: str, demo: bool = False, duration_ms: int | None = None) -> None:
    logger.info("auth.session.created", user_id=user_id, session_id=session_id, demo=demo, duration_ms=duration_ms)

def log_lockout_trigger(user_id: str, attempts: int, locked_until_iso: str, session_id: str | None = None) -> None:
    logger.info(
        "auth.lockout.trigger",
        user_id=user_id,
        attempts=attempts,
        locked_until=locked_until_iso,
        session_id=session_id,
    )

def log_identity_lookup(user_id: str | None, masked_identity: str | None, success: bool, duration_ms: int | None = None) -> None:
    logger.info(
        "auth.identity.lookup",
        user_id=user_id,
        masked_identity=masked_identity,
        success=success,
        duration_ms=duration_ms,
    )

def log_registration_attempt(email: str, success: bool, user_id: str | None = None, duration_ms: int | None = None, failure_reason: str | None = None) -> None:
    """Emit structured log for a registration attempt."""
    logger.info(
        "auth.registration",
        email=email,
        success=success,
        user_id=user_id,
        duration_ms=duration_ms,
        failure_reason=failure_reason,
    )

def log_registration_success(user_id: str, email: str, session_id: str | None = None, duration_ms: int | None = None) -> None:
    logger.info(
        "auth.registration.success",
        user_id=user_id,
        email=email,
        session_id=session_id,
        duration_ms=duration_ms,
    )

@contextmanager
def time_auth_log():
    """Context manager to measure duration of an auth operation for logging helpers."""
    start = time.time()
    try:
        yield lambda: int((time.time() - start) * 1000)
    finally:
        pass

__all__ = [
    "log_login_attempt",
    "log_logout",
    "log_session_created",
    "log_lockout_trigger",
    "log_identity_lookup",
    "log_registration_attempt",
    "log_registration_success",
    "time_auth_log",
]

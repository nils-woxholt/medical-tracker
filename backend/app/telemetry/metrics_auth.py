"""Authentication-specific metrics wrappers.

Provides convenience functions around the global MetricsRegistry for emitting
auth flow counters and gauges. Keeps metric cardinality controlled.
"""

from __future__ import annotations

from typing import Literal
import structlog
import time
from contextlib import contextmanager
from app.telemetry.metrics import get_metrics_registry

logger = structlog.get_logger(__name__)

# Use the shared global metrics_registry so that increments are reflected in the /metrics endpoint.
# Previously this module instantiated a fresh MetricsRegistry which meant counters were
# updated on an isolated registry instance and not exposed, causing tests that look for
# authentication_attempts_total samples to fail.


def inc_login(result: Literal["success", "failure", "locked"], method: str = "password") -> None:
    """Increment authentication attempt metrics (single increment, no noisy diagnostics)."""
    registry = get_metrics_registry()
    try:
        registry.authentication_attempts_total.labels(result=result, method=method).inc()
    except Exception as e:
        # Never raise from metrics paths; log once at debug level
        logger.debug("auth_metrics.increment_failed", error=str(e), result=result, method=method)

def inc_session_status(valid: bool) -> None:
    # session_status_checks_total labels: valid
    registry = get_metrics_registry()
    if hasattr(registry, "session_status_checks_total"):
        registry.session_status_checks_total.labels(valid=str(valid).lower()).inc()

def inc_demo_session_created(success: bool) -> None:
    # demo_session_creations_total labels: success
    registry = get_metrics_registry()
    if hasattr(registry, "demo_session_creations_total"):
        registry.demo_session_creations_total.labels(success=str(success).lower()).inc()

def inc_registration() -> None:
    registry = get_metrics_registry()
    registry.operations_total.labels(operation="registration", type="auth", status="success").inc()

def inc_logout() -> None:
    registry = get_metrics_registry()
    registry.operations_total.labels(operation="logout", type="auth", status="success").inc()
    # Also increment dedicated logout counter (result=success)
    if hasattr(registry, "auth_logout_total"):
        registry.auth_logout_total.labels(result="success").inc()

def inc_logout_failure() -> None:
    registry = get_metrics_registry()
    # record failure path for logout attempts
    if hasattr(registry, "auth_logout_total"):
        registry.auth_logout_total.labels(result="failure").inc()

def gauge_active_sessions(count: int) -> None:
    registry = get_metrics_registry()
    registry.active_requests.set(count)  # Reuse active_requests gauge for simplicity; could add dedicated gauge later.

__all__ = ["inc_login", "inc_registration", "inc_logout", "gauge_active_sessions", "inc_session_status", "inc_demo_session_created"]

# New helpers introduced in T014

def observe_auth_action_duration(action: str, result: str, duration_seconds: float) -> None:
    """Record duration of an auth action (login/logout/identity/register)."""
    registry = get_metrics_registry()
    if hasattr(registry, "auth_action_duration_seconds"):
        try:
            registry.auth_action_duration_seconds.labels(action=action, result=result).observe(duration_seconds)
        except Exception as e:
            logger.debug("auth_metrics.observe_failed", error=str(e), action=action, result=result)

@contextmanager
def time_auth_action(action: str, result: str = "success"):
    """Context manager to time an auth action and emit to histogram."""
    start = time.time()
    try:
        yield
        final_result = result
    except Exception:
        final_result = "failure"
        raise
    finally:
        observe_auth_action_duration(action, final_result, time.time() - start)

__all__.extend(["observe_auth_action_duration", "time_auth_action", "inc_logout_failure"])

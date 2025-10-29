"""Security constants and helpers for cookie-based auth.

Phase 2 (Foundational) addition for Login UI feature:
Provides central definitions for the HTTP-only session cookie used to
store the JWT (or opaque session identifier) once login/register flows
are implemented.

Design goals:
 - Single source of truth for cookie name & attributes
 - Easy to adjust SameSite/secure flags for local dev vs production
 - Explicit defaults: HTTP-only, Secure (except when DEBUG), SameSite=Lax
 - Support future split between access/refresh if needed

NOTE: Actual setting/clearing of cookies will occur in auth endpoints.
This module only supplies configuration to avoid scattering literals.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Dict, Any

from app.core.config import get_settings

settings = get_settings()

# Primary session cookie name (JWT bearer stored server-side only - cookie carries token)
SESSION_COOKIE_NAME: str = "mt_session"

# Potential future refresh cookie (not yet used; reserved for expansion)
REFRESH_COOKIE_NAME: str = "mt_refresh"

# Default cookie configuration applied when setting the session cookie.
# Adjust Secure flag automatically based on environment to ease local development.
COOKIE_DEFAULTS: Dict[str, Any] = {
    "httponly": True,
    # Only mark secure when not in local debug to allow browser to send over http:// during dev
    "secure": not settings.DEBUG,
    # Lax prevents CSRF on top-level POST from other sites while allowing normal navigation
    "samesite": "lax",
    # Path scoped to root so all API endpoints receive it
    "path": "/",
}

# Standard session lifetime (seconds) aligned with settings token expiry (30m default)
COOKIE_SESSION_MAX_AGE: int = settings.ACCESS_TOKEN_EXPIRE_SECONDS


def build_session_cookie(token: str) -> Dict[str, Any]:
    """Return keyword args for Response.set_cookie for the session JWT.

    Separates token value from attribute dictionary so callers can:
        response.set_cookie(key=SESSION_COOKIE_NAME, value=token, **attrs)

    Args:
        token: Encoded JWT or opaque session value.

    Returns:
        Dict[str, Any]: Attributes suitable for set_cookie
    """
    attrs = COOKIE_DEFAULTS.copy()
    attrs.update({"max_age": COOKIE_SESSION_MAX_AGE})
    return attrs


def build_clear_cookie() -> Dict[str, Any]:
    """Return kwargs for deleting the session cookie (logout / invalid session)."""
    attrs = COOKIE_DEFAULTS.copy()
    # Expire immediately; browsers respect either max_age=0 or empty value + past expiry
    attrs.update({"max_age": 0})
    return attrs


__all__ = [
    "SESSION_COOKIE_NAME",
    "REFRESH_COOKIE_NAME",
    "COOKIE_DEFAULTS",
    "COOKIE_SESSION_MAX_AGE",
    "build_session_cookie",
    "build_clear_cookie",
]

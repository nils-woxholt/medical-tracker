"""Cookie helper for auth session management.

Defines standardized attributes for session cookies (security settings from plan).
"""

from __future__ import annotations

from fastapi import Response
from typing import Optional, Literal
from datetime import datetime
from app.core.settings import get_settings

COOKIE_NAME = "session"

def set_session_cookie(response: Response, session_id: str, *, secure: bool | None = None, http_only: bool = True, same_site: str | None = None, max_age: int = 1800) -> None:
    """Set session cookie with hardened defaults.

    If secure/same_site not explicitly provided, derive from environment:
    - Production: secure=True, same_site="strict"
    - Non-production: secure=False (for local dev & tests), same_site="lax"
    """
    settings = get_settings()
    if secure is None:
        secure = settings.ENVIRONMENT.lower() == "production"
    if same_site is None:
        same_site = "strict" if settings.ENVIRONMENT.lower() == "production" else "lax"
    samesite_literal: Literal['lax','strict','none']
    lower = same_site.lower()
    if lower not in {"lax","strict","none"}:
        lower = "lax"
    samesite_literal = lower  # type: ignore
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_id,
        httponly=http_only,
        secure=secure,
        # FastAPI expects one of: 'lax', 'strict', 'none'
        samesite=samesite_literal,
        max_age=max_age,
        path="/",
    )

def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")

__all__ = ["set_session_cookie", "clear_session_cookie", "COOKIE_NAME"]

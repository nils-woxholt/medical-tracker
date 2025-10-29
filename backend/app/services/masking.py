"""Email and identity masking utilities.

Provides a single function `mask_email` used by auth flows to render a
non-enumerable identity when display_name is absent.

Rules:
 - Preserve up to first 3 characters of local part (or full if <3).
 - Append ellipsis + domain.
 - If malformed (no '@'), return original string.
 - Never raise exceptions; fall back to original input on unexpected errors.
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)

def mask_email(email: str) -> str:
    """Mask an email for display without enabling easy enumeration.

    Examples:
    - `user@example.com` -> `use...@example.com`
    - `ab@example.com`   -> `ab...@example.com`
    - `x@example.com`    -> `x...@example.com`
    - `invalid`          -> `invalid`
    """
    if '@' not in email:
        return email
    try:
        local, domain = email.split('@', 1)
        visible = local[:3] if len(local) >= 3 else local
        return f"{visible}...@{domain}"
    except Exception as e:  # pragma: no cover - defensive path
        logger.debug("mask_email.error", error=str(e))
        return email

__all__ = ["mask_email"]
"""Registration endpoint implementation (T033, T039)."""

from fastapi import Depends, HTTPException, Response, Request, status
import structlog
from pydantic import BaseModel, EmailStr

from app.api.auth import auth_router
from app.core.dependencies_auth import (
    get_user_service,
    get_session_service,
    normalize_email,
)
from app.services.user import UserService
from app.services.session_service import SessionService
from app.services.cookie_helper import set_session_cookie
from app.telemetry.audit_recorder import get_audit_recorder
from app.telemetry.logging_auth import log_session_created
from app.telemetry.metrics_auth import inc_login, gauge_active_sessions
from app.core.auth import create_password_hash

PASSWORD_MIN_LENGTH = 8

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None  # legacy/display field retained for contract tests

class UserPublic(BaseModel):
    id: str
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None  # echoed for compatibility with early contract tests

class UserResponse(BaseModel):
    data: UserPublic | None = None
    # Accept either string error code or structured dict (future-proof)
    error: str | dict | None = None

GENERIC_ERROR = "REGISTRATION_FAILED"
logger = structlog.get_logger(__name__)


def _validate_password(password: str) -> None:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError("PASSWORD_TOO_SHORT")
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise ValueError("PASSWORD_WEAK")

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    response: Response,
    request: Request,
    user_service: UserService = Depends(get_user_service),
    session_service: SessionService = Depends(get_session_service),
):
    recorder = get_audit_recorder()
    # Legacy contract: versioned path /api/v1/auth/register must still return 501 Not Implemented.
    # Detect versioned path invocation and short-circuit.
    if request.url.path.startswith("/api/v1/auth/"):
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not yet implemented")
    logger.info("register.request.received", raw_email=payload.email, has_display=bool(payload.display_name))
    try:
        email = normalize_email(payload.email)
    except ValueError as e:
        logger.warning("register.email_normalization_failed", error=str(e))
        inc_login("failure")
        recorder.record("auth.login.failure")  # treat as failure for metrics parity
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=GENERIC_ERROR)

    # Password policy
    try:
        _validate_password(payload.password)
    except ValueError as e:
        logger.warning("register.password_policy_failed", reason=str(e))
        inc_login("failure")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Uniqueness handled optimistically; rely on service.create_user raising ValueError("EMAIL_IN_USE")

    # Create user
    # Derive name fields; prefer explicit first/last, fall back to display_name for first_name
    # Ensure required name fields meet model min_length >=1 constraints to avoid validation errors.
    # Fallback strategy:
    #  - first_name: explicit first_name -> display_name -> email local part -> 'User'
    #  - last_name: explicit last_name -> (if display_name provided and different) display_name -> 'User'
    email_local_part = email.split("@")[0] if "@" in email else email
    first_name = (payload.first_name or payload.display_name or email_local_part or "User").strip()
    if not first_name:
        first_name = "User"
    last_name = (payload.last_name or (payload.display_name if payload.display_name and payload.display_name != first_name else None) or "User").strip()
    if not last_name:
        last_name = "User"
    from fastapi.responses import JSONResponse
    try:
        user = user_service.create_user(email=email, first_name=first_name, last_name=last_name, password=payload.password)
    except ValueError as ve:
        # Expected conflict race or duplicate detection inside service layer
        if str(ve) == "EMAIL_IN_USE":
            logger.info("register.email_conflict", email=email)
            inc_login("failure")
            return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={
                "error": "EMAIL_EXISTS",
                "message": "EMAIL_IN_USE",
                "detail": "EMAIL_IN_USE",
            })
        logger.error("register.user_create_value_error", email=email, error=str(ve))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=GENERIC_ERROR)
    except Exception as e:  # pragma: no cover - unexpected create failure
        logger.error("register.user_create_failed", email=email, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=GENERIC_ERROR)
    # create session
    try:
        sess = session_service.create(user_id=user.id)
    except Exception as e:  # pragma: no cover - unexpected session failure
        logger.error("register.session_create_failed", user_id=user.id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=GENERIC_ERROR)
    # secure=False for test environment (HTTP); production should enable secure
    set_session_cookie(response, sess.id, secure=False)
    logger.info("register.cookie.set", session_id=sess.id)
    log_session_created(user.id, sess.id, demo=False)
    recorder.record("auth.register.success", user_id=user.id, session_id=sess.id)
    inc_login("success")
    gauge_active_sessions(1)
    logger.info("register.success", user_id=user.id, email=user.email, session_id=sess.id)
    return UserResponse(data=UserPublic(id=user.id, email=user.email, first_name=first_name or None, last_name=last_name or None, display_name=payload.display_name or first_name or None))

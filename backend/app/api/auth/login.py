"""Login endpoint implementation (T023)."""

from datetime import datetime
from fastapi import Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi import status
from pydantic import BaseModel, EmailStr

from app.api.auth import auth_router
from app.core.dependencies_auth import (
    get_user_service,
    get_session_service,
    is_locked,
    register_failed_attempt,
    register_success,
    normalize_email,
)
from app.services.user import UserService
from app.services.session_service import SessionService
from app.services.cookie_helper import set_session_cookie
import structlog
logger = structlog.get_logger(__name__)
from app.services.rate_limit import allow as rate_allow
from app.telemetry.metrics import metrics_registry
from app.telemetry.audit_recorder import get_audit_recorder
from app.telemetry.logging_auth import (
    log_login_attempt,
    log_session_created,
    log_lockout_trigger,
)
from app.telemetry.metrics_auth import inc_login, gauge_active_sessions
from app.models.user import User
from app.services.lockout import LOCK_THRESHOLD, LOCK_DURATION_MINUTES
from app.services.masking import mask_email
from app.services.login_guard import guard as login_guard, DuplicateInFlight


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    display_name: str | None = None


class UserResponse(BaseModel):
    data: UserPublic | None = None
    error: dict | None = None


GENERIC_ERROR = {"error": "INVALID_CREDENTIALS"}


def _generic_credentials_response() -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=GENERIC_ERROR)


@auth_router.post("/login", response_model=UserResponse)
def login(
    payload: LoginRequest,
    response: Response,
    user_service: UserService = Depends(get_user_service),
    session_service: SessionService = Depends(get_session_service),
):
    recorder = get_audit_recorder()
    # Basic rate limiting by email (enumeration resistance: still same error message)
    # Use raw input email before normalization to avoid distinguishing normalized variants
    if not rate_allow(f"login:{payload.email.lower()}"):
        # Emit security event metric
        metrics_registry.security_events_total.labels(event_type="rate_limit", severity="low").inc()
        raise HTTPException(status_code=429, detail="TOO_MANY_ATTEMPTS")
    try:
        email = normalize_email(payload.email)
    except ValueError:
        # Treat invalid email format same as invalid credentials (enumeration resistance)
        inc_login("failure")
        log_login_attempt(payload.email, success=False, masked_identity=mask_email(payload.email))
        recorder.record("auth.login.failure")
        return _generic_credentials_response()
    # Duplicate submission guard (best-effort)
    try:
        with login_guard(f"login:{email}"):
            user: User | None = user_service.get_by_email(email)
            if not user:
                inc_login("failure")
                log_login_attempt(email, success=False, masked_identity=mask_email(email))
                recorder.record("auth.login.failure")
                return _generic_credentials_response()
            # At this point, user is guaranteed non-None for type checkers
            assert user is not None

            # Check lock state first
            if is_locked(user):
                inc_login("locked")
                remaining = int((user.lock_until - datetime.utcnow()).total_seconds()) if user.lock_until else LOCK_DURATION_MINUTES * 60
                log_login_attempt(email, success=False, locked=True, remaining_lock_seconds=remaining, masked_identity=mask_email(email))
                recorder.record(
                    "auth.login.failure",
                    user_id=user.id,
                    attempt_count=user.failed_attempts,
                    locked_until=user.lock_until,
                )
                raise HTTPException(status_code=423, detail={"error": "ACCOUNT_LOCKED", "lock_expires_at": user.lock_until.isoformat() if user.lock_until else None})

            # Verify password
            if not user_service.authenticate(email=email, password=payload.password):
                register_failed_attempt(user)
                # persist mutation
                user_service.db.add(user)
                user_service.db.commit()
                user_service.db.refresh(user)
                inc_login("failure")
                # Lock triggered?
                if is_locked(user):
                    lock_iso = user.lock_until.isoformat() if user.lock_until else ""
                    log_lockout_trigger(user.id, user.failed_attempts, lock_iso)
                    recorder.record(
                        "auth.lockout.trigger",
                        user_id=user.id,
                        attempt_count=user.failed_attempts,
                        locked_until=user.lock_until,
                    )
                    raise HTTPException(status_code=423, detail={"error": "ACCOUNT_LOCKED", "lock_expires_at": user.lock_until.isoformat() if user.lock_until else None})
                log_login_attempt(email, success=False, masked_identity=mask_email(email))
                recorder.record("auth.login.failure", user_id=user.id, attempt_count=user.failed_attempts)
                return _generic_credentials_response()

            # Success
            register_success(user)
            user_service.db.add(user)
            user_service.db.commit()
            user_service.db.refresh(user)
            inc_login("success")
            sess = session_service.create(user_id=user.id)
            # secure & same_site derived automatically from environment now
            set_session_cookie(response, sess.id)
            logger.info("login.cookie.set", session_id=sess.id)
            log_session_created(user.id, sess.id, demo=False)
            log_login_attempt(email, success=True)
            recorder.record("auth.login.success", user_id=user.id, session_id=sess.id)
            # naive gauge calc (would query active sessions normally) - omitted for simplicity
            gauge_active_sessions(1)
            return UserResponse(data=UserPublic(id=user.id, email=user.email, display_name=getattr(user, "display_name", None)))
    except DuplicateInFlight:
        return JSONResponse(status_code=409, content={"error": "DUPLICATE_SUBMISSION"})
    # Fallback - should not reach here normally
    return _generic_credentials_response()

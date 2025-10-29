"""Registration endpoint (US2 T038-T039).

Provides /auth/register which validates password strength, ensures email
uniqueness, creates user, establishes session cookie, emits metrics & logs.
"""
from fastapi import Depends, Response, HTTPException, status, Request
from fastapi.responses import JSONResponse
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
from app.telemetry.metrics_auth import inc_registration, gauge_active_sessions, inc_login
from app.telemetry.logging_auth import (
    log_registration_attempt,
    log_registration_success,
    log_session_created,
    log_login_attempt,
    log_logout,
)
from app.telemetry.audit_recorder import get_audit_recorder
from app.services.masking import mask_email


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = None


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    display_name: str | None = None


class UserResponse(BaseModel):
    data: UserPublic | None = None
    error: str | None = None


def _weak_password(password: str) -> bool:
    # Simple heuristic: length >=10 and contains 3 character classes
    if len(password) < 10:
        return True
    classes = sum(
        [
            any(c.islower() for c in password),
            any(c.isupper() for c in password),
            any(c.isdigit() for c in password),
            any(not c.isalnum() for c in password),
        ]
    )
    return classes < 3


@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    response: Response,
    user_service: UserService = Depends(get_user_service),
    session_service: SessionService = Depends(get_session_service),
):
    recorder = get_audit_recorder()
    try:
        email = normalize_email(payload.email)
    except ValueError:
        # treat as generic invalid credentials (avoid enumeration) - respond 400
        raise HTTPException(status_code=400, detail={"error": "INVALID_EMAIL"})

    if _weak_password(payload.password):
        raise HTTPException(status_code=400, detail={"error": "WEAK_PASSWORD"})

    # Uniqueness check
    existing = user_service.get_by_email(email)
    if existing:
        log_registration_attempt(email, success=False, failure_reason="EMAIL_EXISTS")
        return JSONResponse(status_code=409, content={"error": "EMAIL_EXISTS"})

    # Create user (assuming model fields first_name/last_name optional -> we map display_name onto first_name)
    user = user_service.create_user(
        email=email,
        first_name=payload.display_name or "",
        last_name="",
        password=payload.password,
    )
    log_registration_attempt(email, success=True, user_id=user.id)
    inc_registration()
    # Auto-login: create session
    sess = session_service.create(user_id=user.id)
    set_session_cookie(response, sess.id)
    log_session_created(user.id, sess.id, demo=False)
    log_registration_success(user.id, email, session_id=sess.id)
    # Audit success (best-effort; ignore if unavailable)
    try:
        recorder.record("auth.register.success", user_id=user.id, session_id=sess.id)
    except Exception:
        pass
    gauge_active_sessions(1)
    # Also increment login success metric for unified attempts tracking
    inc_login("success")
    # FastAPI will serialize the Pydantic model and use declared status_code (201)
    return UserResponse(data=UserPublic(id=user.id, email=user.email, display_name=payload.display_name))


class SessionStatus(BaseModel):
    authenticated: bool
    user_id: str | None = None


@auth_router.get("/session", response_model=SessionStatus)
def session_status(request: Request, session_service: SessionService = Depends(get_session_service)):
    """Lightweight session status endpoint to check if session cookie maps to active session."""
    # Cookie helper already sets 'session_id'; we read it directly
    sess_id = request.cookies.get("session")
    if not sess_id:
        return SessionStatus(authenticated=False)
    sess = session_service.get(sess_id)
    if not sess:
        return SessionStatus(authenticated=False)
    return SessionStatus(authenticated=True, user_id=sess.user_id)


# Identity endpoint for client getIdentity() calls
@auth_router.get("/me", response_model=UserResponse)
def me(request: Request, session_service: SessionService = Depends(get_session_service), user_service: UserService = Depends(get_user_service)):
    sess_id = request.cookies.get("session")
    if not sess_id:
        return UserResponse(data=None)
    sess = session_service.get(sess_id)
    if not sess:
        return UserResponse(data=None)
    user = user_service.get_by_id(sess.user_id)
    if not user:
        return UserResponse(data=None)
    return UserResponse(data=UserPublic(id=user.id, email=user.email, display_name=getattr(user, "display_name", None)))


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@auth_router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response, user_service: UserService = Depends(get_user_service), session_service: SessionService = Depends(get_session_service)):
    email = normalize_email(payload.email)
    user = user_service.authenticate(email=email, password=payload.password)
    if not user:
        log_login_attempt(email, success=False)
        inc_login("failure")
        raise HTTPException(status_code=401, detail={"error": "INVALID_CREDENTIALS"})
    sess = session_service.create(user_id=user.id)
    set_session_cookie(response, sess.id)
    log_session_created(user.id, sess.id, demo=False)
    log_login_attempt(email, success=True, user_id=user.id, session_id=sess.id)
    inc_login("success")
    return UserResponse(data=UserPublic(id=user.id, email=user.email, display_name=getattr(user, "display_name", None)))


@auth_router.post("/logout")
def logout(request: Request, response: Response, session_service: SessionService = Depends(get_session_service)):
    sess_id = request.cookies.get("session")
    if sess_id:
        sess = session_service.get(sess_id)
        if sess:
            session_service.revoke(sess)
            log_logout(sess.user_id, sess_id, success=True)
    from app.services.cookie_helper import clear_session_cookie
    clear_session_cookie(response)
    return {"data": {"success": True}}

"""Authentication API endpoints (renamed to avoid package/module collision)."""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session as SASession
from sqlmodel import Session

from app.schemas.auth import UserRegister, UserLogin, UserPublic, TokenResponse, AuthErrorResponse
from app.services.user import UserService
from app.services.lockout import is_locked, register_failed_attempt, register_success
from app.services.session_service import SessionService
from app.core.dependencies_auth import get_session_service
from app.core.dependencies import get_sync_db_session, get_current_user
from app.core.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def get_user_service(db: SASession | Session = Depends(get_sync_db_session)) -> UserService:
    return UserService(db)


@router.post("/signup", response_model=UserPublic, responses={400: {"model": AuthErrorResponse}})
def signup(payload: UserRegister, service: UserService = Depends(get_user_service)):
    try:
        user = service.create_user(
            email=payload.email,
            first_name=payload.first_name,
            last_name=payload.last_name,
            password=payload.password,
        )
        return UserPublic.model_validate(user)
    except ValueError as ve:
        if str(ve) == "EMAIL_IN_USE":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
        raise


@router.post("/login", response_model=TokenResponse, responses={401: {"model": AuthErrorResponse}})
def login(payload: UserLogin, response: Response, service: UserService = Depends(get_user_service), sessions: SessionService = Depends(get_session_service)):
    # Normalize email for lookup (do not reveal enumeration) - case-insensitive
    email = payload.email.strip().lower()
    user = service.get_by_email(email)
    if not user:
        # Generic failure
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Lockout check
    if is_locked(user):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    auth_user = service.authenticate(email=email, password=payload.password)
    if not auth_user:
        register_failed_attempt(user)
        # Persist mutated user
        service.db.add(user)
        service.db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Success: reset counters
    register_success(user)
    service.db.add(user)
    service.db.commit()

    token = service.create_access_token_for_user(user)

    # Create session record (JWT still primary; cookie for future middleware)
    session = sessions.create(user_id=user.id)
    # Set cookie (placeholder attributes; secure flag conditional on settings)
    response.set_cookie(
        key="session_id",
        value=session.id,
        httponly=True,
        secure=False,  # TODO: set True in production / when behind TLS
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        path="/",
    )

    return TokenResponse(access_token=token, expires_in=settings.ACCESS_TOKEN_EXPIRE_SECONDS)


@router.get("/me", response_model=UserPublic)
def me(current: dict = Depends(get_current_user), service: UserService = Depends(get_user_service)):
    if current["user_id"] == "demo-user":
        from datetime import datetime
        now = datetime.utcnow()
        return UserPublic(
            id="demo-user",
            email="demo@example.com",
            first_name="Demo",
            last_name="User",
            is_active=True,
            is_verified=False,
            created_at=now,
            updated_at=now,
        )
    user = service.get_by_email(current["email"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserPublic.model_validate(user)

__all__ = ["router"]

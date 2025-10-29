"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as SASession
from sqlmodel import Session

from app.schemas.auth import UserRegister, UserLogin, UserPublic, TokenResponse, AuthErrorResponse
from app.services.user import UserService
from app.core.dependencies import get_sync_db_session, get_current_user
from app.core.auth import decode_access_token
from app.core.config import get_settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
settings = get_settings()


def get_user_service(db: SASession | Session = Depends(get_sync_db_session)) -> UserService:
    return UserService(db)


@router.post("/register", response_model=UserPublic, responses={
    400: {"model": AuthErrorResponse},
})
def register(payload: UserRegister, service: UserService = Depends(get_user_service)):
    """Register a new user account."""
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


@router.post("/token", response_model=TokenResponse, responses={
    401: {"model": AuthErrorResponse},
})
def login(payload: UserLogin, service: UserService = Depends(get_user_service)):
    """Authenticate user and return access token."""
    user = service.authenticate(email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = service.create_access_token_for_user(user)
    return TokenResponse(access_token=token, expires_in=settings.ACCESS_TOKEN_EXPIRE_SECONDS)


@router.get("/me", response_model=UserPublic, responses={401: {"model": AuthErrorResponse}})
def me(current: dict = Depends(get_current_user), service: UserService = Depends(get_user_service)):
    """Return current user profile from token or demo user if no auth."""
    # If demo user (no auth), synthesize a public user representation
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
    # For authenticated user, fetch from DB
    user = service.get_by_email(current["email"])
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserPublic.model_validate(user)


__all__ = ["router"]

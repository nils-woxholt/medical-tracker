"""Auth-specific dependency wiring."""

from fastapi import Depends
from sqlalchemy.orm import Session as SASession
from sqlmodel import Session

from app.core.dependencies import get_sync_db_session
from app.services.user import UserService
from app.services.session_service import SessionService
from app.services.lockout import is_locked, register_failed_attempt, register_success
from app.services.email_normalization import normalize_email

def get_user_service(db: SASession | Session = Depends(get_sync_db_session)) -> UserService:
    return UserService(db)

def get_session_service(db: SASession | Session = Depends(get_sync_db_session)) -> SessionService:
    return SessionService(db)

__all__ = [
    "get_user_service",
    "get_session_service",
    "is_locked",
    "register_failed_attempt",
    "register_success",
    "normalize_email",
]
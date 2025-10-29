"""User service layer.

Provides functions for creating users and authenticating credentials.
"""

from typing import Optional
from sqlalchemy.orm import Session as SASession
from sqlmodel import select, Session
import structlog

from app.models.user import User
from app.core.auth import create_password_hash, verify_password, create_access_token
from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class UserService:
    """Service encapsulating user-related operations."""

    def __init__(self, db: SASession | Session):
        self.db = db

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        # sqlmodel Session has .exec; plain SQLAlchemy session uses execute
        if isinstance(self.db, Session):
            return self.db.exec(stmt).first()
        else:
            result = self.db.execute(stmt).scalars().first()
            return result

    def get_by_id(self, user_id: str) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        if isinstance(self.db, Session):
            return self.db.exec(stmt).first()
        else:
            return self.db.execute(stmt).scalars().first()

    # ------------------------------------------------------------------
    # Create user
    # ------------------------------------------------------------------
    def create_user(self, *, email: str, first_name: str, last_name: str, password: str) -> User:
        existing = self.get_by_email(email)
        if existing:
            raise ValueError("EMAIL_IN_USE")

        password_hash = create_password_hash(password)
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        logger.info("User created", user_id=user.id, email=user.email)
        return user

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def authenticate(self, *, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

    def create_access_token_for_user(self, user: User) -> str:
        return create_access_token({"sub": user.email, "user_id": user.id})


__all__ = ["UserService"]

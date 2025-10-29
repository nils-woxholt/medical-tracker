"""Session model for tracking authenticated user sessions.

Implements idle timeout and revocation semantics.
"""

from datetime import datetime, timedelta
from typing import Optional, ClassVar
from uuid import uuid4

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import String, DateTime, Boolean, ForeignKey, func


class Session(SQLModel, table=True):
    __tablename__: ClassVar[str] = "sessions"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        sa_column=Column(String(36), primary_key=True, nullable=False),
        description="Unique session identifier (UUID)"
    )

    user_id: str = Field(
        sa_column=Column(String(36), ForeignKey("users.id"), nullable=False, index=True),
        description="Associated user id"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, default=func.now()),
        description="Session creation time"
    )

    last_activity_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False, default=func.now()),
        description="Last activity timestamp"
    )

    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(minutes=30),
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Idle timeout expiration timestamp"
    )

    revoked_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="If set, session is revoked"
    )

    demo: bool = Field(
        default=False,
        sa_column=Column(Boolean(), nullable=False, default=False),
        description="True if this is a demo session"
    )

    def touch(self) -> None:
        """Update last activity and extend expiry (rolling)."""
        now = datetime.utcnow()
        self.last_activity_at = now
        # Extend expiry rolling window
        self.expires_at = now + timedelta(minutes=30)

    def revoke(self) -> None:
        if self.revoked_at is None:
            self.revoked_at = datetime.utcnow()

__all__ = ["Session"]
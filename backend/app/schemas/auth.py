"""Authentication schemas.

These Pydantic models define request and response payloads for
registration, login (token issuance) and current user retrieval.

Separated from `app.models.user` (SQLModel) to keep transport layer
contracts decoupled from persistence definitions.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

# NOTE: Feature 003-implement-login-ui introduces cookie-based identity retrieval and masked identity logic.
# New schemas below (IdentityResponse, LoginResult) are additive and do not remove existing token models.


class UserRegister(BaseModel):
        """Payload for user registration (lean mode).

        Lean Mode Adjustment (Option A):
        - `first_name` and `last_name` now optional to allow a single display name field in UI.
        - Added optional `display_name` field; when names are absent they are derived from
            `display_name` (split on first space) or from email local part.
        - Password minimum length retained (>=10) per FR-004.
        """
        email: EmailStr = Field(examples=["user@example.com"])
        first_name: str | None = Field(default=None, min_length=1, max_length=100, examples=["Jane"])
        last_name: str | None = Field(default=None, min_length=1, max_length=100, examples=["Doe"])
        display_name: str | None = Field(default=None, min_length=1, max_length=150, examples=["Jane Doe"])
        password: str = Field(min_length=10, max_length=255, examples=["StrongPass123!#"])  # upgraded min length


class UserLogin(BaseModel):
    """Payload for user login (token request).

    Feature update: minimum password length raised to 10 to match registration.
    """
    email: EmailStr = Field(examples=["user@example.com"])
    password: str = Field(min_length=10, max_length=255, examples=["StrongPass123!#"])


class UserPublic(BaseModel):
    """Public user representation exposed via API."""
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    """Access token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Lifetime in seconds of the access token")


class IdentityResponse(BaseModel):
    """Minimal identity returned from `/auth/me` (feature 003).

    Provides masked display when display_name not set while avoiding exposure of raw email.
    """
    user_id: str
    display_name: str | None = None
    masked_identity: str = Field(description="Masked email if display_name absent (first 3 chars + ellipsis + domain)")


class LoginResult(BaseModel):
    """Feature-specific unified response for login/register when not returning raw token.

    Present for future adaptation when shifting from bearer token transport to cookie-only sessions.
    """
    identity: IdentityResponse
    # token fields intentionally optional for cookie mode
    access_token: str | None = None
    expires_in: int | None = None


class AuthErrorResponse(BaseModel):
    """Standardized error shape for auth endpoints when granular auth-specific messaging is helpful."""
    error: str = Field(examples=["INVALID_CREDENTIALS", "EMAIL_IN_USE"])
    message: str
    detail: Optional[str] = None


__all__ = [
    "UserRegister",
    "UserLogin",
    "UserPublic",
    "TokenResponse",
    "AuthErrorResponse",
    "IdentityResponse",
    "LoginResult",
]

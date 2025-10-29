"""Identity endpoint implementation.

Replaces earlier stub with functional session-based identity resolution so
integration tests for login flow can verify authenticated state via `/auth/me`.

Behavior:
 - Reads session cookie (name: `session`).
 - Looks up session via SessionService; if missing/invalid returns 401.
 - Fetches user and returns same envelope shape as other auth endpoints:
     {"data": {"id": ..., "email": ..., "display_name": ...}, "error": null}
 - Emits a lightweight structured log event.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, HTTPException, Request, status
from pydantic import BaseModel
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["auth"], prefix="/auth")


class IdentityUser(BaseModel):
    id: str
    email: str
    display_name: str | None = None


class IdentityEnvelope(BaseModel):
    data: IdentityUser | None = None
    error: str | None = None


from app.core.dependencies_auth import get_session_service, get_user_service
from app.services.session_service import SessionService
from app.services.user import UserService


@router.get("/me", response_model=IdentityEnvelope, summary="Get current user identity")
def get_identity(request: Request, response: Response, session_service: SessionService = Depends(get_session_service), user_service: UserService = Depends(get_user_service)) -> IdentityEnvelope:
    sess_id = request.cookies.get("session")
    if not sess_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    sess = session_service.get(sess_id)
    if not sess:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = user_service.get_by_id(sess.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    logger.info("identity_lookup", user_id=user.id, email=user.email)
    return IdentityEnvelope(data=IdentityUser(id=user.id, email=user.email, display_name=getattr(user, "display_name", None)))


__all__ = ["router", "IdentityEnvelope", "IdentityUser"]
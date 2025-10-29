"""Session status endpoint (T040)."""

from datetime import datetime
from fastapi import Depends, HTTPException, status
import structlog
from fastapi import Response, Request
from pydantic import BaseModel

from app.api.auth import auth_router
from app.core.dependencies_auth import get_session_service, get_user_service
from app.telemetry.metrics_auth import inc_session_status
from app.services.cookie_helper import COOKIE_NAME, clear_session_cookie
from app.services.session_service import SessionService
from app.services.user import UserService
logger = structlog.get_logger(__name__)


class SessionInfo(BaseModel):
    id: str
    demo: bool
    last_activity_at: datetime
    expires_at: datetime


class UserInfo(BaseModel):
    id: str
    email: str


class SessionStatusResponse(BaseModel):
    # data envelope holds: authenticated: bool, user: {id,email}|None, session: {...}|None
    data: dict | None = None
    error: dict | None = None


@auth_router.get("/session", response_model=SessionStatusResponse)
def session_status(
    request: Request,
    response: Response,
    session_service: SessionService = Depends(get_session_service),
    user_service: UserService = Depends(get_user_service),
):
    # Use standardized cookie name (COOKIE_NAME) set by cookie_helper
    session_id = request.cookies.get(COOKIE_NAME)
    logger.info("session.request", has_cookie=bool(session_id), session_id=session_id)
    if not session_id:
        # No cookie -> unauthenticated. We still return 401 to preserve existing contract semantics
        # (frontend helper already maps non-OK to authenticated False).
        inc_session_status(False)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="NO_SESSION")
    session = session_service.get(session_id)
    logger.info("session.lookup", found=bool(session))
    if not session or session.revoked_at is not None:
        # Clear cookie if present but invalid
        clear_session_cookie(response)
        inc_session_status(False)
        return SessionStatusResponse(data={"authenticated": False, "user": None, "session": None})
    # Idle timeout check (enforcement will also live in middleware T042)
    now = datetime.utcnow()
    if session.expires_at < now:
        session_service.revoke(session)
        clear_session_cookie(response)
        inc_session_status(False)
        return SessionStatusResponse(data={"authenticated": False, "user": None, "session": None})
    user = user_service.get_by_id(session.user_id)
    if not user:
        inc_session_status(False)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="NO_USER")
    inc_session_status(True)
    logger.info("session.success", user_id=user.id, session_id=session.id)
    return SessionStatusResponse(
        data={
            "authenticated": True,
            "user": UserInfo(id=user.id, email=user.email).model_dump(),
            "session": SessionInfo(
                id=session.id,
                demo=session.demo,
                last_activity_at=session.last_activity_at,
                expires_at=session.expires_at,
            ).model_dump(),
        }
    )

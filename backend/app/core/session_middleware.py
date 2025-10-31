"""Session extraction & idle timeout enforcement middleware (T025).

Relocated to app.core.session_middleware to avoid name shadowing with the existing
`middleware.py` module.
"""
from __future__ import annotations

from datetime import datetime
from fastapi import Request, Response
from starlette.types import ASGIApp
from app.services.cookie_helper import COOKIE_NAME
from app.core.dependencies import get_sync_db_session
from app.services.session_service import SessionService
from app.models.session import Session as SessionModel
from app.telemetry.logging_auth import log_session_created

class SessionMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        session_id = request.cookies.get(COOKIE_NAME)
        request.state.session = None
        request.state.session_id = None
        # Preserve any existing user_id (e.g., set by auth middleware) but prefer session user
        existing_user_id = getattr(request.state, "user_id", None)
        if session_id:
            db = next(get_sync_db_session())  # generator dependency pattern
            try:
                service = SessionService(db)
                sess: SessionModel | None = service.get(session_id)
                if sess and sess.revoked_at is None:
                    # Idle timeout check
                    if datetime.utcnow() > sess.expires_at:
                        service.revoke(sess)
                    else:
                        service.touch(sess)
                        request.state.session = sess
                        request.state.session_id = sess.id
                        request.state.user_id = sess.user_id
                        if existing_user_id and existing_user_id != sess.user_id:
                            # In rare cases bearer & session mismatch; prefer session user id
                            request.state.user_id = sess.user_id
            finally:
                try:
                    db.close()
                except Exception:
                    pass
        if not getattr(request.state, "user_id", None):
            # Ensure attribute exists even if unauthenticated
            request.state.user_id = existing_user_id

        async def send_wrapper(message):
            await send(message)

        await self.app(scope, receive, send_wrapper)

__all__ = ["SessionMiddleware"]

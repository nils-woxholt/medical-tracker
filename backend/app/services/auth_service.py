"""Auth service high-level operations (US3 T053).

Provides cohesive operations spanning user + session domain (logout, etc.).
Currently minimal: logout revokes session if present; idempotent semantics.
"""
from __future__ import annotations
from typing import Optional

from app.services.session_service import SessionService
from app.services.cookie_helper import COOKIE_NAME
from fastapi import Request
from app.models.session import Session as SessionModel

class AuthService:
    def __init__(self, session_service: SessionService):
        self.session_service = session_service

    def get_session(self, session_id: str) -> Optional[SessionModel]:
        return self.session_service.get(session_id)

    def logout(self, session: SessionModel | None) -> bool:
        """Revoke session if active.

        Returns True if a revocation occurred or session absent (idempotent success).
        """
        if not session or session.revoked_at is not None:
            return True
        self.session_service.revoke(session)
        return True

__all__ = ["AuthService"]

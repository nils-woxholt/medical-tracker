"""Logout endpoint (US3 T052-T053).

Contract expectations (T049 tests):
 - POST /auth/logout returns 200 always (idempotent)
 - If no valid session present: still 200 with no error field (graceful)
 - If session valid: revoke + clear cookie and emit metrics/logs
"""

from fastapi import Depends, Response, Request, status
from fastapi.responses import JSONResponse
from app.api.auth import auth_router
from app.core.dependencies_auth import get_session_service
from app.services.session_service import SessionService
from app.services.cookie_helper import clear_session_cookie, COOKIE_NAME
from app.telemetry.audit_recorder import get_audit_recorder
from app.telemetry.logging_auth import log_logout
from app.telemetry.metrics_auth import inc_logout, inc_logout_failure


@auth_router.post("/logout")
def logout(request: Request, response: Response, session_service: SessionService = Depends(get_session_service)):
    """Revoke current session (if any) and clear cookie.

    Always returns 200 with envelope {data: {success: True}, error: None} for idempotency.
    """
    session_id = request.cookies.get(COOKIE_NAME)
    recorder = get_audit_recorder()
    if not session_id:
        clear_session_cookie(response)
        log_logout(user_id=None, session_id=None, success=True)
        return JSONResponse(status_code=200, content={"data": {"success": True}, "error": None})

    sess = session_service.get(session_id)
    if not sess or sess.revoked_at is not None:
        clear_session_cookie(response)
        log_logout(user_id=sess.user_id if sess else None, session_id=session_id, success=True)
        return JSONResponse(status_code=200, content={"data": {"success": True}, "error": None})

    try:
        session_service.revoke(sess)
        clear_session_cookie(response)
        inc_logout()
        log_logout(sess.user_id, sess.id, success=True)
        recorder.record("auth.logout", user_id=sess.user_id, session_id=sess.id)
        return JSONResponse(status_code=200, content={"data": {"success": True}, "error": None})
    except Exception:
        inc_logout_failure()
        log_logout(sess.user_id, sess.id, success=False)
        return JSONResponse(status_code=200, content={"data": {"success": True}, "error": None})

"""Demo access endpoint (T041, T049)."""

from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Response, status
from pydantic import BaseModel

from app.api.auth import auth_router
from app.core.dependencies_auth import get_session_service, get_user_service
from app.services.session_service import SessionService
from app.services.user import UserService
from app.services.cookie_helper import set_session_cookie
from app.telemetry.audit_recorder import get_audit_recorder
from app.telemetry.logging_auth import log_session_created
from app.telemetry.metrics_auth import inc_login, gauge_active_sessions, inc_demo_session_created
from app.services.rate_limit import allow as rate_allow
from app.telemetry.metrics import metrics_registry


class DemoResponse(BaseModel):
    data: dict | None = None
    error: dict | None = None


DEMO_EMAIL = "demo@example.com"


@auth_router.post("/demo", response_model=DemoResponse)
def start_demo(
    response: Response,
    user_service: UserService = Depends(get_user_service),
    session_service: SessionService = Depends(get_session_service),
):
    # Rate limit demo session creations (avoid abuse creating excessive demo users/sessions)
    if not rate_allow("demo:start"):
        metrics_registry.security_events_total.labels(event_type="rate_limit", severity="low").inc()
        raise HTTPException(status_code=429, detail="TOO_MANY_ATTEMPTS")
    # Ensure demo user exists (minimal creation if absent)
    user = user_service.get_by_email(DEMO_EMAIL)
    if not user:
        # Create with random password that won't be used for login path
        user = user_service.create_user(email=DEMO_EMAIL, first_name="Demo", last_name="User", password="DemoTemp123")
    # Create demo session
    session = session_service.create(user_id=user.id, demo=True)
    # Hardened cookie defaults apply automatically
    set_session_cookie(response, session.id)
    log_session_created(user.id, session.id, demo=True)
    recorder = get_audit_recorder()
    recorder.record("auth.demo.start", user_id=user.id, session_id=session.id)
    inc_login("success")
    inc_demo_session_created(True)
    gauge_active_sessions(1)
    return DemoResponse(
        data={
            "user": {"id": user.id, "email": user.email},
            "session": {"id": session.id, "demo": True, "expires_at": session.expires_at.isoformat() + "Z"},
        }
    )

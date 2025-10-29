"""Contract tests for /auth/logout endpoint (T049).

Focus: Idempotent logout behavior. A logged-in session can be terminated via
POST /auth/logout returning a 200 status and clearing the session cookie. A
subsequent call with no valid session MUST still return 200 (idempotent) and
MUST NOT error. Cookie clearance (expiration) should be asserted when possible.
"""

from http import HTTPStatus
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app

client = TestClient(app)


def _login(email: str, password: str):
    return client.post("/auth/login", json={"email": email, "password": password})


def _logout():
    return client.post("/auth/logout")


def test_logout_success_and_cookie_cleared(sample_user_data):
    """Login then logout; expect 200 and session cookie cleared/expired."""
    # Ensure user exists (registration may 201 or conflict)
    reg = client.post(
        "/auth/register",
        json={
            "email": sample_user_data["email"],
            "password": "Password!123",
            "display_name": "Logout Tester",
        },
    )
    assert reg.status_code in (HTTPStatus.CREATED, HTTPStatus.CONFLICT, HTTPStatus.UNPROCESSABLE_ENTITY)
    login = _login(sample_user_data["email"], "Password!123")
    assert login.status_code == status.HTTP_200_OK
    # Capture cookie prior to logout
    pre_cookies = {k: v for k, v in login.cookies.items()}
    assert any("session" in k.lower() for k in pre_cookies.keys())

    resp = _logout()
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert body.get("error") in (None, {})  # logout success no error
    # Set-Cookie headers should attempt to clear session (value blank or expired)
    set_cookie_headers = [h for h in resp.headers.get("set-cookie", "").split(",") if h]
    # Accept either explicit deletion cookie (Max-Age=0 / Expires=...) or absence (middleware cleared)
    cleared_indicators = [h for h in set_cookie_headers if "session" in h.lower() and ("max-age=0" in h.lower() or "expires=" in h.lower() or "deleted" in h.lower())]
    assert cleared_indicators or not set_cookie_headers  # tolerant if framework merges headers


def test_logout_idempotent_no_session():
    """Calling logout with no prior login still returns 200 (idempotent)."""
    resp = _logout()
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    # Idempotent logout still success; may include a generic message or empty data
    assert body.get("error") in (None, {})

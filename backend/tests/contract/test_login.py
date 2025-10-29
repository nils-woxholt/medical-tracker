"""Contract tests for /auth/login endpoint (T017).

Focus: Success, failure (generic), lockout response shape.
"""

from fastapi.testclient import TestClient
import pytest
from fastapi import status

from app.main import app

client = TestClient(app)


def _login(email: str, password: str):
    return client.post("/auth/login", json={"email": email, "password": password})


@pytest.mark.contract
def test_login_failure_generic():
    resp = _login("unknown@example.com", "wrongpass123")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
    body = resp.json()
    # Contract: generic error only
    assert body.get("error") == "INVALID_CREDENTIALS"


@pytest.mark.contract
def test_login_success(sample_user_data):
    # Attempt registration first if endpoint present
    reg_resp = client.post("/auth/register", json={"email": sample_user_data["email"], "password": "Password!123", "display_name": "Test User"})
    # Registration now returns 201 Created on success; allow 409 if user already exists
    assert reg_resp.status_code in (201, 409)
    resp = _login(sample_user_data["email"], "Password!123")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json().get("data")
    assert data is not None
    assert data["email"].lower() == sample_user_data["email"].lower()
    assert "error" not in resp.json() or resp.json()["error"] is None
    # Session cookie must be present
    cookies = resp.cookies
    assert any(k for k in cookies.keys() if "session" in k.lower())


@pytest.mark.contract
def test_login_locked_account(sample_user_data):
    # Ensure user exists via register endpoint
    client.post("/auth/register", json={"email": sample_user_data["email"], "password": "Password!123", "display_name": "Lock User"})
    user_email = sample_user_data["email"]
    # Fail attempts until locked
    for _ in range(5):  # threshold from lockout config
        _login(user_email, "WrongPassword999!")
    # Next attempt should yield 423
    locked_resp = _login(user_email, "WrongPassword999!")
    assert locked_resp.status_code == status.HTTP_423_LOCKED
    body = locked_resp.json()
    err_field = body.get("error")
    is_direct_code = err_field == "ACCOUNT_LOCKED"
    is_nested_code = isinstance(err_field, dict) and err_field.get("error") == "ACCOUNT_LOCKED"
    assert is_direct_code or is_nested_code
    # lock_expires_at may be nested depending on implementation detail, accept either
    lock_error_obj = err_field if isinstance(err_field, dict) else {}
    lock_expires = body.get("lock_expires_at") or lock_error_obj.get("lock_expires_at")
    assert lock_expires is not None
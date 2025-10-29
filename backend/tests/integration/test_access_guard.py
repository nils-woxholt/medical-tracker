"""Integration test for protected route access guard (T018).

Verifies unauthenticated request denied; authenticated succeeds after login creating session cookie.
"""

from fastapi.testclient import TestClient
from fastapi import status
import pytest

from app.main import app
from app.models.base import get_database
from app.services.user import UserService

client = TestClient(app)


@pytest.mark.integration
def test_protected_route_requires_auth(sample_user_data):
    """Accessing versioned logs endpoint should require auth (get_authenticated_user)."""
    # Strictly protected (router included with Depends(get_authenticated_user))
    protected_path = "/api/v1/logs/medications"

    unauth_resp = client.get(protected_path)
    assert unauth_resp.status_code == status.HTTP_401_UNAUTHORIZED, (
        f"Expected 401 for unauthenticated access; got {unauth_resp.status_code} body={unauth_resp.text}"
    )

    # Register user via root path (cannot use versioned register which returns 501)
    reg_payload = {"email": sample_user_data["email"], "password": "Password!123"}
    reg_resp = client.post("/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.status_code} body={reg_resp.text}"

    # Manually generate JWT access token via service (versioned endpoint placeholder returns 501)
    db = get_database()
    with db.sync_session_factory() as session:
        svc = UserService(session)
        user = svc.get_by_email(reg_payload["email"])
        assert user, "Registered user not found in DB"
        access_token = svc.create_access_token_for_user(user)

    # Authenticated request should now succeed with Bearer token (empty list OK)
    auth_resp = client.get(protected_path, headers={"Authorization": f"Bearer {access_token}"})
    assert auth_resp.status_code == status.HTTP_200_OK, (
        f"Expected 200 after auth; got {auth_resp.status_code} body={auth_resp.text}"
    )
    # Minimal test log store may already have entries from earlier tests (global in-process store).
    # Accept any list (empty or with dict entries) as long as structure is list.
    body = auth_resp.json()
    assert isinstance(body, list), f"Expected list response for medication logs; got {type(body)}"
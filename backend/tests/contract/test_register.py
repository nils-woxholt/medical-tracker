"""Contract tests for /auth/register endpoint (T035).

Covers success (201) and conflict (409) responses using existing application
fixtures. These tests assert shape of the envelope and generic error semantics.
"""
from http import HTTPStatus
from typing import Callable
import re

from fastapi.testclient import TestClient

EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


def test_register_success(sync_client: TestClient, db_session):  # use sync client fixture
    payload = {"email": "new_user@example.com", "password": "StrongPass123!", "display_name": "New User"}
    resp = sync_client.post("/auth/register", json=payload)
    assert resp.status_code == HTTPStatus.CREATED
    body = resp.json()
    assert "data" in body and body["data"] is not None
    user = body["data"]
    assert "id" in user and isinstance(user["id"], str)
    assert EMAIL_RE.match(user.get("email", ""))
    assert user.get("display_name") == "New User"
    # error should be absent
    assert body.get("error") in (None, {})


def test_register_conflict(sync_client: TestClient, db_session):
    # Pre-create user (depends on a helper fixture or direct DB insert)
    # For simplicity, attempt registering same email twice
    payload = {"email": "dup_user@example.com", "password": "StrongPass123!"}
    first = sync_client.post("/auth/register", json=payload)
    assert first.status_code == HTTPStatus.CREATED
    second = sync_client.post("/auth/register", json=payload)
    assert second.status_code == HTTPStatus.CONFLICT
    body = second.json()
    assert body.get("error") == "EMAIL_EXISTS"

"""Integration tests for login endpoint (T029)."""

from datetime import timedelta, datetime
import pytest
from fastapi import status
from httpx import AsyncClient

from app.main import app  # assuming app exposes FastAPI instance
from app.core.auth import create_password_hash
from app.models.user import User
from app.services.lockout import LOCK_THRESHOLD
from app.core.dependencies import get_sync_db_session


@pytest.fixture
def db_session():
    sess_gen = get_sync_db_session()
    db = next(sess_gen)
    try:
        yield db
    finally:
        try:
            next(sess_gen)
        except StopIteration:
            pass


@pytest.fixture
def user(db_session):
    u = User(
        email="login_test@example.com",
        first_name="Login",
        last_name="Tester",
        password_hash=create_password_hash("CorrectPass123"),
        failed_attempts=0,
        lock_until=None,
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.mark.asyncio
async def test_login_success_sets_cookie(user):
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/auth/login", json={"email": user.email, "password": "CorrectPass123"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["data"]["email"] == user.email
        # Cookie presence
        assert any(c for c in resp.cookies.jar if c.name == "session")


@pytest.mark.asyncio
async def test_login_unknown_email_enumeration_resistant():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/auth/login", json={"email": "unknown@example.com", "password": "Whatever123"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        body = resp.json()
        assert body.get("error") == "INVALID_CREDENTIALS" or body.get("detail", {}).get("error") == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_wrong_password(user):
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/auth/login", json={"email": user.email, "password": "WrongPass123"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        body = resp.json()
        assert body.get("error") == "INVALID_CREDENTIALS" or body.get("detail", {}).get("error") == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_lockout_after_threshold(user, db_session):
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Perform threshold attempts
        for _ in range(LOCK_THRESHOLD):
            await client.post("/auth/login", json={"email": user.email, "password": "WrongPass123"})
        # Attempt again should yield lock (423)
        locked_resp = await client.post("/auth/login", json={"email": user.email, "password": "WrongPass123"})
        assert locked_resp.status_code == 423
        data = locked_resp.json()
        assert data.get("error") == "ACCOUNT_LOCKED" or data.get("detail", {}).get("error") == "ACCOUNT_LOCKED"
        assert "lock_expires_at" in data or "lock_expires_at" in data.get("detail", {})

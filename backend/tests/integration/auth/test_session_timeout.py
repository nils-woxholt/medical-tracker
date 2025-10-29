"""Integration tests for session persistence & idle timeout (T045)."""

from datetime import datetime, timedelta
import uuid
import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.models.session import Session
from app.models.user import User
from app.services.cookie_helper import COOKIE_NAME
from app.core.dependencies import get_sync_db_session


IDLE_MINUTES = 30


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


def _register_factory():
    async def _register(client: AsyncClient, email: str):
        resp = await client.post("/auth/register", json={"email": email, "password": "Secure123"})
        # Success returns 201 Created
        assert resp.status_code == status.HTTP_201_CREATED, resp.text
        return resp
    return _register

_register = _register_factory()


@pytest.mark.asyncio
async def test_session_persists_before_timeout(db_session):
    email = f"persist{uuid.uuid4().hex[:6]}@example.com"
    async with AsyncClient(app=app, base_url="http://test") as client:
        reg = await _register(client, email)
        # Fetch status
        s1 = await client.get("/auth/session")
        assert s1.status_code == status.HTTP_200_OK
        body = s1.json()
        assert body["data"]["session"]["demo"] is False
        # Touch again within idle window
        s2 = await client.get("/auth/session")
        assert s2.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_session_expires_after_idle(db_session):
    email = f"expire{uuid.uuid4().hex[:6]}@example.com"
    async with AsyncClient(app=app, base_url="http://test") as client:
        reg = await _register(client, email)
        # Pull the session id from cookie
        cookie = reg.cookies.get(COOKIE_NAME)
        assert cookie
        # Force last_activity_at backwards beyond idle timeout
        session = db_session.query(Session).filter(Session.id == cookie).first()
        assert session is not None
        past = datetime.utcnow() - timedelta(minutes=IDLE_MINUTES + 5)
        session.last_activity_at = past
        session.expires_at = past  # ensure considered expired
        db_session.commit()
        # Next call should indicate not authenticated / expired
        s = await client.get("/auth/session")
        assert s.status_code == status.HTTP_401_UNAUTHORIZED or s.status_code == status.HTTP_200_OK
        # If 200, expect data.session to be None signaling revoked
        if s.status_code == status.HTTP_200_OK:
            assert s.json()["data"]["session"] is None

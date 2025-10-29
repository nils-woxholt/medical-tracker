"""Integration tests for registration endpoint (T036)."""

from uuid import uuid4
import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.core.auth import verify_password
from app.models.user import User
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


@pytest.mark.asyncio
async def test_register_success(db_session):
    email = f"user{uuid4().hex[:6]}@example.com"
    payload = {"email": email, "password": "Secure123", "first_name": "Test", "last_name": "User"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/auth/register", json=payload)
    # Endpoint returns 201 Created on successful registration
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    data = resp.json()["data"]
    assert data["email"] == email
    # confirm user in db
    user = db_session.query(User).filter(User.email == email).first()
    assert user is not None
    assert verify_password("Secure123", user.password_hash)


@pytest.mark.asyncio
async def test_register_email_in_use(db_session):
    email = f"dup{uuid4().hex[:6]}@example.com"
    payload = {"email": email, "password": "Secure123", "first_name": "A", "last_name": "B"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp1 = await client.post("/auth/register", json=payload)
        assert resp1.status_code == status.HTTP_201_CREATED
        resp2 = await client.post("/auth/register", json=payload)
    assert resp2.status_code == status.HTTP_409_CONFLICT
    body = resp2.json()
    # Error handler maps 409 to standardized shape without 'detail'; assert message content.
    # Allow fallback to 'detail' if future handler adds it.
    assert body.get("message") == "EMAIL_IN_USE" or body.get("detail") == "EMAIL_IN_USE"


@pytest.mark.asyncio
async def test_register_password_policy():
    email = f"pw{uuid4().hex[:6]}@example.com"
    bad_payload = {"email": email, "password": "short", "first_name": "X", "last_name": "Y"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/auth/register", json=bad_payload)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    body = resp.json()
    assert body.get("detail") in {"PASSWORD_TOO_SHORT", "PASSWORD_WEAK"}


@pytest.mark.asyncio
async def test_register_email_normalization(db_session):
    raw_email = f"MiXeD{uuid4().hex[:4]}@Example.COM"
    payload = {"email": raw_email, "password": "Secure123", "first_name": "Norm", "last_name": "Case"}
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    stored_email = db_session.query(User).filter(User.email == raw_email.lower()).first()
    assert stored_email is not None

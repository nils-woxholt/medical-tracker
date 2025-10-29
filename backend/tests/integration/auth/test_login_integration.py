"""Integration tests for login flow (renamed to avoid basename collision with contract tests)."""

import pytest
import time
from httpx import AsyncClient

@pytest.mark.anyio
async def test_login_success_flow(async_client: AsyncClient):
    # Register user first
    email = f"login_int_{int(time.time()*1000)}@example.com"
    r = await async_client.post("/auth/register", json={"email": email, "password": "ValidPass123!", "display_name": "Di"})
    assert r.status_code == 201
    # Explicit logout to clear auto-login
    await async_client.post("/auth/logout")
    # Login
    r2 = await async_client.post("/auth/login", json={"email": email, "password": "ValidPass123!"})
    assert r2.status_code == 200, r2.text
    # Identity endpoint should now resolve
    me = await async_client.get("/auth/me")
    assert me.status_code == 200
    body = me.json()
    data = body.get("data") or body
    assert data["email"] == email

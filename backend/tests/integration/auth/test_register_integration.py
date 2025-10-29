"""Integration tests for registration flow (renamed to avoid basename collision)."""

import pytest
import time
from httpx import AsyncClient

@pytest.mark.anyio
async def test_register_conflict(async_client: AsyncClient):
    email = f"reg_int_{int(time.time()*1000)}@example.com"
    r1 = await async_client.post("/auth/register", json={"email": email, "password": "ValidPass123!", "display_name": "A"})
    assert r1.status_code == 201
    r2 = await async_client.post("/auth/register", json={"email": email, "password": "ValidPass123!", "display_name": "B"})
    assert r2.status_code == 409

"""Integration tests for demo session isolation (T046)."""

import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app
from app.services.cookie_helper import COOKIE_NAME


@pytest.mark.asyncio
async def test_demo_session_creation():
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/auth/demo")
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["data"]["session"]["demo"] is True
        assert body["data"]["user"]["email"].startswith("demo@") or body["data"]["user"]["email"].endswith("demo.local")

        # Fetch session status
        status_resp = await client.get("/auth/session")
        assert status_resp.status_code == status.HTTP_200_OK
        status_body = status_resp.json()
        assert status_body["data"]["session"]["demo"] is True

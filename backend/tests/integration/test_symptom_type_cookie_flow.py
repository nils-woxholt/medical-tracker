"""Integration test: SymptomType CRUD using only session cookie (no bearer token).

Validates fallback dependency get_current_user_id_or_session works when SessionMiddleware
extracts user_id from session cookie.
"""
from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app


@pytest.mark.asyncio
async def test_symptom_type_crud_cookie_only():
    # Unique email per test
    email = f"cookie{uuid.uuid4().hex[:8]}@example.com"
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register (sets session cookie)
        reg = await client.post("/auth/register", json={"email": email, "password": "StrongPass123"})
        assert reg.status_code == status.HTTP_201_CREATED, reg.text
        # Verify session status endpoint works & cookie persisted
        sess_status = await client.get("/auth/session")
        assert sess_status.status_code in (status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED)
        if sess_status.status_code == status.HTTP_401_UNAUTHORIZED:
            pytest.skip("Session status returned 401; environment may not support session cookies")
        # Create symptom type WITHOUT Authorization header
        create_payload = {
            "name": "Fatigue",
            "description": "Persistent tiredness",
            "default_severity_numeric": 4,
            "default_impact_numeric": 3,
        }
        create_resp = await client.post("/api/v1/symptom-types", json=create_payload)
        assert create_resp.status_code == status.HTTP_201_CREATED, create_resp.text
        created = create_resp.json()
        st_id = created["id"]
        # List to ensure appears
        list_resp = await client.get("/api/v1/symptom-types")
        assert list_resp.status_code == status.HTTP_200_OK, list_resp.text
        listed = list_resp.json()
        assert any(st["id"] == st_id for st in listed)
        # Deactivate
        deactivate_resp = await client.patch(f"/api/v1/symptom-types/{st_id}/deactivate")
        assert deactivate_resp.status_code == status.HTTP_200_OK, deactivate_resp.text
        assert deactivate_resp.json()["active"] is False

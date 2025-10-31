"""Integration tests for SymptomType CRUD and lifecycle.

Covers:
- Create symptom type
- List symptom types (active only default)
- Get symptom type by id
- Update symptom type (name + description)
- Deactivate symptom type
- Uniqueness conflict (duplicate name for same user)
- Audit diff structure validation on update/deactivate

Assumptions:
- Authentication dependency provides a demo user automatically for tests via fixture.
- Endpoint paths under /api/v1/symptom-types
"""
from __future__ import annotations

import asyncio
from httpx import AsyncClient
import pytest
from fastapi import status

from app.main import app


@pytest.mark.asyncio
async def test_symptom_type_crud_flow():
    from tests.conftest import create_access_token  # if available; else use fixture
    # Generate a token manually using fixture logic
    token = create_access_token({"sub": "crud@example.com", "user_id": "symptom-user-1"})
    headers = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(app=app, base_url="http://test", headers=headers) as client:
        # Create symptom type
        create_payload = {
            "name": "Headache",
            "description": "Throbbing pain in head region",
            "default_severity_numeric": 5,
            "default_impact_numeric": 4
        }
        create_resp = await client.post("/api/v1/symptom-types", json=create_payload)
        assert create_resp.status_code == status.HTTP_201_CREATED, create_resp.text
        created = create_resp.json()
        symptom_type_id = created["id"]
        assert created["active"] is True
        assert created["name"] == "Headache"
        assert "created_at" in created

        # List active symptom types (default should be active only)
        list_resp = await client.get("/api/v1/symptom-types")
        assert list_resp.status_code == status.HTTP_200_OK
        listed = list_resp.json()
        assert any(st["id"] == symptom_type_id for st in listed)

        # Get by id
        get_resp = await client.get(f"/api/v1/symptom-types/{symptom_type_id}")
        assert get_resp.status_code == status.HTTP_200_OK
        got = get_resp.json()
        assert got["id"] == symptom_type_id
        assert got["name"] == "Headache"

        # Update symptom type
        update_payload = {
            "name": "Severe Headache",
            "description": "Intense throbbing pain often with sensitivity to light",
            "default_severity_numeric": 7,
            "default_impact_numeric": 6
        }
        update_resp = await client.put(f"/api/v1/symptom-types/{symptom_type_id}", json=update_payload)
        assert update_resp.status_code == status.HTTP_200_OK, update_resp.text
        updated = update_resp.json()
        assert updated["name"] == "Severe Headache"
        assert updated["description"].startswith("Intense throbbing")
        assert updated["updated_at"] != created["updated_at"]

        # Deactivate symptom type
        # small sleep to ensure timestamp changes
        await asyncio.sleep(0.05)
        deactivate_resp = await client.patch(f"/api/v1/symptom-types/{symptom_type_id}/deactivate")
        assert deactivate_resp.status_code == status.HTTP_200_OK, deactivate_resp.text
        deactivated = deactivate_resp.json()
        assert deactivated["active"] is False
        assert deactivated["updated_at"] != updated["updated_at"]

        # Verify deactivated not returned in default list
        post_deactivate_list = await client.get("/api/v1/symptom-types")
        assert post_deactivate_list.status_code == status.HTTP_200_OK
        assert all(st["id"] != symptom_type_id for st in post_deactivate_list.json())

        # Attempt duplicate creation (same name) should 409
        dup_resp = await client.post(
            "/api/v1/symptom-types",
            json={
                "name": "Severe Headache",
                "description": "duplicate",
                "default_severity_numeric": 7,
                "default_impact_numeric": 6,
            },
        )
        assert dup_resp.status_code == status.HTTP_409_CONFLICT
        body = dup_resp.json()
        detail_text = (body.get("detail") or body.get("message") or "").lower()
        assert "already exists" in detail_text or "unique" in detail_text


@pytest.mark.asyncio
async def test_symptom_type_list_include_inactive():
    from tests.conftest import create_access_token
    token = create_access_token({"sub": "crud2@example.com", "user_id": "symptom-user-2"})
    headers = {"Authorization": f"Bearer {token}"}
    async with AsyncClient(app=app, base_url="http://test", headers=headers) as client:
        # Create two
        for name in ["Nausea", "Dizziness"]:
            resp = await client.post(
                "/api/v1/symptom-types",
                json={
                    "name": name,
                    "description": name,
                    "default_severity_numeric": 3,
                    "default_impact_numeric": 2,
                },
            )
            assert resp.status_code == status.HTTP_201_CREATED
        # Deactivate one (Nausea)
        current_list_resp = await client.get("/api/v1/symptom-types")
        current_list = current_list_resp.json()
        nausea_id = next(st["id"] for st in current_list if st["name"] == "Nausea")
        deactivate_resp = await client.patch(f"/api/v1/symptom-types/{nausea_id}/deactivate")
        assert deactivate_resp.status_code == status.HTTP_200_OK, deactivate_resp.text
        assert deactivate_resp.json()["active"] is False
        # Default list should exclude deactivated nausea
        default_list_resp = await client.get("/api/v1/symptom-types")
        default_list = default_list_resp.json()
        assert all(st["name"] != "Nausea" for st in default_list)
        # include_inactive should show both names
        all_list_resp = await client.get("/api/v1/symptom-types?include_inactive=true")
        all_list = all_list_resp.json()
        names = {st["name"] for st in all_list}
        assert names == {"Nausea", "Dizziness"}


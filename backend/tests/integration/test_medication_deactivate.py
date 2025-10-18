"""
Integration tests for medication deactivation behavior.

Tests verify that deactivated medications are properly excluded from 
medication logging operations and that existing logs remain unaffected.
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app


@pytest.fixture
def medication_data():
    """Sample active medication data."""
    return {
        "name": "Test Medication",
        "description": "A test medication for deactivation testing",
        "is_active": True
    }


@pytest.fixture
def log_data():
    """Sample medication log data."""
    return {
        "medication_name": "Test Medication",
        "quantity": 1,
        "unit": "tablet",
        "notes": "Morning dose"
    }


class TestMedicationDeactivationIntegration:
    """Integration tests for medication deactivation behavior."""

    async def test_active_medications_appear_in_logging_dropdown(self, medication_data):
        """Test that active medications appear in logging form dropdown."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create active medication
            med_response = await ac.post("/medications", json=medication_data)
            assert med_response.status_code == status.HTTP_201_CREATED
            
            # Get active medications for logging
            response = await ac.get("/medications", params={"active_only": True})
            assert response.status_code == status.HTTP_200_OK
            
            medications = response.json()
            assert len(medications) == 1
            assert medications[0]["name"] == medication_data["name"]
            assert medications[0]["is_active"] is True

    async def test_deactivated_medications_excluded_from_logging_dropdown(self, medication_data):
        """Test that deactivated medications are excluded from logging dropdown."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create active medication
            med_response = await ac.post("/medications", json=medication_data)
            medication_id = med_response.json()["id"]
            
            # Verify it appears in active list
            response = await ac.get("/medications", params={"active_only": True})
            assert len(response.json()) == 1
            
            # Deactivate medication
            deactivate_response = await ac.patch(f"/medications/{medication_id}/deactivate")
            assert deactivate_response.status_code == status.HTTP_200_OK
            
            # Verify it no longer appears in active list
            response = await ac.get("/medications", params={"active_only": True})
            assert response.status_code == status.HTTP_200_OK
            medications = response.json()
            assert len(medications) == 0

    async def test_existing_logs_unaffected_by_deactivation(self, medication_data, log_data):
        """Test that existing logs remain when medication is deactivated."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create medication
            med_response = await ac.post("/medications", json=medication_data)
            medication_id = med_response.json()["id"]
            
            # Create log entry with this medication
            log_response = await ac.post("/logs/medications", json=log_data)
            assert log_response.status_code == status.HTTP_201_CREATED
            log_id = log_response.json()["id"]
            
            # Deactivate medication
            deactivate_response = await ac.patch(f"/medications/{medication_id}/deactivate")
            assert deactivate_response.status_code == status.HTTP_200_OK
            
            # Verify existing log still exists and is accessible
            logs_response = await ac.get("/logs/medications")
            assert logs_response.status_code == status.HTTP_200_OK
            logs = logs_response.json()
            
            # Find our log in the response
            our_log = next((log for log in logs if log["id"] == log_id), None)
            assert our_log is not None
            assert our_log["medication_name"] == log_data["medication_name"]

    async def test_cannot_create_new_logs_with_deactivated_medication(self, medication_data):
        """Test that new logs cannot be created with deactivated medications."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create medication
            med_response = await ac.post("/medications", json=medication_data)
            medication_id = med_response.json()["id"]
            
            # Deactivate medication
            await ac.patch(f"/medications/{medication_id}/deactivate")
            
            # Try to create log with deactivated medication
            log_data_deactivated = {
                "medication_name": medication_data["name"],
                "quantity": 1,
                "unit": "tablet",
                "notes": "Should fail"
            }
            
            log_response = await ac.post("/logs/medications", json=log_data_deactivated)
            
            # Should fail with 400 Bad Request or 422 Unprocessable Entity
            assert log_response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
            error_data = log_response.json()
            assert "detail" in error_data
            assert "inactive" in error_data["detail"].lower() or "deactivated" in error_data["detail"].lower()

    async def test_medication_search_includes_deactivated_when_requested(self, medication_data):
        """Test that search can optionally include deactivated medications."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create medication
            med_response = await ac.post("/medications", json=medication_data)
            medication_id = med_response.json()["id"]
            
            # Deactivate medication
            await ac.patch(f"/medications/{medication_id}/deactivate")
            
            # Search without active_only filter (should include deactivated)
            response = await ac.get("/medications")
            assert response.status_code == status.HTTP_200_OK
            all_medications = response.json()
            assert len(all_medications) == 1
            assert all_medications[0]["is_active"] is False
            
            # Search with active_only=True (should exclude deactivated)
            response = await ac.get("/medications", params={"active_only": True})
            assert response.status_code == status.HTTP_200_OK
            active_medications = response.json()
            assert len(active_medications) == 0

    async def test_reactivate_medication_restores_availability(self, medication_data):
        """Test that reactivating a medication makes it available for logging again."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create medication
            med_response = await ac.post("/medications", json=medication_data)
            medication_id = med_response.json()["id"]
            
            # Deactivate medication
            await ac.patch(f"/medications/{medication_id}/deactivate")
            
            # Verify it's excluded from active list
            response = await ac.get("/medications", params={"active_only": True})
            assert len(response.json()) == 0
            
            # Reactivate medication (update is_active to True)
            reactivate_data = {
                "name": medication_data["name"],
                "description": medication_data["description"],
                "is_active": True
            }
            reactivate_response = await ac.put(f"/medications/{medication_id}", json=reactivate_data)
            assert reactivate_response.status_code == status.HTTP_200_OK
            
            # Verify it appears in active list again
            response = await ac.get("/medications", params={"active_only": True})
            assert response.status_code == status.HTTP_200_OK
            medications = response.json()
            assert len(medications) == 1
            assert medications[0]["is_active"] is True

    async def test_multiple_medications_deactivation_isolation(self):
        """Test that deactivating one medication doesn't affect others."""
        medications_data = [
            {"name": "Medication A", "description": "First medication", "is_active": True},
            {"name": "Medication B", "description": "Second medication", "is_active": True},
            {"name": "Medication C", "description": "Third medication", "is_active": True}
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create multiple medications
            medication_ids = []
            for med_data in medications_data:
                response = await ac.post("/medications", json=med_data)
                medication_ids.append(response.json()["id"])
            
            # Verify all are active
            response = await ac.get("/medications", params={"active_only": True})
            assert len(response.json()) == 3
            
            # Deactivate middle medication
            await ac.patch(f"/medications/{medication_ids[1]}/deactivate")
            
            # Verify only 2 remain active
            response = await ac.get("/medications", params={"active_only": True})
            active_medications = response.json()
            assert len(active_medications) == 2
            
            # Verify the correct ones remain active
            active_names = [med["name"] for med in active_medications]
            assert "Medication A" in active_names
            assert "Medication C" in active_names
            assert "Medication B" not in active_names

    async def test_deactivation_audit_trail(self, medication_data):
        """Test that medication deactivation updates the updated_at timestamp."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create medication
            med_response = await ac.post("/medications", json=medication_data)
            medication_id = med_response.json()["id"]
            original_updated_at = med_response.json()["updated_at"]
            
            # Add small delay to ensure timestamp difference
            import asyncio
            await asyncio.sleep(0.1)
            
            # Deactivate medication
            deactivate_response = await ac.patch(f"/medications/{medication_id}/deactivate")
            assert deactivate_response.status_code == status.HTTP_200_OK
            
            # Verify updated_at timestamp changed
            updated_medication = deactivate_response.json()
            assert updated_medication["updated_at"] != original_updated_at
            assert updated_medication["is_active"] is False
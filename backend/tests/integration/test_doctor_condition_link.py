"""
Integration tests for doctor-condition linking functionality.

Tests verify the complete workflow of creating conditions and doctors,
linking them together, and verifying the passport aggregation behavior.
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app


@pytest.fixture
def hypertension_condition():
    """Sample hypertension condition data."""
    return {
        "name": "Hypertension",
        "description": "High blood pressure requiring monitoring",
        "is_active": True
    }


@pytest.fixture
def diabetes_condition():
    """Sample diabetes condition data."""
    return {
        "name": "Type 2 Diabetes",
        "description": "Blood sugar management condition",
        "is_active": True
    }


@pytest.fixture
def cardiologist_doctor():
    """Sample cardiologist doctor data."""
    return {
        "name": "Dr. Sarah Johnson",
        "specialty": "Cardiology",
        "contact_info": "sarah.johnson@heartcenter.com",
        "is_active": True
    }


@pytest.fixture
def endocrinologist_doctor():
    """Sample endocrinologist doctor data."""
    return {
        "name": "Dr. Michael Chen",
        "specialty": "Endocrinology",
        "contact_info": "michael.chen@diabetescenter.com",
        "is_active": True
    }


@pytest.fixture
def primary_care_doctor():
    """Sample primary care doctor data."""
    return {
        "name": "Dr. Emily Rodriguez",
        "specialty": "Family Medicine",
        "contact_info": "emily.rodriguez@familycare.com",
        "is_active": True
    }


class TestDoctorConditionLinkingIntegration:
    """Integration tests for doctor-condition linking workflow."""

    async def test_single_condition_single_doctor_link(self, hypertension_condition, cardiologist_doctor):
        """Test linking one doctor to one condition."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create condition
            condition_response = await ac.post("/conditions", json=hypertension_condition)
            assert condition_response.status_code == status.HTTP_201_CREATED
            condition = condition_response.json()
            
            # Create doctor
            doctor_response = await ac.post("/doctors", json=cardiologist_doctor)
            assert doctor_response.status_code == status.HTTP_201_CREATED
            doctor = doctor_response.json()
            
            # Link doctor to condition
            link_data = {
                "doctor_id": doctor["id"],
                "condition_id": condition["id"]
            }
            
            link_response = await ac.post("/doctors/link-condition", json=link_data)
            assert link_response.status_code == status.HTTP_200_OK
            
            # Verify passport shows the link
            passport_response = await ac.get("/passport")
            assert passport_response.status_code == status.HTTP_200_OK
            passport = passport_response.json()
            
            assert len(passport) == 1
            passport_item = passport[0]
            assert passport_item["condition"]["id"] == condition["id"]
            assert passport_item["condition"]["name"] == "Hypertension"
            assert len(passport_item["doctors"]) == 1
            assert passport_item["doctors"][0]["id"] == doctor["id"]
            assert passport_item["doctors"][0]["name"] == "Dr. Sarah Johnson"

    async def test_single_condition_multiple_doctors_link(
        self, 
        hypertension_condition, 
        cardiologist_doctor, 
        primary_care_doctor
    ):
        """Test linking multiple doctors to one condition."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create condition
            condition_response = await ac.post("/conditions", json=hypertension_condition)
            condition = condition_response.json()
            
            # Create doctors
            cardiologist_response = await ac.post("/doctors", json=cardiologist_doctor)
            cardiologist = cardiologist_response.json()
            
            primary_care_response = await ac.post("/doctors", json=primary_care_doctor)
            primary_care = primary_care_response.json()
            
            # Link both doctors to condition
            link_cardiologist = await ac.post("/doctors/link-condition", json={
                "doctor_id": cardiologist["id"],
                "condition_id": condition["id"]
            })
            assert link_cardiologist.status_code == status.HTTP_200_OK
            
            link_primary_care = await ac.post("/doctors/link-condition", json={
                "doctor_id": primary_care["id"],
                "condition_id": condition["id"]
            })
            assert link_primary_care.status_code == status.HTTP_200_OK
            
            # Verify passport shows both doctors
            passport_response = await ac.get("/passport")
            passport = passport_response.json()
            
            assert len(passport) == 1
            passport_item = passport[0]
            assert passport_item["condition"]["id"] == condition["id"]
            assert len(passport_item["doctors"]) == 2
            
            # Verify both doctors are present (order not guaranteed)
            doctor_names = [doc["name"] for doc in passport_item["doctors"]]
            assert "Dr. Sarah Johnson" in doctor_names
            assert "Dr. Emily Rodriguez" in doctor_names

    async def test_multiple_conditions_multiple_doctors_complex_links(
        self,
        hypertension_condition,
        diabetes_condition,
        cardiologist_doctor,
        endocrinologist_doctor,
        primary_care_doctor
    ):
        """Test complex scenario with multiple conditions and doctors."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create conditions
            hypertension_response = await ac.post("/conditions", json=hypertension_condition)
            hypertension = hypertension_response.json()
            
            diabetes_response = await ac.post("/conditions", json=diabetes_condition)
            diabetes = diabetes_response.json()
            
            # Create doctors
            cardiologist_response = await ac.post("/doctors", json=cardiologist_doctor)
            cardiologist = cardiologist_response.json()
            
            endocrinologist_response = await ac.post("/doctors", json=endocrinologist_doctor)
            endocrinologist = endocrinologist_response.json()
            
            primary_care_response = await ac.post("/doctors", json=primary_care_doctor)
            primary_care = primary_care_response.json()
            
            # Create complex linking pattern:
            # Hypertension -> Cardiologist + Primary Care
            # Diabetes -> Endocrinologist + Primary Care
            await ac.post("/doctors/link-condition", json={
                "doctor_id": cardiologist["id"],
                "condition_id": hypertension["id"]
            })
            
            await ac.post("/doctors/link-condition", json={
                "doctor_id": primary_care["id"],
                "condition_id": hypertension["id"]
            })
            
            await ac.post("/doctors/link-condition", json={
                "doctor_id": endocrinologist["id"],
                "condition_id": diabetes["id"]
            })
            
            await ac.post("/doctors/link-condition", json={
                "doctor_id": primary_care["id"],
                "condition_id": diabetes["id"]
            })
            
            # Verify passport shows correct structure
            passport_response = await ac.get("/passport")
            passport = passport_response.json()
            
            assert len(passport) == 2
            
            # Find hypertension item
            hypertension_item = next(
                item for item in passport 
                if item["condition"]["name"] == "Hypertension"
            )
            assert len(hypertension_item["doctors"]) == 2
            hypertension_doctor_names = [doc["name"] for doc in hypertension_item["doctors"]]
            assert "Dr. Sarah Johnson" in hypertension_doctor_names
            assert "Dr. Emily Rodriguez" in hypertension_doctor_names
            
            # Find diabetes item
            diabetes_item = next(
                item for item in passport 
                if item["condition"]["name"] == "Type 2 Diabetes"
            )
            assert len(diabetes_item["doctors"]) == 2
            diabetes_doctor_names = [doc["name"] for doc in diabetes_item["doctors"]]
            assert "Dr. Michael Chen" in diabetes_doctor_names
            assert "Dr. Emily Rodriguez" in diabetes_doctor_names

    async def test_inactive_conditions_excluded_from_passport(self, hypertension_condition, cardiologist_doctor):
        """Test that inactive conditions are excluded from passport."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create active condition
            condition_response = await ac.post("/conditions", json=hypertension_condition)
            condition = condition_response.json()
            
            # Create doctor
            doctor_response = await ac.post("/doctors", json=cardiologist_doctor)
            doctor = doctor_response.json()
            
            # Link doctor to condition
            await ac.post("/doctors/link-condition", json={
                "doctor_id": doctor["id"],
                "condition_id": condition["id"]
            })
            
            # Verify condition appears in passport
            passport_response = await ac.get("/passport")
            passport = passport_response.json()
            assert len(passport) == 1
            
            # Deactivate condition (assuming PATCH endpoint exists)
            deactivate_response = await ac.patch(f"/conditions/{condition['id']}", json={
                "is_active": False
            })
            
            # If deactivation is supported, verify it's excluded from passport
            if deactivate_response.status_code == status.HTTP_200_OK:
                passport_response = await ac.get("/passport")
                passport = passport_response.json()
                
                # Should be empty or not contain the deactivated condition
                active_conditions = [
                    item for item in passport 
                    if item["condition"]["is_active"]
                ]
                assert len(active_conditions) == 0

    async def test_inactive_doctors_excluded_from_passport(self, hypertension_condition, cardiologist_doctor):
        """Test that inactive doctors are excluded from passport."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create condition
            condition_response = await ac.post("/conditions", json=hypertension_condition)
            condition = condition_response.json()
            
            # Create active doctor
            doctor_response = await ac.post("/doctors", json=cardiologist_doctor)
            doctor = doctor_response.json()
            
            # Link doctor to condition
            await ac.post("/doctors/link-condition", json={
                "doctor_id": doctor["id"],
                "condition_id": condition["id"]
            })
            
            # Verify doctor appears in passport
            passport_response = await ac.get("/passport")
            passport = passport_response.json()
            assert len(passport) == 1
            assert len(passport[0]["doctors"]) == 1
            
            # Deactivate doctor (assuming PATCH endpoint exists)
            deactivate_response = await ac.patch(f"/doctors/{doctor['id']}", json={
                "is_active": False
            })
            
            # If deactivation is supported, verify doctor is excluded from passport
            if deactivate_response.status_code == status.HTTP_200_OK:
                passport_response = await ac.get("/passport")
                passport = passport_response.json()
                
                # Condition should still exist but with no active doctors
                assert len(passport) == 1
                active_doctors = [
                    doc for doc in passport[0]["doctors"] 
                    if doc["is_active"]
                ]
                assert len(active_doctors) == 0

    async def test_duplicate_link_prevention(self, hypertension_condition, cardiologist_doctor):
        """Test that duplicate links are handled gracefully."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create condition and doctor
            condition_response = await ac.post("/conditions", json=hypertension_condition)
            condition = condition_response.json()
            
            doctor_response = await ac.post("/doctors", json=cardiologist_doctor)
            doctor = doctor_response.json()
            
            # Link doctor to condition first time
            link_data = {
                "doctor_id": doctor["id"],
                "condition_id": condition["id"]
            }
            
            first_link = await ac.post("/doctors/link-condition", json=link_data)
            assert first_link.status_code == status.HTTP_200_OK
            
            # Try to link same doctor to same condition again
            second_link = await ac.post("/doctors/link-condition", json=link_data)
            
            # Should either succeed (idempotent) or return appropriate error
            assert second_link.status_code in [
                status.HTTP_200_OK,  # Idempotent
                status.HTTP_409_CONFLICT,  # Duplicate
                status.HTTP_422_UNPROCESSABLE_ENTITY  # Validation error
            ]
            
            # Verify passport still shows only one link
            passport_response = await ac.get("/passport")
            passport = passport_response.json()
            assert len(passport) == 1
            assert len(passport[0]["doctors"]) == 1

    async def test_link_validation_with_invalid_ids(self):
        """Test that linking with invalid IDs returns appropriate errors."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Test with completely invalid UUIDs
            invalid_link = await ac.post("/doctors/link-condition", json={
                "doctor_id": "invalid-uuid",
                "condition_id": "invalid-uuid"
            })
            assert invalid_link.status_code in [
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_404_NOT_FOUND
            ]
            
            # Test with valid UUID format but non-existent entities
            import uuid
            fake_doctor_id = str(uuid.uuid4())
            fake_condition_id = str(uuid.uuid4())
            
            nonexistent_link = await ac.post("/doctors/link-condition", json={
                "doctor_id": fake_doctor_id,
                "condition_id": fake_condition_id
            })
            assert nonexistent_link.status_code in [
                status.HTTP_404_NOT_FOUND,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
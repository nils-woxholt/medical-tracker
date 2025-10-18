"""
Contract tests for medical context endpoints (conditions, doctors, passport).

Tests verify API contract compliance for CRUD operations on conditions and doctors,
as well as passport aggregation functionality.
Ensures proper validation, response formats, and error handling.
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app


@pytest.fixture
def condition_data():
    """Sample condition data for testing."""
    return {
        "name": "Hypertension",
        "description": "High blood pressure condition",
        "is_active": True
    }


@pytest.fixture
def doctor_data():
    """Sample doctor data for testing."""
    return {
        "name": "Dr. Sarah Johnson",
        "specialty": "Cardiology",
        "contact_info": "sarah.johnson@example.com",
        "is_active": True
    }


@pytest.fixture
def inactive_condition_data():
    """Sample inactive condition data for testing."""
    return {
        "name": "Old Condition",
        "description": "No longer relevant",
        "is_active": False
    }


class TestConditionEndpoints:
    """Contract tests for /conditions endpoints."""

    async def test_create_condition_success(self, condition_data):
        """Test successful condition creation."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/conditions", json=condition_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["name"] == condition_data["name"]
        assert data["description"] == condition_data["description"]
        assert data["is_active"] == condition_data["is_active"]
        assert "created_at" in data
        assert "updated_at" in data
        assert "user_id" in data

    async def test_create_condition_invalid_data(self):
        """Test condition creation with invalid data."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/conditions", json={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

    async def test_create_condition_missing_name(self, condition_data):
        """Test condition creation with missing required field."""
        invalid_data = condition_data.copy()
        del invalid_data["name"]
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/conditions", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

    async def test_list_conditions_empty(self):
        """Test listing conditions when none exist."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/conditions")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_list_conditions_with_data(self, condition_data):
        """Test listing conditions after creating one."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create condition first
            create_response = await ac.post("/conditions", json=condition_data)
            assert create_response.status_code == status.HTTP_201_CREATED
            
            # List conditions
            list_response = await ac.get("/conditions")
            assert list_response.status_code == status.HTTP_200_OK
            
            data = list_response.json()
            assert isinstance(data, list)
            assert len(data) >= 1
            
            # Verify structure of first item
            condition = data[0]
            assert "id" in condition
            assert "name" in condition
            assert "description" in condition
            assert "is_active" in condition
            assert "created_at" in condition
            assert "updated_at" in condition


class TestDoctorEndpoints:
    """Contract tests for /doctors endpoints."""

    async def test_create_doctor_success(self, doctor_data):
        """Test successful doctor creation."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/doctors", json=doctor_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["name"] == doctor_data["name"]
        assert data["specialty"] == doctor_data["specialty"]
        assert data["contact_info"] == doctor_data["contact_info"]
        assert data["is_active"] == doctor_data["is_active"]
        assert "created_at" in data
        assert "updated_at" in data
        assert "user_id" in data

    async def test_create_doctor_invalid_data(self):
        """Test doctor creation with invalid data."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/doctors", json={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

    async def test_create_doctor_missing_name(self, doctor_data):
        """Test doctor creation with missing required field."""
        invalid_data = doctor_data.copy()
        del invalid_data["name"]
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/doctors", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

    async def test_list_doctors_empty(self):
        """Test listing doctors when none exist."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/doctors")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_list_doctors_with_data(self, doctor_data):
        """Test listing doctors after creating one."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create doctor first
            create_response = await ac.post("/doctors", json=doctor_data)
            assert create_response.status_code == status.HTTP_201_CREATED
            
            # List doctors
            list_response = await ac.get("/doctors")
            assert list_response.status_code == status.HTTP_200_OK
            
            data = list_response.json()
            assert isinstance(data, list)
            assert len(data) >= 1
            
            # Verify structure of first item
            doctor = data[0]
            assert "id" in doctor
            assert "name" in doctor
            assert "specialty" in doctor
            assert "contact_info" in doctor
            assert "is_active" in doctor
            assert "created_at" in doctor
            assert "updated_at" in doctor


class TestPassportEndpoints:
    """Contract tests for /passport endpoints."""

    async def test_get_passport_empty(self):
        """Test passport retrieval when no conditions exist."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/passport")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_get_passport_with_conditions_and_doctors(self, condition_data, doctor_data):
        """Test passport retrieval with conditions and linked doctors."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create condition
            condition_response = await ac.post("/conditions", json=condition_data)
            assert condition_response.status_code == status.HTTP_201_CREATED
            condition = condition_response.json()
            
            # Create doctor
            doctor_response = await ac.post("/doctors", json=doctor_data)
            assert doctor_response.status_code == status.HTTP_201_CREATED
            doctor = doctor_response.json()
            
            # Get passport
            passport_response = await ac.get("/passport")
            assert passport_response.status_code == status.HTTP_200_OK
            
            data = passport_response.json()
            assert isinstance(data, list)
            assert len(data) >= 1
            
            # Verify passport structure
            passport_item = data[0]
            assert "condition" in passport_item
            assert "doctors" in passport_item
            
            # Verify condition structure
            passport_condition = passport_item["condition"]
            assert "id" in passport_condition
            assert "name" in passport_condition
            assert "description" in passport_condition
            assert "is_active" in passport_condition
            
            # Verify doctors array structure
            passport_doctors = passport_item["doctors"]
            assert isinstance(passport_doctors, list)

    async def test_passport_response_format(self):
        """Test that passport response follows expected format."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/passport")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers.get("content-type") == "application/json"
        
        data = response.json()
        assert isinstance(data, list)
        
        # If data exists, verify format
        if data:
            passport_item = data[0]
            assert isinstance(passport_item, dict)
            assert "condition" in passport_item
            assert "doctors" in passport_item
            assert isinstance(passport_item["doctors"], list)


class TestDoctorConditionLinking:
    """Contract tests for doctor-condition linking functionality."""

    async def test_link_doctor_to_condition_success(self, condition_data, doctor_data):
        """Test successful linking of doctor to condition."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create condition
            condition_response = await ac.post("/conditions", json=condition_data)
            assert condition_response.status_code == status.HTTP_201_CREATED
            condition = condition_response.json()
            
            # Create doctor
            doctor_response = await ac.post("/doctors", json=doctor_data)
            assert doctor_response.status_code == status.HTTP_201_CREATED
            doctor = doctor_response.json()
            
            # Link doctor to condition
            link_data = {
                "doctor_id": doctor["id"],
                "condition_id": condition["id"]
            }
            
            link_response = await ac.post("/doctors/link-condition", json=link_data)
            assert link_response.status_code == status.HTTP_200_OK
            
            # Verify link in passport
            passport_response = await ac.get("/passport")
            passport_data = passport_response.json()
            
            # Find the condition in passport
            condition_passport = next(
                (item for item in passport_data if item["condition"]["id"] == condition["id"]),
                None
            )
            assert condition_passport is not None
            
            # Verify doctor is linked
            linked_doctors = condition_passport["doctors"]
            assert len(linked_doctors) >= 1
            linked_doctor = next(
                (d for d in linked_doctors if d["id"] == doctor["id"]),
                None
            )
            assert linked_doctor is not None

    async def test_link_nonexistent_doctor_to_condition(self, condition_data):
        """Test linking non-existent doctor to condition fails properly."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create condition
            condition_response = await ac.post("/conditions", json=condition_data)
            assert condition_response.status_code == status.HTTP_201_CREATED
            condition = condition_response.json()
            
            # Try to link non-existent doctor
            link_data = {
                "doctor_id": "non-existent-id",
                "condition_id": condition["id"]
            }
            
            link_response = await ac.post("/doctors/link-condition", json=link_data)
            assert link_response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_ENTITY]

    async def test_link_doctor_to_nonexistent_condition(self, doctor_data):
        """Test linking doctor to non-existent condition fails properly."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create doctor
            doctor_response = await ac.post("/doctors", json=doctor_data)
            assert doctor_response.status_code == status.HTTP_201_CREATED
            doctor = doctor_response.json()
            
            # Try to link to non-existent condition
            link_data = {
                "doctor_id": doctor["id"],
                "condition_id": "non-existent-id"
            }
            
            link_response = await ac.post("/doctors/link-condition", json=link_data)
            assert link_response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_ENTITY]
"""
Contract tests for medication master endpoints.

Tests verify API contract compliance for CRUD operations on medication master data.
Ensures proper validation, response formats, and error handling.
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from app.main import app


@pytest.fixture
def medication_data():
    """Sample medication data for testing."""
    return {
        "name": "Aspirin",
        "description": "Pain reliever and anti-inflammatory",
        "is_active": True
    }


@pytest.fixture
def inactive_medication_data():
    """Sample inactive medication data for testing."""
    return {
        "name": "Old Medication",
        "description": "No longer prescribed",
        "is_active": False
    }


class TestMedicationEndpoints:
    """Contract tests for /medications endpoints."""

    async def test_create_medication_success(self, medication_data):
        """Test successful medication creation."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/medications", json=medication_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["name"] == medication_data["name"]
        assert data["description"] == medication_data["description"]
        assert data["is_active"] == medication_data["is_active"]
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_medication_duplicate_name(self, medication_data):
        """Test duplicate medication name validation."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create first medication
            await ac.post("/medications", json=medication_data)
            
            # Try to create duplicate
            response = await ac.post("/medications", json=medication_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()

    async def test_create_medication_invalid_data(self):
        """Test medication creation with invalid data."""
        invalid_data = {
            "name": "",  # Empty name should be invalid
            "description": "Valid description"
        }
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/medications", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_list_medications_empty(self):
        """Test listing medications when none exist."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/medications")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_list_medications_with_data(self, medication_data):
        """Test listing medications with existing data."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create medication first
            create_response = await ac.post("/medications", json=medication_data)
            medication_id = create_response.json()["id"]
            
            # List medications
            response = await ac.get("/medications")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == medication_id

    async def test_list_medications_active_only(self, medication_data, inactive_medication_data):
        """Test listing only active medications."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create active and inactive medications
            await ac.post("/medications", json=medication_data)
            await ac.post("/medications", json=inactive_medication_data)
            
            # List only active medications
            response = await ac.get("/medications", params={"active_only": True})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["is_active"] is True

    async def test_get_medication_success(self, medication_data):
        """Test successful medication retrieval by ID."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create medication first
            create_response = await ac.post("/medications", json=medication_data)
            medication_id = create_response.json()["id"]
            
            # Get medication
            response = await ac.get(f"/medications/{medication_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == medication_id
        assert data["name"] == medication_data["name"]

    async def test_get_medication_not_found(self):
        """Test medication retrieval with non-existent ID."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/medications/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_medication_success(self, medication_data):
        """Test successful medication update."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create medication first
            create_response = await ac.post("/medications", json=medication_data)
            medication_id = create_response.json()["id"]
            
            # Update medication
            update_data = {
                "name": "Updated Aspirin",
                "description": "Updated description",
                "is_active": True
            }
            response = await ac.put(f"/medications/{medication_id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == medication_id
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]

    async def test_update_medication_not_found(self):
        """Test medication update with non-existent ID."""
        update_data = {
            "name": "Non-existent medication",
            "description": "This should fail"
        }
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.put("/medications/99999", json=update_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_deactivate_medication_success(self, medication_data):
        """Test successful medication deactivation."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create medication first
            create_response = await ac.post("/medications", json=medication_data)
            medication_id = create_response.json()["id"]
            
            # Deactivate medication
            response = await ac.patch(f"/medications/{medication_id}/deactivate")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == medication_id
        assert data["is_active"] is False

    async def test_deactivate_medication_not_found(self):
        """Test medication deactivation with non-existent ID."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.patch("/medications/99999/deactivate")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_search_medications_by_name(self, medication_data):
        """Test medication search functionality."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create medication first
            await ac.post("/medications", json=medication_data)
            
            # Search by partial name
            response = await ac.get("/medications", params={"search": "Asp"})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert "Aspirin" in data[0]["name"]

    async def test_medication_name_case_insensitive(self):
        """Test medication name normalization (case insensitive)."""
        medication_upper = {
            "name": "ASPIRIN",
            "description": "Upper case name"
        }
        
        medication_lower = {
            "name": "aspirin",
            "description": "Lower case name"
        }
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create first medication
            response1 = await ac.post("/medications", json=medication_upper)
            assert response1.status_code == status.HTTP_201_CREATED
            
            # Try to create with different case - should fail as duplicate
            response2 = await ac.post("/medications", json=medication_lower)
            assert response2.status_code == status.HTTP_400_BAD_REQUEST

    async def test_medication_pagination(self):
        """Test medication list pagination."""
        # Create multiple medications for pagination test
        medications = [
            {"name": f"Medication {i}", "description": f"Description {i}"}
            for i in range(15)
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            # Create medications
            for med_data in medications:
                await ac.post("/medications", json=med_data)
            
            # Test pagination
            response = await ac.get("/medications", params={"limit": 10, "offset": 0})
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 10
            
            # Test second page
            response = await ac.get("/medications", params={"limit": 10, "offset": 10})
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 5
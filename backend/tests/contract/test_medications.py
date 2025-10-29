"""
Contract tests for medication master endpoints.

Tests verify API contract compliance for CRUD operations on medication master data.
Ensures proper validation, response formats, and error handling.
"""

import pytest
from httpx import AsyncClient, ASGITransport
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
    """Contract tests for /api/v1/medications endpoints (paginated schema)."""

    API_PREFIX = "/api/v1/medications"

    async def test_create_medication_success(self, medication_data):
        """Test successful medication creation."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(f"{self.API_PREFIX}/", json=medication_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify response structure matches MedicationResponse
        assert {"id", "name", "description", "is_active", "created_at", "updated_at"}.issubset(data.keys())
        assert data["name"] == medication_data["name"]
        assert data["description"] == medication_data["description"]
        assert data["is_active"] == medication_data["is_active"]

    async def test_create_medication_duplicate_name(self, medication_data):
        """Test duplicate medication name validation."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Create first medication
            await ac.post(f"{self.API_PREFIX}/", json=medication_data)

            # Try to create duplicate
            response = await ac.post(f"{self.API_PREFIX}/", json=medication_data)

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
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(f"{self.API_PREFIX}/", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_list_medications_empty(self):
        """Test listing medications when none exist (expects paginated object)."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get(f"{self.API_PREFIX}/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Validate paginated schema keys
        assert {"items", "total", "page", "per_page", "pages"}.issubset(data.keys())
        assert isinstance(data["items"], list)
        assert data["total"] == 0
        assert len(data["items"]) == 0

    async def test_list_medications_with_data(self, medication_data):
        """Test listing medications with existing data (paginated)."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Create medication first
            create_response = await ac.post(f"{self.API_PREFIX}/", json=medication_data)
            medication_id = create_response.json()["id"]

            # List medications
            response = await ac.get(f"{self.API_PREFIX}/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == medication_id

    async def test_list_medications_active_only(self, medication_data, inactive_medication_data):
        """Test listing only active medications."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Create active and inactive medications
            await ac.post(f"{self.API_PREFIX}/", json=medication_data)
            await ac.post(f"{self.API_PREFIX}/", json=inactive_medication_data)

            # List only active medications
            response = await ac.get(f"{self.API_PREFIX}/", params={"active_only": True})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data["items"], list)
        # Only active should appear
        assert all(item["is_active"] for item in data["items"])
        assert len(data["items"]) == 1

    async def test_get_medication_success(self, medication_data):
        """Test successful medication retrieval by ID."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Create medication first
            create_response = await ac.post(f"{self.API_PREFIX}/", json=medication_data)
            medication_id = create_response.json()["id"]

            # Get medication
            response = await ac.get(f"{self.API_PREFIX}/{medication_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == medication_id
        assert data["name"] == medication_data["name"]

    async def test_get_medication_not_found(self):
        """Test medication retrieval with non-existent ID."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get(f"{self.API_PREFIX}/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_medication_success(self, medication_data):
        """Test successful medication update."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Create medication first
            create_response = await ac.post(f"{self.API_PREFIX}/", json=medication_data)
            medication_id = create_response.json()["id"]

            # Update medication
            update_data = {
                "name": "Updated Aspirin",
                "description": "Updated description",
                "is_active": True
            }
            response = await ac.put(f"{self.API_PREFIX}/{medication_id}", json=update_data)

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
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.put(f"{self.API_PREFIX}/99999", json=update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_deactivate_medication_success(self, medication_data):
        """Test successful medication deactivation."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Create medication first
            create_response = await ac.post(f"{self.API_PREFIX}/", json=medication_data)
            medication_id = create_response.json()["id"]

            # Deactivate medication
            response = await ac.patch(f"{self.API_PREFIX}/{medication_id}/deactivate")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == medication_id
        assert data["is_active"] is False

    async def test_deactivate_medication_not_found(self):
        """Test medication deactivation with non-existent ID."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.patch(f"{self.API_PREFIX}/99999/deactivate")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_search_medications_by_name(self, medication_data):
        """Test medication search functionality via list endpoint search param."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Create medication first
            await ac.post(f"{self.API_PREFIX}/", json=medication_data)

            # Search by partial name
            response = await ac.get(f"{self.API_PREFIX}/", params={"search": "Asp"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 1
        assert any("Aspirin" in item["name"] for item in data["items"])

    async def test_medication_name_case_insensitive(self):
        """Test medication name normalization (case insensitive)."""
        medication_upper = {"name": "ASPIRIN", "description": "Upper case name"}
        medication_lower = {"name": "aspirin", "description": "Lower case name"}
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Create first medication
            response1 = await ac.post(f"{self.API_PREFIX}/", json=medication_upper)
            assert response1.status_code == status.HTTP_201_CREATED

            # Try to create with different case - should fail as duplicate
            response2 = await ac.post(f"{self.API_PREFIX}/", json=medication_lower)
            assert response2.status_code == status.HTTP_400_BAD_REQUEST

    async def test_medication_pagination(self):
        """Test medication list pagination using page/per_page parameters."""
        medications = [{"name": f"Medication {i}", "description": f"Description {i}"} for i in range(15)]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            for med_data in medications:
                await ac.post(f"{self.API_PREFIX}/", json=med_data)

            # First page
            response = await ac.get(f"{self.API_PREFIX}/", params={"page": 1, "per_page": 10})
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["items"]) == 10
            assert data["total"] == 15
            assert data["pages"] == 2

            # Second page
            response = await ac.get(f"{self.API_PREFIX}/", params={"page": 2, "per_page": 10})
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["items"]) == 5
            assert data["page"] == 2
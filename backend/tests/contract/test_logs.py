"""
Contract Tests for Logs and Feel-vs-Yesterday APIs

This module contains contract tests for the logging and feel analysis endpoints
in the SaaS Medical Tracker application, following the OpenAPI specification.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.auth import create_access_token
from app.main import app
from app.models.base import Base


class TestLogsContracts:
    """Contract tests for logs endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def test_user_token(self):
        """Create test user token."""
        payload = {
            "user_id": "test-user-123",
            "sub": "test@example.com",
            "exp": datetime.now(timezone.utc).timestamp() + 3600  # 1 hour
        }
        return create_access_token(payload)

    @pytest.fixture
    def auth_headers(self, test_user_token):
        """Create authorization headers."""
        return {"Authorization": f"Bearer {test_user_token}"}

    def test_create_medication_log_contract(self, client, auth_headers):
        """Test POST /api/v1/logs/medications matches contract."""
        
        # Valid medication log payload
        payload = {
            "medication_name": "Ibuprofen",
            "dosage": "200mg",
            "taken_at": datetime.now(timezone.utc).isoformat(),
            "notes": "Taken for headache",
            "effectiveness_rating": 4
        }
        
        response = client.post(
            "/api/v1/logs/medications",
            json=payload,
            headers=auth_headers
        )
        
        # Contract validation
        assert response.status_code == 201
        data = response.json()
        
        # Required fields from contract
        assert "id" in data
        assert "user_id" in data
        assert "medication_name" in data
        assert "dosage" in data
        assert "taken_at" in data
        assert "logged_at" in data
        
        # Data type validation
        assert isinstance(data["id"], int)
        assert isinstance(data["user_id"], str)
        assert isinstance(data["medication_name"], str)
        assert isinstance(data["dosage"], str)
        assert data["effectiveness_rating"] == 4

    def test_list_medication_logs_contract(self, client, auth_headers):
        """Test GET /api/v1/logs/medications matches contract."""
        
        response = client.get(
            "/api/v1/logs/medications",
            headers=auth_headers
        )
        
        # Contract validation
        assert response.status_code == 200
        data = response.json()
        
        # Should return array
        assert isinstance(data, list)
        
        # If logs exist, validate structure
        if data:
            log = data[0]
            assert "id" in log
            assert "user_id" in log
            assert "medication_name" in log
            assert "dosage" in log
            assert "taken_at" in log
            assert "logged_at" in log

    def test_get_medication_log_contract(self, client, auth_headers):
        """Test GET /api/v1/logs/medications/{log_id} matches contract."""
        
        # First create a log
        create_payload = {
            "medication_name": "Test Med",
            "dosage": "100mg",
            "taken_at": datetime.now(timezone.utc).isoformat()
        }
        
        create_response = client.post(
            "/api/v1/logs/medications",
            json=create_payload,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            log_id = create_response.json()["id"]
            
            # Test get endpoint
            response = client.get(
                f"/api/v1/logs/medications/{log_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Contract validation
            assert data["id"] == log_id
            assert "user_id" in data
            assert "medication_name" in data
            assert "dosage" in data

    def test_create_symptom_log_contract(self, client, auth_headers):
        """Test POST /api/v1/logs/symptoms matches contract."""
        
        payload = {
            "symptom_name": "Headache",
            "severity": "moderate",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "duration_minutes": 120,
            "location": "Forehead",
            "impact_rating": 3
        }
        
        response = client.post(
            "/api/v1/logs/symptoms",
            json=payload,
            headers=auth_headers
        )
        
        # Contract validation
        assert response.status_code == 201
        data = response.json()
        
        # Required fields from contract
        assert "id" in data
        assert "user_id" in data
        assert "symptom_name" in data
        assert "severity" in data
        assert "started_at" in data
        assert "logged_at" in data
        
        # Data validation
        assert data["symptom_name"] == "Headache"
        assert data["severity"] == "moderate"
        assert data["duration_minutes"] == 120
        assert data["impact_rating"] == 3

    def test_list_symptom_logs_contract(self, client, auth_headers):
        """Test GET /api/v1/logs/symptoms matches contract."""
        
        response = client.get(
            "/api/v1/logs/symptoms",
            headers=auth_headers
        )
        
        # Contract validation
        assert response.status_code == 200
        data = response.json()
        
        # Should return array
        assert isinstance(data, list)

    def test_logs_summary_contract(self, client, auth_headers):
        """Test GET /api/v1/logs/summary matches contract."""
        
        response = client.get(
            "/api/v1/logs/summary",
            headers=auth_headers
        )
        
        # Contract validation
        assert response.status_code == 200
        data = response.json()
        
        # Required fields from contract
        assert "recent_medications" in data
        assert "recent_symptoms" in data
        assert "total_medications_today" in data
        assert "total_symptoms_today" in data
        
        # Data types
        assert isinstance(data["recent_medications"], list)
        assert isinstance(data["recent_symptoms"], list)
        assert isinstance(data["total_medications_today"], int)
        assert isinstance(data["total_symptoms_today"], int)

    def test_medication_log_validation_contract(self, client, auth_headers):
        """Test validation error responses match contract."""
        
        # Invalid payload (missing required fields)
        payload = {
            "medication_name": ""  # Empty name should fail validation
        }
        
        response = client.post(
            "/api/v1/logs/medications",
            json=payload,
            headers=auth_headers
        )
        
        # Should return validation error
        assert response.status_code == 422
        data = response.json()
        
        # Validation error structure
        assert "detail" in data
        assert isinstance(data["detail"], list)

    def test_symptom_log_validation_contract(self, client, auth_headers):
        """Test symptom validation error responses match contract."""
        
        # Invalid severity level
        payload = {
            "symptom_name": "Test",
            "severity": "invalid_level",  # Should fail validation
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = client.post(
            "/api/v1/logs/symptoms",
            json=payload,
            headers=auth_headers
        )
        
        # Should return validation error
        assert response.status_code == 422


class TestFeelVsYesterdayContracts:
    """Contract tests for feel-vs-yesterday endpoint."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def test_user_token(self):
        """Create test user token.""" 
        payload = {
            "user_id": "test-user-123",
            "sub": "test@example.com",
            "exp": datetime.now(timezone.utc).timestamp() + 3600
        }
        return create_access_token(payload)

    @pytest.fixture
    def auth_headers(self, test_user_token):
        """Create authorization headers."""
        return {"Authorization": f"Bearer {test_user_token}"}

    def test_feel_vs_yesterday_contract(self, client, auth_headers):
        """Test GET /api/v1/feel-vs-yesterday matches contract."""
        
        response = client.get(
            "/api/v1/feel-vs-yesterday",
            headers=auth_headers
        )
        
        # Contract validation
        assert response.status_code == 200
        data = response.json()
        
        # Required fields from contract
        assert "status" in data
        assert "confidence" in data
        assert "summary" in data
        assert "details" in data
        assert "date_compared" in data
        
        # Data types and constraints
        assert isinstance(data["status"], str)
        assert data["status"] in ["better", "same", "worse", "unknown"]
        assert isinstance(data["confidence"], (int, float))
        assert 0.0 <= data["confidence"] <= 1.0
        assert isinstance(data["summary"], str)
        assert isinstance(data["details"], dict)
        assert isinstance(data["date_compared"], str)

    def test_feel_vs_yesterday_with_date_contract(self, client, auth_headers):
        """Test feel-vs-yesterday with target_date parameter."""
        
        target_date = datetime.now(timezone.utc).isoformat()
        
        response = client.get(
            "/api/v1/feel-vs-yesterday",
            params={"target_date": target_date},
            headers=auth_headers
        )
        
        # Should work with date parameter
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_feel_vs_yesterday_history_contract(self, client, auth_headers):
        """Test GET /api/v1/feel-vs-yesterday/history matches contract."""
        
        response = client.get(
            "/api/v1/feel-vs-yesterday/history",
            params={"days": 3},
            headers=auth_headers
        )
        
        # Contract validation
        assert response.status_code == 200
        data = response.json()
        
        # Should return array of feel responses
        assert isinstance(data, list)
        
        # Each item should match feel response schema
        for item in data:
            assert "status" in item
            assert "confidence" in item
            assert "summary" in item
            assert "details" in item
            assert "date_compared" in item

    def test_feel_service_health_contract(self, client):
        """Test GET /api/v1/feel-vs-yesterday/health matches contract."""
        
        response = client.get("/api/v1/feel-vs-yesterday/health")
        
        # Health check should work without auth
        assert response.status_code == 200
        data = response.json()
        
        # Health response structure
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data
        assert data["status"] in ["healthy", "unhealthy"]

    def test_unauthorized_access_contract(self, client):
        """Test that endpoints require authentication."""
        
        # Test logs endpoints without auth
        response = client.get("/api/v1/logs/medications")
        assert response.status_code == 401
        
        response = client.post("/api/v1/logs/medications", json={})
        assert response.status_code == 401
        
        response = client.get("/api/v1/logs/symptoms")
        assert response.status_code == 401
        
        response = client.get("/api/v1/feel-vs-yesterday")
        assert response.status_code == 401


class TestContractParameterValidation:
    """Test parameter validation matches OpenAPI contract."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Create authorization headers."""
        payload = {
            "user_id": "test-user-123", 
            "sub": "test@example.com",
            "exp": datetime.now(timezone.utc).timestamp() + 3600
        }
        token = create_access_token(payload)
        return {"Authorization": f"Bearer {token}"}

    def test_pagination_parameters_contract(self, client, auth_headers):
        """Test pagination parameters match contract."""
        
        # Valid pagination
        response = client.get(
            "/api/v1/logs/medications",
            params={"limit": 10, "offset": 0},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Invalid limit (too high)
        response = client.get(
            "/api/v1/logs/medications",
            params={"limit": 1000},  # Should exceed max
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_date_parameters_contract(self, client, auth_headers):
        """Test date parameter validation."""
        
        valid_date = datetime.now(timezone.utc).isoformat()
        
        # Valid date
        response = client.get(
            "/api/v1/logs/medications",
            params={"start_date": valid_date},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Invalid date format
        response = client.get(
            "/api/v1/logs/medications",
            params={"start_date": "invalid-date"},
            headers=auth_headers
        )
        assert response.status_code == 422


# Example usage and testing
if __name__ == "__main__":
    print("✅ Contract tests for logs and feel-vs-yesterday endpoints created")
    print("Test coverage:")
    print("- Medication logs CRUD operations")
    print("- Symptom logs CRUD operations")  
    print("- Logs summary endpoint")
    print("- Feel vs yesterday analysis")
    print("- Feel vs yesterday history")
    print("- Parameter validation")
    print("- Authentication requirements")
    print("- Error response formats")
    print("")
    print("Run with: pytest backend/tests/contract/test_logs.py -v")
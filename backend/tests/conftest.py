"""
Test Configuration and Fixtures

This module provides shared test configuration, fixtures, and utilities
for the SaaS Medical Tracker test suite using pytest and httpx.
"""

import asyncio
import os
import tempfile
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import sessionmaker

from app.core.auth import create_access_token, create_password_hash
from app.core.config import get_settings
from app.main import create_app
from app.models.base import DatabaseManager, get_db_session

# Test settings
os.environ["TESTING"] = "true"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def settings():
    """Get test settings configuration."""
    return get_settings()


@pytest.fixture(scope="session")
def test_db():
    """Create a test database for the session."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    db_url = f"sqlite:///{db_path}"

    try:
        # Initialize database manager with test database
        db_manager = DatabaseManager(database_url=db_url, echo=False)

        # Create all tables
        db_manager.create_tables()

        yield db_manager

    finally:
        # Cleanup
        os.close(db_fd)
        os.unlink(db_path)


@pytest.fixture
def db_session(test_db):
    """
    Create a database session for a test.
    
    Uses a transaction that is rolled back after each test.
    """
    # Create a connection and transaction
    connection = test_db.engine.connect()
    transaction = connection.begin()

    # Create session bound to the connection
    session = sessionmaker(bind=connection)()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
async def app(test_db) -> FastAPI:
    """Create a FastAPI app configured for testing."""
    # Override database dependency
    def override_get_db():
        with test_db.get_session() as session:
            yield session

    # Create app
    test_app = create_app()

    # Override database dependency
    test_app.dependency_overrides[get_db_session] = override_get_db

    return test_app


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing the API."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as ac:
        yield ac


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!"
    }


@pytest.fixture
def sample_medication_data():
    """Sample medication data for testing."""
    return {
        "name": "Test Medication",
        "dosage": "100mg",
        "frequency": "Twice daily",
        "notes": "Take with food"
    }


@pytest.fixture
def sample_symptom_data():
    """Sample symptom log data for testing."""
    return {
        "symptom": "Headache",
        "severity": 7,
        "notes": "Started after lunch",
        "occurred_at": "2023-12-01T14:30:00Z"
    }


@pytest.fixture
def auth_token(sample_user_data):
    """Create a valid JWT token for testing authenticated endpoints."""
    token_data = {
        "sub": sample_user_data["email"],
        "user_id": "123e4567-e89b-12d3-a456-426614174000"
    }
    return create_access_token(token_data)


@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers for testing."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def hashed_password():
    """Create a hashed password for testing."""
    return create_password_hash("TestPassword123!")


class TestDatabase:
    """
    Test database context manager for integration tests.
    
    Provides isolated database instances for tests that need
    specific database state.
    """

    def __init__(self):
        self.db_path = None
        self.db_manager = None

    def __enter__(self):
        """Create a temporary test database."""
        db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)  # Close file descriptor, we only need the path

        db_url = f"sqlite:///{self.db_path}"
        self.db_manager = DatabaseManager(database_url=db_url, echo=False)
        self.db_manager.create_tables()

        return self.db_manager

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the test database."""
        if self.db_manager:
            self.db_manager.engine.dispose()

        if self.db_path and os.path.exists(self.db_path):
            os.unlink(self.db_path)


# Test utilities
class APITestClient:
    """
    Enhanced test client with convenience methods for API testing.
    """

    def __init__(self, client: AsyncClient):
        self.client = client
        self._auth_headers = None

    def set_auth(self, token: str):
        """Set authentication token for subsequent requests."""
        self._auth_headers = {"Authorization": f"Bearer {token}"}

    def clear_auth(self):
        """Clear authentication token."""
        self._auth_headers = None

    async def get(self, url: str, **kwargs):
        """GET request with optional authentication."""
        if self._auth_headers:
            headers = kwargs.get("headers", {})
            headers.update(self._auth_headers)
            kwargs["headers"] = headers
        return await self.client.get(url, **kwargs)

    async def post(self, url: str, **kwargs):
        """POST request with optional authentication."""
        if self._auth_headers:
            headers = kwargs.get("headers", {})
            headers.update(self._auth_headers)
            kwargs["headers"] = headers
        return await self.client.post(url, **kwargs)

    async def put(self, url: str, **kwargs):
        """PUT request with optional authentication."""
        if self._auth_headers:
            headers = kwargs.get("headers", {})
            headers.update(self._auth_headers)
            kwargs["headers"] = headers
        return await self.client.put(url, **kwargs)

    async def delete(self, url: str, **kwargs):
        """DELETE request with optional authentication."""
        if self._auth_headers:
            headers = kwargs.get("headers", {})
            headers.update(self._auth_headers)
            kwargs["headers"] = headers
        return await self.client.delete(url, **kwargs)


@pytest.fixture
async def api_client(client: AsyncClient) -> APITestClient:
    """Create an enhanced API test client."""
    return APITestClient(client)


# Test data factories
def create_test_user(**overrides):
    """Create test user data with optional field overrides."""
    default_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!"
    }
    default_data.update(overrides)
    return default_data


def create_test_medication(**overrides):
    """Create test medication data with optional field overrides."""
    default_data = {
        "name": "Test Medication",
        "dosage": "100mg",
        "frequency": "Twice daily",
        "notes": "Take with food"
    }
    default_data.update(overrides)
    return default_data


def create_test_symptom(**overrides):
    """Create test symptom data with optional field overrides."""
    default_data = {
        "symptom": "Headache",
        "severity": 7,
        "notes": "Started after lunch"
    }
    default_data.update(overrides)
    return default_data


# Test markers for pytest
pytest_plugins = ["pytest_asyncio"]

# Custom test markers
pytestmark = [
    pytest.mark.asyncio,  # Mark all tests as async by default
]


# Test configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "auth: mark test as requiring authentication")


# Example test to verify setup
async def test_fixtures_work(client: AsyncClient, settings):
    """Test that basic fixtures are working."""
    # Test settings fixture
    assert settings.ENVIRONMENT == "test"

    # Test client fixture
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    # Test that we get proper JSON response
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "unhealthy"]


if __name__ == "__main__":
    print("✅ Test configuration module loaded")
    print("Available fixtures:")
    print("- settings: Test settings configuration")
    print("- test_db: Test database manager")
    print("- db_session: Database session with rollback")
    print("- app: FastAPI app configured for testing")
    print("- client: Async HTTP client")
    print("- api_client: Enhanced API client with auth support")
    print("- auth_token: Valid JWT token")
    print("- auth_headers: Authorization headers")
    print("- sample_user_data: Sample user data")
    print("- sample_medication_data: Sample medication data")
    print("- sample_symptom_data: Sample symptom data")
    print("\nTest utilities:")
    print("- TestDatabase: Context manager for isolated DB tests")
    print("- APITestClient: Enhanced client with auth methods")
    print("- create_test_*(): Data factory functions")
    print("\nCustom markers:")
    print("- @pytest.mark.integration")
    print("- @pytest.mark.unit")
    print("- @pytest.mark.slow")
    print("- @pytest.mark.auth")

"""
Test Configuration and Fixtures

This module provides shared test configuration, fixtures, and utilities
for the SaaS Medical Tracker test suite using pytest and httpx.
"""

# ---------------------------------------------------------------------------
# Import Path Normalization
# ---------------------------------------------------------------------------
# We occasionally observed ModuleNotFoundError for `app.core.auth` during early
# import in pytest collection. To stabilise, ensure the project root (the
# directory containing `app/` and `tests/`) is at the front of sys.path.
# This defensive insertion is test-only and can be removed with proper
# packaging / editable install.
import sys, os
_here = os.path.dirname(__file__)
_project_root = os.path.abspath(os.path.join(_here, os.pardir))
_workspace_root = os.path.abspath(os.path.join(_project_root))  # same as project_root currently
_grandparent = os.path.abspath(os.path.join(_project_root, os.pardir))

for _candidate in (_project_root, _grandparent):
    if _candidate not in sys.path:
        sys.path.insert(0, _candidate)

# Debug (printed once) to help diagnose path issues if import keeps failing
if os.getenv('PYTEST_DEBUG_IMPORTS', '0') == '1':  # opt-in via env var
    print('[conftest] sys.path candidates inserted:', _project_root, _grandparent)
    print('[conftest] Final sys.path snippet:', [p for p in sys.path[:8]])

import asyncio
import os
import tempfile
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import sessionmaker

import importlib
try:
    _auth_mod = importlib.import_module('app.core.auth')
    create_access_token = getattr(_auth_mod, 'create_access_token')
    create_password_hash = getattr(_auth_mod, 'create_password_hash')
    _config_mod = importlib.import_module('app.core.config')
    get_settings = getattr(_config_mod, 'get_settings')
    _main_mod = importlib.import_module('app.main')
    create_app = getattr(_main_mod, 'create_app')
    _base_mod = importlib.import_module('app.models.base')
    DatabaseManager = getattr(_base_mod, 'DatabaseManager')
    get_db_session = getattr(_base_mod, 'get_db_session')
    init_database = getattr(_base_mod, 'init_database')
except ModuleNotFoundError as e:  # pragma: no cover
    import sys
    print('[conftest] Import failure:', e)
    print('[conftest] sys.path head:', sys.path[:10])
    raise


# ----------------------------------------------------------------------------
# Autouse isolated database fixture (function scope)
# ----------------------------------------------------------------------------
# Many contract tests import the FastAPI app directly (app.main.app) and do not
# request the test_db fixture. This caused 'Database not initialized' errors
# because lifespan events are not triggered when using httpx ASGITransport
# without lifespan handling. Additionally, tests expect a clean database state
# for each test (e.g. list empty, then create, then duplicate checks) so state
# leakage would make assertions flaky.
#
# This autouse fixture creates a fresh temporary SQLite database for every
# single test function, initializes the global db_manager via init_database,
# and creates the tables. After the test it disposes and deletes the database
# file. This guarantees isolation and ensures FastAPI dependencies that rely
# on get_database() work even when lifespan isn't executed.
# ----------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _isolated_db():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    db_url = f"sqlite:///{db_path}"

    try:
        db_manager = init_database(database_url=db_url, echo=False)
        db_manager.create_tables()
        yield db_manager
    finally:
        os.close(db_fd)
        try:
            db_manager.engine.dispose()
        except Exception:
            pass
        if os.path.exists(db_path):
            os.unlink(db_path)

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
    """Create a test database for the session and register it globally.

    We must use init_database() so FastAPI dependencies that call get_database()
    will see the global db_manager instead of raising 'Database not initialized'.
    """
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    db_url = f"sqlite:///{db_path}"

    try:
        # Initialize global database manager (sets module-level db_manager)
        db_manager = init_database(database_url=db_url, echo=False)
        # Create tables for tests (bypassing migrations)
        db_manager.create_tables()
        yield db_manager
    finally:
        os.close(db_fd)
        try:
            db_manager.engine.dispose()
        except Exception:
            pass
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

# Provide alias fixture name 'async_client' used by some integration tests
@pytest.fixture(name="async_client")
async def async_client_fixture(client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    yield client

# Synchronous TestClient fixture for contract tests expecting blocking interface
from fastapi.testclient import TestClient as _SyncTestClient

@pytest.fixture(name="sync_client")
def sync_client_fixture(app: FastAPI):
    return _SyncTestClient(app)


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

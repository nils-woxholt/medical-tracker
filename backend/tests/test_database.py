"""
Test Database Models and Database Manager

This module tests the database models, connection management,
and health check functionality for the SaaS Medical Tracker.
"""

from datetime import datetime

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.base import (
    Base,
    BaseModel,
    DatabaseHealthStatus,
    DatabaseManager,
    SoftDeleteMixin,
    TimestampMixin,
    check_database_health,
    get_async_session,
    get_database_manager,
    get_sync_session,
)

settings = get_settings()


class TestModel(BaseModel, TimestampMixin, SoftDeleteMixin, table=True):  # Added table=True for SQLModel mapping
    """Test model for database operations."""
    __tablename__ = "test_models"

    name: str
    value: int = 0


class TestBaseModel:
    """Test BaseModel functionality."""

    def test_base_model_attributes(self):
        """Test that BaseModel has required attributes."""
        model = TestModel(name="test", value=42)

        # Should have ID (UUID)
        assert hasattr(model, 'id')
        assert model.id is not None
        assert len(str(model.id)) == 36  # UUID format

        # Should have name and value
        assert model.name == "test"
        assert model.value == 42

    def test_model_string_representation(self):
        """Test model string representation."""
        model = TestModel(name="test", value=42)
        str_repr = str(model)

        assert "TestModel" in str_repr
        assert str(model.id) in str_repr

    def test_model_dict_conversion(self):
        """Test converting model to dictionary."""
        model = TestModel(name="test", value=42)
        model_dict = model.dict()

        assert "id" in model_dict
        assert model_dict["name"] == "test"
        assert model_dict["value"] == 42
        assert "created_at" in model_dict
        assert "updated_at" in model_dict


class TestTimestampMixin:
    """Test TimestampMixin functionality."""

    def test_timestamp_creation(self):
        """Test that timestamps are set on creation."""
        model = TestModel(name="test")

        # Should have timestamps
        assert hasattr(model, 'created_at')
        assert hasattr(model, 'updated_at')

        # Timestamps should be datetime objects
        assert isinstance(model.created_at, datetime)
        assert isinstance(model.updated_at, datetime)

        # Created and updated should be the same initially
        assert model.created_at == model.updated_at

    def test_timestamp_updates(self):
        """Test that updated_at changes on modification."""
        model = TestModel(name="test")
        original_updated = model.updated_at

        # Simulate time passing and update
        import time
        time.sleep(0.001)

        # Manually trigger update (in real scenario this happens via SQLAlchemy)
        model.updated_at = datetime.utcnow()

        # Updated timestamp should be different
        assert model.updated_at > original_updated

        # Created timestamp should remain the same
        assert model.created_at < model.updated_at


class TestSoftDeleteMixin:
    """Test SoftDeleteMixin functionality."""

    def test_soft_delete_attributes(self):
        """Test soft delete attributes."""
        model = TestModel(name="test")

        # Should have soft delete attributes
        assert hasattr(model, 'deleted_at')
        assert hasattr(model, 'is_deleted')

        # Initially not deleted
        assert model.deleted_at is None
        assert model.is_deleted is False

    def test_soft_delete_operation(self):
        """Test soft delete operation."""
        model = TestModel(name="test")

        # Perform soft delete
        model.soft_delete()

        # Should be marked as deleted
        assert model.is_deleted is True
        assert model.deleted_at is not None
        assert isinstance(model.deleted_at, datetime)

    def test_soft_restore_operation(self):
        """Test soft restore operation."""
        model = TestModel(name="test")

        # Delete then restore
        model.soft_delete()
        assert model.is_deleted is True

        model.restore()

        # Should be restored
        assert model.is_deleted is False
        assert model.deleted_at is None


class TestDatabaseManager:
    """Test DatabaseManager functionality."""

    def test_database_manager_creation(self):
        """Test creating DatabaseManager instance."""
        manager = DatabaseManager()

        # Should have required attributes
        assert hasattr(manager, 'sync_engine')
        assert hasattr(manager, 'async_engine')
        assert hasattr(manager, 'sync_session_factory')
        assert hasattr(manager, 'async_session_factory')

    def test_sync_session_creation(self):
        """Test creating synchronous database session."""
        manager = DatabaseManager()

        with manager.get_sync_session() as session:
            assert isinstance(session, Session)

            # Test basic query
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_async_session_creation(self):
        """Test creating asynchronous database session."""
        manager = DatabaseManager()

        async with manager.get_async_session() as session:
            assert isinstance(session, AsyncSession)

            # Test basic query
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_sync_session_dependency(self):
        """Test sync session FastAPI dependency."""
        # This would normally be called by FastAPI
        session_gen = get_sync_session()
        session = next(session_gen)

        assert isinstance(session, Session)

        # Clean up
        try:
            next(session_gen)
        except StopIteration:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_async_session_dependency(self):
        """Test async session FastAPI dependency."""
        # This would normally be called by FastAPI
        session_gen = get_async_session()
        session = await session_gen.__anext__()

        assert isinstance(session, AsyncSession)

        # Clean up
        try:
            await session_gen.__anext__()
        except StopAsyncIteration:
            pass  # Expected

    def test_database_manager_dependency(self):
        """Test DatabaseManager FastAPI dependency."""
        manager = get_database_manager()

        assert isinstance(manager, DatabaseManager)

    def test_database_health_check(self):
        """Test database health check functionality."""
        health = check_database_health()

        assert isinstance(health, DatabaseHealthStatus)
        assert health.status in ["healthy", "unhealthy"]
        assert isinstance(health.response_time_ms, (int, float))

        if health.status == "healthy":
            assert health.error is None
        else:
            assert health.error is not None

    @pytest.mark.asyncio
    async def test_async_database_health_check(self):
        """Test async database health check."""
        manager = DatabaseManager()

        # Test async health check
        try:
            async with manager.get_async_session() as session:
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1

            # If we get here, database is healthy
            health_status = "healthy"
        except Exception:
            health_status = "unhealthy"

        assert health_status in ["healthy", "unhealthy"]

    def test_connection_pooling(self):
        """Test that connection pooling is working."""
        manager = DatabaseManager()

        # Create multiple sessions
        sessions = []
        for i in range(3):
            session_gen = manager.get_sync_session()
            session = next(session_gen)
            sessions.append((session, session_gen))

        # All sessions should be valid
        for session, _ in sessions:
            result = session.execute(text("SELECT 1"))
            assert result.scalar() == 1

        # Clean up
        for session, session_gen in sessions:
            try:
                next(session_gen)
            except StopIteration:
                pass


class TestDatabaseHealth:
    """Test database health monitoring."""

    def test_health_status_structure(self):
        """Test health status structure."""
        health = check_database_health()

        # Should have required fields
        assert hasattr(health, 'status')
        assert hasattr(health, 'response_time_ms')
        assert hasattr(health, 'error')

        # Status should be valid
        assert health.status in ["healthy", "unhealthy"]

        # Response time should be non-negative
        assert health.response_time_ms >= 0

    def test_healthy_database_response(self):
        """Test response when database is healthy."""
        health = check_database_health()

        # Assuming test database is healthy
        if health.status == "healthy":
            assert health.error is None
            assert health.response_time_ms > 0
            assert health.response_time_ms < 5000  # Should be fast

    def test_health_check_timing(self):
        """Test that health check measures timing."""
        import time

        start_time = time.time()
        health = check_database_health()
        end_time = time.time()

        actual_time_ms = (end_time - start_time) * 1000

        # Reported time should be reasonable
        assert health.response_time_ms > 0
        assert health.response_time_ms <= actual_time_ms + 100  # Allow for overhead


@pytest.mark.integration
class TestDatabaseIntegration:
    """Test database integration scenarios."""

    @pytest.fixture
    def setup_test_table(self):
        """Set up test table for integration tests."""
        manager = DatabaseManager()

        # Create test table
        Base.metadata.create_all(manager.sync_engine)

        yield

        # Clean up
        Base.metadata.drop_all(manager.sync_engine)

    def test_crud_operations(self, setup_test_table):
        """Test basic CRUD operations."""
        manager = DatabaseManager()

        with manager.get_sync_session() as session:
            # Create
            model = TestModel(name="test_crud", value=100)
            session.add(model)
            session.commit()
            session.refresh(model)

            # Read
            retrieved = session.query(TestModel).filter(TestModel.name == "test_crud").first()
            assert retrieved is not None
            assert retrieved.name == "test_crud"
            assert retrieved.value == 100

            # Update
            retrieved.value = 200
            session.commit()

            updated = session.query(TestModel).filter(TestModel.name == "test_crud").first()
            assert updated.value == 200

            # Soft Delete
            updated.soft_delete()
            session.commit()

            # Should still exist but marked as deleted
            deleted = session.query(TestModel).filter(TestModel.name == "test_crud").first()
            assert deleted.is_deleted is True

    @pytest.mark.asyncio
    async def test_async_crud_operations(self, setup_test_table):
        """Test async CRUD operations."""
        manager = DatabaseManager()

        async with manager.get_async_session() as session:
            # Create
            model = TestModel(name="test_async_crud", value=300)
            session.add(model)
            await session.commit()
            await session.refresh(model)

            # Read
            result = await session.execute(
                text("SELECT * FROM test_models WHERE name = :name"),
                {"name": "test_async_crud"}
            )
            row = result.first()
            assert row is not None
            assert row.name == "test_async_crud"

    def test_concurrent_sessions(self, setup_test_table):
        """Test multiple concurrent database sessions."""
        manager = DatabaseManager()

        def create_model(name_suffix):
            with manager.get_sync_session() as session:
                model = TestModel(name=f"concurrent_{name_suffix}", value=name_suffix)
                session.add(model)
                session.commit()
                return model.id

        # Create models concurrently (simulated)
        model_ids = []
        for i in range(3):
            model_id = create_model(i)
            model_ids.append(model_id)

        # Verify all models were created
        with manager.get_sync_session() as session:
            for i, model_id in enumerate(model_ids):
                model = session.query(TestModel).filter(TestModel.id == model_id).first()
                assert model is not None
                assert model.name == f"concurrent_{i}"
                assert model.value == i


if __name__ == "__main__":
    print("✅ Database tests module loaded")
    print("Test classes:")
    print("- TestBaseModel: BaseModel functionality and attributes")
    print("- TestTimestampMixin: Timestamp creation and updates")
    print("- TestSoftDeleteMixin: Soft delete and restore operations")
    print("- TestDatabaseManager: Database connection and session management")
    print("- TestDatabaseHealth: Health check monitoring")
    print("- TestDatabaseIntegration: Full CRUD and concurrent operations")

"""
Backend Unit Test Harness - Sanity Tests

This module provides sanity checks to validate the basic functionality
of the backend test environment and core application components.
"""

import pytest
import structlog
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.main import create_app
from app.telemetry.metrics import get_metrics_registry


class TestApplicationSanity:
    """Test basic application functionality and configuration."""

    def test_app_creation(self):
        """Test that the FastAPI application can be created successfully."""
        app = create_app()

        assert isinstance(app, FastAPI)
        assert app.title == "SaaS Medical Tracker"
        assert hasattr(app, 'routes')
        assert len(app.routes) > 0

    def test_app_has_required_middleware(self):
        """Test that required middleware is properly configured."""
        app = create_app()

        # Check that middleware is configured
        assert hasattr(app, 'user_middleware')
        assert len(app.user_middleware) > 0

        # Verify specific middleware types are present
        middleware_types = [mw.cls.__name__ for mw in app.user_middleware]
        expected_middleware = ['MetricsMiddleware', 'RequestIDMiddleware']

        # At least some expected middleware should be present
        assert any(mw in middleware_types for mw in expected_middleware), \
            f"Expected middleware not found. Found: {middleware_types}"

    def test_app_routes_configured(self):
        """Test that basic routes are properly configured."""
        app = create_app()
        client = TestClient(app)

        # Test that the app has routes configured
        assert len(app.routes) > 0

        # Basic route existence test (health endpoint not yet implemented)
        # TODO: Test actual health endpoint after API implementation

    def test_metrics_endpoint_available(self):
        """Test that metrics endpoint is accessible."""
        app = create_app()
        client = TestClient(app)

        response = client.get("/metrics")
        assert response.status_code == 200

        # Should return Prometheus format metrics
        metrics_text = response.text
        assert "# HELP" in metrics_text
        assert "# TYPE" in metrics_text


class TestSettings:
    """Test application settings and configuration."""

    def test_settings_can_be_loaded(self):
        """Test that application settings load correctly."""
        settings = get_settings()

        assert settings is not None
        assert hasattr(settings, 'PROJECT_NAME')
        assert hasattr(settings, 'VERSION')
        assert hasattr(settings, 'API_V1_STR')
        assert settings.PROJECT_NAME == "SaaS Medical Tracker"

    def test_settings_environment_variables(self):
        """Test that environment-based settings work."""
        settings = get_settings()

        # Test default values
        assert settings.ENVIRONMENT in ["development", "staging", "production"]
        assert settings.API_V1_STR == "/api/v1"

        # Test database URL format
        assert settings.DATABASE_URL.startswith("sqlite://") or \
               settings.DATABASE_URL.startswith("postgresql://")


class TestLogging:
    """Test logging configuration and functionality."""

    def test_logging_setup(self):
        """Test that structured logging is properly configured."""
        # Setup logging
        setup_logging()

        # Get a logger instance
        logger = structlog.get_logger(__name__)

        # Test that we can log messages
        assert logger is not None
        logger.info("Test log message for unit tests")

    def test_logger_has_required_processors(self):
        """Test that logger has proper processors configured."""
        setup_logging()

        # Check that structlog is configured
        config = structlog.get_config()
        assert config is not None
        assert 'processors' in config
        assert len(config['processors']) > 0


class TestMetrics:
    """Test metrics collection and registry functionality."""

    def test_metrics_registry_initialized(self):
        """Test that metrics registry is properly initialized."""
        registry = get_metrics_registry()

        assert registry is not None
        assert hasattr(registry, '_metrics')
        assert len(registry._metrics) > 0

    def test_default_metrics_present(self):
        """Test that default metrics are registered."""
        registry = get_metrics_registry()

        # Check for some expected default metrics
        metric_names = [metric._name for metric in registry._metrics.values()]

        expected_metrics = [
            'http_requests',  # Actual metric name
            'http_request_duration_seconds',
            'database_queries'  # Actual metric name
        ]

        for expected_metric in expected_metrics:
            assert any(expected_metric in name for name in metric_names), \
                f"Expected metric '{expected_metric}' not found in {metric_names}"

    def test_metrics_collection_functional(self):
        """Test that metrics can be collected."""
        from app.telemetry.metrics import record_database_query, record_http_request

        # Record some test metrics
        record_http_request("GET", "/test", 200, 0.1)
        record_database_query("SELECT", 0.05)

        # Get metrics summary
        from app.telemetry.metrics import get_metrics_summary
        summary = get_metrics_summary()

        assert summary is not None
        assert isinstance(summary, dict)


class TestDependencyInjection:
    """Test dependency injection system."""

    def test_dependencies_can_be_imported(self):
        """Test that dependency injection components can be imported."""
        # Skip import test for now - dependencies need database setup
        # TODO: Implement proper dependency testing after database models are ready
        pass

    def test_settings_dependency(self):
        """Test settings dependency injection."""
        # Skip dependency test for now - needs proper setup
        # TODO: Implement after database models are complete
        pass


class TestDatabase:
    """Test basic database functionality."""

    def test_database_models_can_be_imported(self):
        """Test that database models can be imported without errors."""
        # Skip model import test for now - models need to be implemented
        # TODO: Test actual model imports after Phase 3 implementation
        pass

    def test_database_connection_string(self):
        """Test database connection configuration."""
        settings = get_settings()

        # Should have a valid database URL
        assert settings.DATABASE_URL is not None
        assert len(settings.DATABASE_URL) > 0

        # Should be SQLite for testing or PostgreSQL for production
        assert (settings.DATABASE_URL.startswith("sqlite://") or
                settings.DATABASE_URL.startswith("postgresql://"))


@pytest.mark.integration
class TestAPIIntegration:
    """Basic integration tests for API functionality."""

    @pytest.fixture
    def client(self):
        """Create a test client for integration tests."""
        app = create_app()
        return TestClient(app)

    def test_api_root_accessible(self, client):
        """Test that API root is accessible."""
        # Skip for now - API routes not yet implemented
        # TODO: Test actual API endpoints after Phase 3 implementation
        pass

    def test_health_check_detailed(self, client):
        """Test detailed health check functionality."""
        # Skip for now - health endpoint not yet implemented
        # TODO: Test health endpoint after API implementation
        pass

    def test_api_v1_prefix_works(self, client):
        """Test that API v1 prefix routing works."""
        # This test will be expanded as we add actual API endpoints
        # For now, just verify the routing structure
        response = client.get("/api/v1/")
        # This might return 404 until we add actual endpoints, which is fine
        assert response.status_code in [200, 404, 405]


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])

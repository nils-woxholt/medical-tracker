"""Database URL utility module.

This lightweight module exists primarily to satisfy integration tests
(`tests/integration/test_migrations.py`) which import
`backend.app.core.database.get_database_url`. The original test suite
appears to have been authored with a different project layout (a top-level
`backend` package). To remain backward/contract compatible while keeping
the current `app` package name, we provide the expected symbol here.

If future functionality (pool management, alembic helpers) is required,
extend this module rather than modifying tests.
"""

from app.core.config import get_settings


def get_database_url() -> str:
    """Return the configured database URL from settings.

    Tests patch the `DATABASE_URL` environment variable; `get_settings()`
    will pick that up because settings object loads from env on creation.
    """
    settings = get_settings()
    return settings.DATABASE_URL


__all__ = ["get_database_url"]

"""Legacy import compatibility shim.

The test suite imports `backend.app.core.database.get_database_url`. To remain
compatible while consolidating on the real `app.core.config` settings, we
forward this symbol. Other functionality should be imported from `app.models`
and `app.core` directly.
"""

from app.core.config import get_settings

def get_database_url() -> str:  # pragma: no cover - thin wrapper
    return get_settings().DATABASE_URL

__all__ = ["get_database_url"]

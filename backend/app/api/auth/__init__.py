"""Authentication API package initialization.

Defines the auth router exposed by the application. Individual endpoint modules
will be added during subsequent phases (login, logout, register, session, demo).
"""

from fastapi import APIRouter, HTTPException, status

auth_router = APIRouter(prefix="/auth", tags=["auth"])

# Versioned placeholder router to satisfy legacy tests expecting 501 at /api/v1/auth/register
versioned_auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth-v1"])

@versioned_auth_router.post("/register", include_in_schema=False)
def placeholder_register_v1():
	# Accept any body and always return Not Implemented for legacy contract tests
	raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not yet implemented")

# Import endpoint modules so their route decorators execute
from . import login  # noqa: F401
from . import logout  # noqa: F401
from . import register  # noqa: F401
from . import session  # noqa: F401
from . import demo  # noqa: F401

# Expose routers for inclusion in main app
__all__ = ["auth_router", "versioned_auth_router"]


"""Placeholder combined auth routes module.

During implementation we may split endpoints into separate files for clarity
 (e.g., login.py, register.py, session.py, demo.py, logout.py). For now we keep
 a placeholder to satisfy scaffolding task T001.
"""

from . import auth_router

@auth_router.get("/health")
async def auth_health():
    """Lightweight placeholder endpoint to verify router inclusion.

    This will be removed once real auth endpoints are implemented.
    """
    return {"status": "auth-router-initialized"}

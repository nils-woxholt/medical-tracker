"""Application package root.

Previously imported create_app at module import time causing side effects during
Alembic migrations (loading full FastAPI app and failing on route dependencies).
Tests import create_app directly from app.main instead.
"""

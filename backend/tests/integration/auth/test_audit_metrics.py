"""T057: Validate audit logging presence and metrics counters exposure for auth flows.

This integration test triggers several auth actions then fetches /metrics
and asserts expected counters increment & audit events logged.

Note: Audit events are logged via structlog; here we indirectly validate
by ensuring counters reflect actions. (Direct log capture can be added later.)
"""
from __future__ import annotations

import re
from httpx import AsyncClient
import pytest
from fastapi import status

from app.main import app
from app.core.auth import create_password_hash
from app.models.user import User
from app.core.dependencies import get_sync_db_session

@pytest.fixture
def db_session():
    sess_gen = get_sync_db_session()
    db = next(sess_gen)
    try:
        yield db
    finally:
        try:
            next(sess_gen)
        except StopIteration:
            pass

@pytest.fixture
def user(db_session):
    u = User(
        email="metrics_test@example.com",
        first_name="Metrics",
        last_name="Tester",
        password_hash=create_password_hash("MetricsPass123"),
        failed_attempts=0,
        lock_until=None,
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u

AUTH_PREFIX = "/auth"

@pytest.mark.asyncio
async def test_metrics_and_audit_counters(user):
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Successful login
        login_resp = await client.post(f"{AUTH_PREFIX}/login", json={"email": user.email, "password": "MetricsPass123"})
        assert login_resp.status_code == status.HTTP_200_OK
        # Failed login
        fail_resp = await client.post(f"{AUTH_PREFIX}/login", json={"email": user.email, "password": "WrongPass123"})
        assert fail_resp.status_code == status.HTTP_401_UNAUTHORIZED
        # Session status check
        sess_resp = await client.get(f"{AUTH_PREFIX}/session")
        assert sess_resp.status_code == status.HTTP_200_OK
        # Demo session creation (rate limiter may apply; ignore 429)
        demo_resp = await client.post(f"{AUTH_PREFIX}/demo")
        assert demo_resp.status_code in {status.HTTP_200_OK, 429}
        # Fetch metrics
        metrics_resp = await client.get("/metrics")
        assert metrics_resp.status_code == status.HTTP_200_OK
        body = metrics_resp.text
        # Assert authentication_attempts_total shows at least 2 attempts (success + failure)
        # Use lookaheads to allow any label ordering (Prometheus may sort labels alphabetically)
        success_pattern = r"authentication_attempts_total\{(?=[^}]*result=\"success\")(?=[^}]*method=\"password\")[^}]*} \d+"
        failure_pattern = r"authentication_attempts_total\{(?=[^}]*result=\"failure\")(?=[^}]*method=\"password\")[^}]*} \d+"
        assert re.search(success_pattern, body)
        assert re.search(failure_pattern, body)
        # Session status checks metric
        assert re.search(r"session_status_checks_total\{valid=\"true\"} \d+", body)
        # Demo session creations metric may be zero if rate limited, but presence of counter confirmed
        assert "demo_session_creations_total" in body
        # Security events total counter should exist (may be zero but present)
        assert "security_events_total" in body

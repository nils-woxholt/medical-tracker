"""Tests for password hashing utilities and lockout state transitions (T028)."""

from datetime import datetime, timedelta

from app.core.auth import create_password_hash, verify_password
from app.services.lockout import register_failed_attempt, register_success, is_locked, LOCK_THRESHOLD, LOCK_DURATION_MINUTES
from app.models.user import User


def _new_user() -> User:
    return User(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        password_hash=create_password_hash("ValidPass123"),
        failed_attempts=0,
        lock_until=None,
        is_active=True,
    )


def test_password_hash_and_verify_round_trip():
    hashed = create_password_hash("SomePwd123")
    assert hashed != "SomePwd123"
    assert verify_password("SomePwd123", hashed) is True
    assert verify_password("WrongPwd123", hashed) is False


def test_lockout_trigger_and_duration():
    user = _new_user()
    # Trigger failed attempts until threshold reached
    for i in range(LOCK_THRESHOLD):
        register_failed_attempt(user)
    assert user.failed_attempts == LOCK_THRESHOLD
    assert user.lock_until is not None
    assert is_locked(user) is True
    # Attempts while locked should not change counters
    prev_lock_until = user.lock_until
    register_failed_attempt(user)
    assert user.failed_attempts == LOCK_THRESHOLD
    assert user.lock_until == prev_lock_until


def test_lockout_expires_and_reset_on_success():
    user = _new_user()
    for _ in range(LOCK_THRESHOLD):
        register_failed_attempt(user)
    assert is_locked(user)
    # Simulate lock expiration
    assert user.lock_until is not None
    user.lock_until = datetime.utcnow() - timedelta(minutes=1)
    # Next success should reset counters
    register_success(user)
    assert user.failed_attempts == 0
    assert user.lock_until is None
    assert is_locked(user) is False

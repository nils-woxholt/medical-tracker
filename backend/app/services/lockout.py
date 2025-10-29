"""Lockout evaluation helper.

Encapsulates logic for incrementing failed attempts and determining whether
the user account is currently locked per policy (5 attempts -> 15 minute lock).
"""

from datetime import datetime, timedelta
from app.models.user import User

LOCK_THRESHOLD = 5
LOCK_DURATION_MINUTES = 15

def is_locked(user: User) -> bool:
    if user.lock_until and datetime.utcnow() < user.lock_until:
        return True
    return False

def register_failed_attempt(user: User) -> None:
    """Mutate user after a failed login attempt according to state machine."""
    now = datetime.utcnow()
    # If lock expired, reset counters first
    if user.lock_until and now >= user.lock_until:
        user.failed_attempts = 0
        user.lock_until = None

    if is_locked(user):  # still locked, no change
        return

    if user.failed_attempts < LOCK_THRESHOLD - 1:
        user.failed_attempts += 1
    else:
        # Trigger lock
        user.failed_attempts = LOCK_THRESHOLD
        user.lock_until = now + timedelta(minutes=LOCK_DURATION_MINUTES)

def register_success(user: User) -> None:
    """Reset lockout counters on successful authentication if not locked."""
    # If lock expired naturally, treat as reset
    if user.lock_until and datetime.utcnow() >= user.lock_until:
        user.lock_until = None
    user.failed_attempts = 0

__all__ = ["is_locked", "register_failed_attempt", "register_success"]
"""Duplicate submission guard for login attempts (T023).

Provides a simple in-memory guard to prevent concurrent or rapidly repeated
submissions for the same normalized email. This is a best-effort UX
protection (not a security mechanism) to avoid double form submissions
resulting in multiple sessions being created.

Design:
- Uses a process-local dict mapping key -> lock counter.
- Context manager acquires if absent; if present, raises DuplicateInFlight.
- Always releases key on context exit to avoid starvation.

NOTE: For a multi-process deployment this should be replaced with a
distributed lock (e.g., Redis SET NX with short TTL). For MVP single process
operation this suffices.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Dict, Set
import threading

_active: Set[str] = set()
_lock = threading.Lock()


class DuplicateInFlight(Exception):
    """Raised when a duplicate submission is already being processed."""


@contextmanager
def guard(email_key: str):
    acquired = False
    with _lock:
        if email_key in _active:
            raise DuplicateInFlight()
        _active.add(email_key)
        acquired = True
    try:
        yield
    finally:
        if acquired:
            with _lock:
                _active.discard(email_key)

__all__ = ["guard", "DuplicateInFlight"]

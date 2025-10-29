"""Placeholder rate limiting integration (T056).

Provides an in-memory simplistic rate limiter to demonstrate where integration
with a production system (Redis, external gateway) would occur. Not robust and
intended only for development / demonstration.
"""
from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Deque, Dict

WINDOW_SECONDS = 60
MAX_EVENTS = 30  # arbitrary demo threshold

_events: Dict[str, Deque[datetime]] = defaultdict(deque)

def allow(key: str) -> bool:
    now = datetime.utcnow()
    q = _events[key]
    # prune old
    cutoff = now - timedelta(seconds=WINDOW_SECONDS)
    while q and q[0] < cutoff:
        q.popleft()
    if len(q) >= MAX_EVENTS:
        return False
    q.append(now)
    return True

__all__ = ["allow"]

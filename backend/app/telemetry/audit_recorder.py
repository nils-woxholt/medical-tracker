"""Audit event recording utilities for authentication flows.

Provides a lightweight abstraction over the existing structured logging
infrastructure so application code can emit consistent, parseable audit
events without duplicating field mapping.

Events follow naming from research & spec:
  - auth.login.success
  - auth.login.failure
  - auth.lockout.trigger
  - auth.register.success
  - auth.logout
  - auth.demo.start

Each audit event includes a minimal field set for correlation:
  event_type: str (one of above)
  user_id: Optional[str]
  session_id: Optional[str]
  ip_hash: Optional[str] (hashed client IP for privacy – simple SHA256 hex)
  attempt_count: Optional[int]
  locked_until: Optional[datetime]
  demo: Optional[bool]
  meta: dict (extensible)

Note: This implementation intentionally avoids persistence (no AuditEvent table)
per MVP scope; structured logs can be shipped to an external system.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from hashlib import sha256
from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger("audit")


def _hash_ip(ip: Optional[str]) -> Optional[str]:
    if not ip:
        return None
    return sha256(ip.encode("utf-8")).hexdigest()


@dataclass
class AuditEvent:
    event_type: str
    occurred_at: datetime = datetime.utcnow()
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_hash: Optional[str] = None
    attempt_count: Optional[int] = None
    locked_until: Optional[datetime] = None
    demo: Optional[bool] = None
    meta: Dict[str, Any] | None = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Convert datetimes to isoformat for logging
        data["occurred_at"] = self.occurred_at.isoformat()
        if data.get("locked_until"):
            data["locked_until"] = self.locked_until.isoformat()  # type: ignore
        return data


class AuditRecorder:
    """Emit structured audit events for auth-related actions."""

    VALID_EVENTS = {
        "auth.login.success",
        "auth.login.failure",
        "auth.lockout.trigger",
        "auth.register.success",
        "auth.logout",
        "auth.demo.start",
    }

    def record(
        self,
        event_type: str,
        *,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip: Optional[str] = None,
        attempt_count: Optional[int] = None,
        locked_until: Optional[datetime] = None,
        demo: Optional[bool] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        if event_type not in self.VALID_EVENTS:
            raise ValueError(f"Unknown audit event: {event_type}")
        evt = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            ip_hash=_hash_ip(ip),
            attempt_count=attempt_count,
            locked_until=locked_until,
            demo=demo,
            meta=meta or {},
        )
        logger.info("audit_event", **evt.to_dict())
        return evt


_recorder = AuditRecorder()


def get_audit_recorder() -> AuditRecorder:
    return _recorder

__all__ = ["AuditRecorder", "get_audit_recorder"]

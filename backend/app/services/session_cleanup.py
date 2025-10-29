"""Session cleanup task (T053).

Provides a function to purge revoked or expired sessions beyond a grace period.
In production this would be scheduled (cron/job runner). For now exposed as a
callable utility that can be triggered manually or via a future management endpoint.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.orm import Session as SASession
from sqlmodel import Session, select

from app.models.session import Session as SessionModel

GRACE_MINUTES = 10  # retain revoked/expired for brief forensic window

def cleanup_expired_sessions(db: SASession | Session) -> int:
    cutoff = datetime.utcnow() - timedelta(minutes=GRACE_MINUTES)
    # Select sessions that are either revoked or expired before cutoff
    from sqlalchemy import or_
    stmt = select(SessionModel).where(
        or_(SessionModel.revoked_at.isnot(None), SessionModel.expires_at < cutoff)
    )
    if isinstance(db, Session):
        sessions = db.exec(stmt).all()
    else:
        sessions = db.execute(stmt).scalars().all()
    removed = 0
    for sess in sessions:
        db.delete(sess)
        removed += 1
    if removed:
        db.commit()
    return removed

__all__ = ["cleanup_expired_sessions"]

"""Session service operations."""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session as SASession
from sqlmodel import Session, select

from app.models.session import Session as SessionModel

class SessionService:
    def __init__(self, db: SASession | Session):
        self.db = db

    def create(self, *, user_id: str, demo: bool = False) -> SessionModel:
        sess = SessionModel(user_id=user_id, demo=demo)
        self.db.add(sess)
        self.db.commit()
        self.db.refresh(sess)
        return sess

    def get(self, session_id: str) -> Optional[SessionModel]:
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        if isinstance(self.db, Session):
            return self.db.exec(stmt).first()
        else:
            return self.db.execute(stmt).scalars().first()

    def touch(self, sess: SessionModel) -> SessionModel:
        sess.touch()
        self.db.add(sess)
        self.db.commit()
        self.db.refresh(sess)
        return sess

    def revoke(self, sess: SessionModel) -> SessionModel:
        sess.revoke()
        self.db.add(sess)
        self.db.commit()
        self.db.refresh(sess)
        return sess

__all__ = ["SessionService"]
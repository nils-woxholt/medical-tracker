from sqlmodel import SQLModel, Field, Session, create_engine
from app.services.active_guard import ensure_active, GuardInactiveError
import pytest

class DemoMaster(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    is_active: bool = True


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


def test_ensure_active_pass():
    engine = setup_db()
    with Session(engine) as session:
        m = DemoMaster(name="A", is_active=True)
        session.add(m)
        session.commit()
        session.refresh(m)
        fetched = ensure_active(session, DemoMaster, m.id)
        assert fetched.id == m.id


def test_ensure_active_inactive():
    engine = setup_db()
    with Session(engine) as session:
        m = DemoMaster(name="B", is_active=False)
        session.add(m)
        session.commit()
        session.refresh(m)
        with pytest.raises(GuardInactiveError):
            ensure_active(session, DemoMaster, m.id)


def test_ensure_active_missing():
    engine = setup_db()
    with Session(engine) as session:
        with pytest.raises(GuardInactiveError):
            ensure_active(session, DemoMaster, 999)

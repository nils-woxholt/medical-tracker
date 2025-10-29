"""Integration tests for Feature 004 migration constraints (T024).

Verifies database-level enforcement of:
  * severity/impact scale 1..10
  * duration_minutes 1..1440 and >720 requires confirmation flag
  * foreign key integrity (symptom_type_id must exist)
"""
from datetime import datetime, timezone
import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import event

# Import models built in Feature 004
from app.models.symptom_type import SymptomType
from app.models.symptom_log import SymptomLog

TZ = timezone.utc

@pytest.fixture(scope="module")
def engine():
    # Use in-memory SQLite with foreign keys enabled
    eng = create_engine("sqlite:///:memory:")

    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SQLModel.metadata.create_all(eng)
    return eng

@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _insert_symptom_log(session: Session, **fields):
    """Helper to insert SymptomLog directly (bypassing service logic).

    Rolls back session if integrity error occurs so caller can continue using session.
    """
    log = SymptomLog(**fields)
    session.add(log)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    session.refresh(log)
    return log


def test_valid_insert(session):
    st = SymptomType(
        user_id="u1",
        name="Headache",
        default_severity_numeric=5,
        default_impact_numeric=4,
        active=True,
    )
    session.add(st)
    session.commit()
    session.refresh(st)
    log = _insert_symptom_log(
        session,
        user_id="u1",
        symptom_type_id=st.id,
        severity_numeric=5,
        impact_numeric=4,
        severity_label="Moderate",
        impact_label="Moderate",
        started_at=datetime.now(TZ),
        duration_minutes=30,
        confirmation_long_duration=False,
        notes="Initial log",
    )
    assert log.id is not None
    assert log.duration_minutes == 30


def test_invalid_severity_out_of_range(session):
    st = SymptomType(
        user_id="u2",
        name="Nausea",
        default_severity_numeric=4,
        default_impact_numeric=3,
        active=True,
    )
    session.add(st)
    session.commit()
    session.refresh(st)
    with pytest.raises(Exception):
        _insert_symptom_log(
            session,
            user_id="u2",
            symptom_type_id=st.id,
            severity_numeric=11,  # invalid (check constraint)
            impact_numeric=4,
            severity_label="Critical",
            impact_label="Moderate",
            started_at=datetime.now(TZ),
            duration_minutes=10,
            confirmation_long_duration=False,
        )


def test_invalid_duration_over_1440(session):
    st = SymptomType(
        user_id="u3",
        name="Fatigue",
        default_severity_numeric=3,
        default_impact_numeric=2,
        active=True,
    )
    session.add(st)
    session.commit()
    session.refresh(st)
    with pytest.raises(Exception):
        _insert_symptom_log(
            session,
            user_id="u3",
            symptom_type_id=st.id,
            severity_numeric=3,
            impact_numeric=2,
            severity_label="Mild",
            impact_label="Mild",
            started_at=datetime.now(TZ),
            duration_minutes=1441,  # invalid (exceeds max)
            confirmation_long_duration=True,
        )


def test_long_duration_requires_confirmation(session):
    st = SymptomType(
        user_id="u4",
        name="Dizziness",
        default_severity_numeric=6,
        default_impact_numeric=5,
        active=True,
    )
    session.add(st)
    session.commit()
    session.refresh(st)
    # Expect failure when >720 without confirmation
    with pytest.raises(Exception):
        _insert_symptom_log(
            session,
            user_id="u4",
            symptom_type_id=st.id,
            severity_numeric=6,
            impact_numeric=5,
            severity_label="Moderate",
            impact_label="Moderate",
            started_at=datetime.now(TZ),
            duration_minutes=900,
            confirmation_long_duration=False,  # missing required True
        )
    # Should succeed when confirmation flag True
    log = _insert_symptom_log(
        session,
        user_id="u4",
        symptom_type_id=st.id,
        severity_numeric=6,
        impact_numeric=5,
        severity_label="Moderate",
        impact_label="Moderate",
        started_at=datetime.now(TZ),
        duration_minutes=900,
        confirmation_long_duration=True,
    )
    assert log.id is not None


def test_foreign_key_symptom_type_missing(session):
    # Attempt insert referencing non-existent symptom_type_id
    with pytest.raises(Exception):
        _insert_symptom_log(
            session,
            user_id="u5",
            symptom_type_id=9999,
            severity_numeric=2,
            impact_numeric=2,
            severity_label="Mild",
            impact_label="Mild",
            started_at=datetime.now(TZ),
            duration_minutes=15,
            confirmation_long_duration=False,
        )

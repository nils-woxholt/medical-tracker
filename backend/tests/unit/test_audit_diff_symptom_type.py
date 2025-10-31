"""Unit tests for SymptomTypeService audit diff generation.

Validates that create/update/deactivate produce expected AuditEntry.diff structure.
"""
from __future__ import annotations

from sqlmodel import Session, select
import pytest

from app.models.audit_entry import AuditEntry  # type: ignore[attr-defined]
from app.services.symptom_type_service import SymptomTypeService
from app.models.symptom_type import SymptomTypeCreate, SymptomTypeUpdate

USER_ID = "audit-user-1"

@pytest.fixture
def service(db_session: Session) -> SymptomTypeService:
    return SymptomTypeService(session=db_session, user_id=USER_ID)


def _get_audits(session: Session):
    """Retrieve audit entries regardless of Session type.

    SQLModel Session provides .exec; plain SQLAlchemy Session provides .execute.
    Tests use the raw SQLAlchemy Session fixture, so we need a compatibility fallback.
    """
    stmt = select(AuditEntry)
    try:
        return list(session.exec(stmt))  # type: ignore[attr-defined]
    except AttributeError:
        return list(session.execute(stmt).scalars())


@pytest.mark.anyio
async def test_audit_diff_on_create(service: SymptomTypeService, db_session: Session):
    create_payload = SymptomTypeCreate(
        name="Headache",
        description="Throbbing pain",
        default_severity_numeric=5,
        default_impact_numeric=4,
    )
    entity = service.create(create_payload)
    db_session.commit()

    audits = _get_audits(db_session)
    assert len(audits) == 1
    entry = audits[0]
    assert entry.action == "create"
    assert entry.entity_id == entity.id
    diff = entry.diff
    assert diff is not None
    # On create all snapshot fields appear with before None
    expected_fields = {"name", "description", "category", "default_severity_numeric", "default_impact_numeric", "active"}
    assert set(diff.keys()) == expected_fields
    for field, change in diff.items():
        assert "before" in change and "after" in change
        # category is None both sides; may be excluded if identical, ensure rule
        if field == "category":
            # category absent change may be None->None; allow either presence or skip
            pass
        else:
            assert change["before"] is None
            assert change["after"] is not None


@pytest.mark.anyio
async def test_audit_diff_on_update(service: SymptomTypeService, db_session: Session):
    # seed
    entity = service.create(
        SymptomTypeCreate(
            name="Nausea",
            description="Baseline nausea",
            default_severity_numeric=3,
            default_impact_numeric=2,
        )
    )
    db_session.commit()

    update_payload = SymptomTypeUpdate(name="Severe Nausea", default_severity_numeric=7)
    service.update(entity.id, update_payload)  # type: ignore[arg-type]
    db_session.commit()

    audits = _get_audits(db_session)
    # Two audits (create + update)
    assert len(audits) == 2
    update_entry = audits[-1]
    assert update_entry.action == "update"
    diff = update_entry.diff
    assert diff is not None
    assert set(diff.keys()) == {"name", "default_severity_numeric"}
    assert diff["name"]["before"] == "Nausea" and diff["name"]["after"] == "Severe Nausea"
    assert diff["default_severity_numeric"]["before"] == 3 and diff["default_severity_numeric"]["after"] == 7


@pytest.mark.anyio
async def test_audit_diff_on_deactivate(service: SymptomTypeService, db_session: Session):
    entity = service.create(
        SymptomTypeCreate(
            name="Dizziness",
            description="Occasional dizziness",
            default_severity_numeric=4,
            default_impact_numeric=3,
        )
    )
    db_session.commit()

    service.deactivate(entity.id)  # type: ignore[arg-type]
    db_session.commit()

    audits = _get_audits(db_session)
    # Two audits (create + deactivate)
    assert len(audits) == 2
    deactivate_entry = audits[-1]
    assert deactivate_entry.action == "deactivate"
    diff = deactivate_entry.diff
    assert diff is not None
    # Only active should change
    assert set(diff.keys()) == {"active"}
    assert diff["active"]["before"] is True and diff["active"]["after"] is False

"""Consolidated migration integration tests.

Validates the single-base consolidated migration revision can:
* Apply cleanly to an empty database
* Provide expected tables (baseline presence check)
* Downgrade (drop tables) and re-upgrade deterministically
* Remain idempotent (re-running upgrade does not alter schema)

The previous multi-step rollback chain tests have been removed as we now
maintain a clean initial schema for new deployments.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine, text, inspect

from backend.app.core.database import get_database_url

CONS_REVISION = "20251031_160000_initial_consolidated"


class TempDB:
    def __init__(self) -> None:
        self.base_url = get_database_url()
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp_dir.name) / "cons_test.db"
        self.url = f"sqlite:///{self.db_path}" if "sqlite" in self.base_url else self.base_url
        self.engine = create_engine(self.url)

    def cleanup(self) -> None:
        self.engine.dispose()
        self._tmp_dir.cleanup()


@pytest.fixture()
def temp_db() -> Generator[TempDB, None, None]:
    tdb = TempDB()
    original = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = tdb.url
    try:
        yield tdb
    finally:
        if original:
            os.environ["DATABASE_URL"] = original
        else:
            os.environ.pop("DATABASE_URL", None)
        tdb.cleanup()


def _run(cmd: str, url: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["DATABASE_URL"] = url
    backend_dir = Path(__file__).resolve().parents[2]
    full = ["uv", "run", "alembic"] + cmd.split()
    result = subprocess.run(full, cwd=str(backend_dir), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.fail(f"Alembic failed: {cmd}\n{result.stderr}")
    return result


def _tables(engine) -> set[str]:
    return set(inspect(engine).get_table_names())


def test_consolidated_upgrade_creates_expected_tables(temp_db: TempDB):
    _run(f"upgrade {CONS_REVISION}", temp_db.url)
    tables = _tables(temp_db.engine)
    expected = {
        "users",
        "sessions",
        "medications",
        "conditions",
        "doctors",
        "doctor_condition_links",
        "symptom_type",
        "symptom_log",
        "audit_entry",
        "alembic_version",
    }
    missing = expected - tables
    assert not missing, f"Missing tables after upgrade: {missing}"


def test_consolidated_downgrade_and_reupgrade(temp_db: TempDB):
    _run(f"upgrade {CONS_REVISION}", temp_db.url)
    first = _tables(temp_db.engine)
    assert "users" in first
    _run("downgrade base", temp_db.url)
    after_down = _tables(temp_db.engine)
    # Only alembic_version should remain (may be dropped depending on dialect)
    assert "users" not in after_down, "Tables not dropped on downgrade"
    _run(f"upgrade {CONS_REVISION}", temp_db.url)
    second = _tables(temp_db.engine)
    assert first == second, "Schema differs after re-upgrade"


def test_consolidated_idempotent(temp_db: TempDB):
    _run(f"upgrade {CONS_REVISION}", temp_db.url)
    structure_before = _tables(temp_db.engine)
    _run(f"upgrade {CONS_REVISION}", temp_db.url)  # no-op
    structure_after = _tables(temp_db.engine)
    assert structure_before == structure_after


def test_consolidated_version_record(temp_db: TempDB):
    _run(f"upgrade {CONS_REVISION}", temp_db.url)
    with temp_db.engine.connect() as conn:
        rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert rev == CONS_REVISION


def test_basic_foreign_keys_present(temp_db: TempDB):
    _run(f"upgrade {CONS_REVISION}", temp_db.url)
    insp = inspect(temp_db.engine)
    fk_counts = {t: len(insp.get_foreign_keys(t)) for t in ["sessions", "conditions", "doctors", "symptom_log"] if t in _tables(temp_db.engine)}
    # sessions references users, conditions references users, doctors references users, symptom_log references users & symptom_type
    assert fk_counts.get("sessions", 0) >= 1
    assert fk_counts.get("conditions", 0) >= 1
    assert fk_counts.get("doctors", 0) >= 1
    assert fk_counts.get("symptom_log", 0) >= 2


def test_minimal_insert_select_cycle(temp_db: TempDB):
    _run(f"upgrade {CONS_REVISION}", temp_db.url)
    with temp_db.engine.connect() as conn:
        # insert user
        conn.execute(text("INSERT INTO users (id,email,password_hash) VALUES (:id,:email,:pw)"), {
            "id": "u1",
            "email": "u1@example.com",
            "pw": "hash",
        })
        # insert medication
        conn.execute(text("INSERT INTO medications (name,is_active) VALUES (:n,1)"), {"n": "Aspirin"})
        conn.commit()
        med_count = conn.execute(text("SELECT COUNT(*) FROM medications WHERE name='Aspirin'")).scalar()
    assert med_count == 1
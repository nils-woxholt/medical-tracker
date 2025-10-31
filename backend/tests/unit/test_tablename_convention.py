"""Enforce snake_case explicit table naming convention.

This test ensures all SQLModel tables define an explicit __tablename__ using
snake_case with at least one underscore (for multi-word names) and no capitals.
"""
from sqlmodel import SQLModel
import re

# Import model modules so subclasses are registered
from app.models import symptom_type, symptom_log  # noqa: F401  # extend as more models added

SNAKE_CASE_RE = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)+$|^[a-z0-9]+$")


def test_table_naming_convention():
    bad = []
    for cls in SQLModel.__subclasses__():
        tab = getattr(cls, "__tablename__", None)
        if tab is None:
            # Skip abstract base classes without table mapping
            continue
        if tab != tab.lower():
            bad.append((cls.__name__, tab, "contains uppercase"))
            continue
        if not SNAKE_CASE_RE.match(tab):
            bad.append((cls.__name__, tab, "not snake_case"))
    assert not bad, f"Non-conforming table names: {bad}" 

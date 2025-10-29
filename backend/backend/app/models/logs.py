"""Legacy import compatibility shim for logs models.

Re-exports models so tests using `backend.app.models.logs` continue working.
Prefer importing from `app.models.logs` directly elsewhere.
"""

from app.models.logs import MedicationLog, SymptomLog, SeverityLevel  # noqa: F401

__all__ = ["MedicationLog", "SymptomLog", "SeverityLevel"]

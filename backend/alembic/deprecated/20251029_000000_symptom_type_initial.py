# DEPRECATED archived migration
"""Initial migration for SymptomType and SymptomLog (Feature 004) (ARCHIVED).
Superseded by consolidated migration 20251031_160000_initial_consolidated.
"""
from __future__ import annotations
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func
revision: str = "20251029_000000_symptom_type_initial"
down_revision: Union[str, None] = "e3b9d8f4c2a1"
branch_labels: Union[str, Sequence[str], None] = ("feature-004","archived")
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    pass

def downgrade():
    pass

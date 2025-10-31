# DEPRECATED archived migration
"""Add audit_entry table (ARCHIVED).
Superseded by consolidated migration 20251031_160000_initial_consolidated.
"""
from __future__ import annotations
revision = "20251030_120500_add_audit_entry_table"
down_revision = "20251029_000000_symptom_type_initial"
branch_labels = ("archived",)

def upgrade():
    pass

def downgrade():
    pass

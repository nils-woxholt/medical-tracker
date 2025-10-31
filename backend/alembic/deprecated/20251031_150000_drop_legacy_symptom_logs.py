# DEPRECATED archived migration
"""Drop legacy symptom_logs table (ARCHIVED).
Superseded by consolidated migration 20251031_160000_initial_consolidated.
"""
revision = "20251031_150000_drop_legacy_symptom_logs"
down_revision = "20251030_120500_add_audit_entry_table"
branch_labels = ("archived",)

def upgrade():
    pass

def downgrade():
    pass

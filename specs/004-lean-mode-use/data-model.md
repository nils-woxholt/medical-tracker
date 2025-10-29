# Data Model: Lean Mode Referential Integrity (Feature 004)

Generated: 2025-10-29

## Overview

Introduce canonical master entities for symptoms and medications with referential integrity for log entries. Support dual severity/impact numeric + categorical labels and duration validation.

## Entities

### SymptomType

Canonical definition of a symptom.

- id: int (PK)
- name: str (unique, case-insensitive)
- description: str | null
- created_at: datetime (TZ naive UTC stored)
- updated_at: datetime
- active: bool (default True; deactivate instead of delete)
- category: str | null (future use – clustering/grouping)

Indexes:

- (lower(name)) unique (case-insensitive uniqueness)
- active filter index (if supported by dialect) OR composite (active, name)

### MedicationMaster (existing)

Reuse existing medication master entity (ensure presence of `active` flag; if missing add). Required fields leveraged by `MedicationLog.medication_id`.

### SymptomLog

A recorded symptom occurrence referencing `SymptomType`.

- id: int (PK)
- symptom_type_id: int (FK -> SymptomType.id, ON DELETE RESTRICT)
- user_id: int (FK -> User.id)
- started_at: datetime
- ended_at: datetime | null (null if ongoing)
- duration_minutes: int (computed server-side if both timestamps; validation: 0 < duration_minutes ≤ 1440) OR derived on read if not stored.
- severity_numeric: int (1–10)
- severity_label: enum(str) (Mild | Moderate | Severe | Critical) derived from severity_numeric mapping: 1–3 Mild, 4–6 Moderate, 7–8 Severe, 9–10 Critical.
- impact_numeric: int (1–10)
- impact_label: enum(str) (same mapping as severity)
- notes: str | null
- created_at: datetime
- confirmation_long_duration: bool (required true if duration_minutes > 720 and ≤ 1440)

Constraints & Checks:

- CHECK (severity_numeric BETWEEN 1 AND 10)
- CHECK (impact_numeric BETWEEN 1 AND 10)
- CHECK (duration_minutes <= 1440)
- CHECK ((duration_minutes <= 720) OR (confirmation_long_duration = 1))

### MedicationLog

Medication intake referencing medication master.

- id: int (PK)
- medication_id: int (FK -> MedicationMaster.id, ON DELETE RESTRICT)
- user_id: int (FK -> User.id)
- taken_at: datetime
- dose_amount: decimal | null (if available)
- dose_unit: str | null (e.g., mg, ml, tablet)
- notes: str | null
- created_at: datetime

### AuditEntry (existing extension / reuse)

Record change events for master data modifications (create/update/deactivate of SymptomType and MedicationMaster).

- id: int (PK)
- entity_type: str ("symptom_type" | "medication_master")
- entity_id: int
- action: str ("create" | "update" | "deactivate")
- user_id: int | null (system actions possible)
- timestamp: datetime
- diff: json | null (structure capturing changed fields)

## Relationships Summary

- SymptomLog.symptom_type_id -> SymptomType.id (many-to-one)
- SymptomLog.user_id -> User.id
- MedicationLog.medication_id -> MedicationMaster.id (many-to-one)
- MedicationLog.user_id -> User.id
- AuditEntry.entity_id -> (SymptomType.id or MedicationMaster.id) depending on entity_type discriminator

## Severity / Impact Mapping Logic

Pseudo:

```python
def severity_label(n: int) -> str:
    if n <= 3:
        return 'Mild'
    if n <= 6:
        return 'Moderate'
    if n <= 8:
        return 'Severe'
    return 'Critical'
```

## Duration Validation

- Compute duration as (ended_at - started_at) minutes rounded down.
- Reject if duration_minutes > 1440.
- If duration_minutes > 720, require confirmation_long_duration = True else 422.
- If ended_at < started_at → 422.
- Support ongoing logs (ended_at null) → duration_minutes not persisted until closure; confirmation flag not needed until ended.

## Deactivation Rules

- Setting SymptomType.active = False:
  - Block new SymptomLog referencing inactive type (service-layer check).
  - Existing logs retained.
- Similar rule for MedicationMaster if not already enforced.

## Derived vs Stored Fields

- severity_label / impact_label stored for read performance & simple filtering; derived again in validation to ensure consistency.
- duration_minutes stored once log is closed; for open logs compute on the fly.

## Indexing Strategy

- SymptomLog: (user_id, started_at DESC) for dashboard queries; (symptom_type_id, started_at DESC) for analytics.
- MedicationLog: (user_id, taken_at DESC)
- Partial index for active SymptomType if supported.

## Migration Outline

1. Create `symptom_type` table.
2. Add `symptom_type_id` FK to symptom logs (existing table rename if necessary) or create new `symptom_log` table if none.
3. Add severity/impact numeric + label columns; add confirmation_long_duration and duration_minutes (nullable until ended).
4. Add constraints (CHECKs).
5. Backfill existing free-text symptom entries (if present) into new SymptomType + map logs to IDs (script; outside migration may be needed).
6. Ensure medication master has `active` column; add if missing.
7. Create indexes.

## Open Implementation Considerations

- Backfill strategy requires snapshot of distinct symptom text values; create new SymptomType rows then update logs.
- Concurrency: enforce uniqueness on lower(name); handle conflict with 409 response.
- Timezones: assume all stored UTC; client responsible for conversion.

## Validation Error Modes

- 400: Business rule violation (e.g. referencing inactive SymptomType) – could also use 422; choose 422 uniformly for input validation consistency.
- 409: Unique name conflict for SymptomType.
- 422: Numeric bounds, duration limits, missing confirmation flag.

## Testing Plan (Data Model Focus)

- Unit: mapping function; duration calculator; confirmation logic.
- Integration: create SymptomType then log symptom; attempt log with inactive type (expect 422/400 per final API spec decision).
- Migration Test: After migration, inspect constraints existence.

## Next Steps

Proceed to draft OpenAPI contracts with new schemas (`SymptomTypeCreate`, `SymptomTypeRead`, `SymptomLogCreate`, `SymptomLogRead`, `MedicationLogCreate`, `MedicationLogRead`).

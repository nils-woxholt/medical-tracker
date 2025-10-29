# Research & Decisions: Lean Mode Referential Integrity Feature

**Feature**: 004-lean-mode-use

**Date**: 2025-10-29

## Decisions Summary

### Duration Upper Bound

- **Decision**: Hard cap at 1440 minutes (24h); warn + confirm >12h ≤24h; block >24h.
- **Rationale**: Prevent data skew and accidental large entries while permitting legitimate extended episodes.
- **Alternatives Considered**:
  - No cap (risk analytics distortion)
  - 48h cap (does not encourage splitting for multi-day symptoms)

### Severity/Impact Scale

- **Decision**: Dual numeric (1–10) + categorical labels (Mild 1–3, Moderate 4–6, Severe 7–8, Critical 9–10).
- **Rationale**: Numeric enables quantitative analysis; labels improve user comprehension; deterministic mapping reduces ambiguity.
- **Alternatives Considered**:
  - Numeric only (less approachable to some users)
  - Categories only (reduces analytical granularity)

### Duration Confirmation Mechanism

- **Decision**: Confirmation checkbox required for durations >12h ≤24h.
- **Rationale**: Lightweight safeguard; ensures intentional long entries.
- **Alternatives Considered**:
  - Passive warning only (higher accidental error risk)
  - Force split >12h (more friction for genuine long episodes)

### Data Storage Strategy

- **Decision**: Referential integrity via foreign keys (SymptomLog.symptom_type_id, MedicationLog.medication_id); deactivation instead of deletion.
- **Rationale**: Preserves historical analytics & avoids orphaned references.
- **Alternatives Considered**:
  - Hard deletion (loss of history)
  - Soft delete with nullable FK (adds complexity)

### Searchable Dropdown Implementation (Conceptual)

- **Decision**: Client-side filtering up to 500 items; degrade to incremental loading beyond scope (future enhancement).
- **Rationale**: Simplicity in Lean Mode; performance acceptable for expected scale.
- **Alternatives Considered**:
  - Server-side search (premature complexity)
  - Virtualized list now (not needed at current sizes)

### Accessibility Commitments

- **Decision**: Keyboard navigation + ARIA roles for dropdown, clear focus states, descriptive labels for severity/impact units.
- **Rationale**: Baseline accessibility per constitution; reduces remediation later.
- **Alternatives Considered**:
  - Defer accessibility (creates debt)

### Observability (Lean Mode)

- **Decision**: Log creation events (symptom_type.create/edit/deactivate, symptom_log.create, medication_log.create) with request id & user id; error logs for validation failures.
- **Rationale**: Minimal yet useful operational insight; aligns with Lean observability.
- **Alternatives Considered**:
  - Full metrics/tracing now (Strict Mode scope)

## Open Questions Resolved

None remaining; all prior NEEDS CLARIFICATION addressed.

## Implementation Impact

- Validation layer update for new duration rules & severity label derivation.
- Migration: add severity_numeric/impact_numeric + derived label fields (or compute labels dynamically — decision: store both for query simplicity).
- UI components: new Symptom Type management page, enhanced dropdown component, duration unit switch & confirmation control.

## Risk Mitigations

- Cap and confirmation reduce erroneous data.
- Dual representation ensures future analytics flexibility.
- Deactivation approach preserves referential integrity.

## Next Steps

Proceed to Phase 1: data modeling and contract generation.

# Feature Specification: Lean Mode: Use Referential Integrity for Symptom & Medication Logs

**Feature Branch**: `004-lean-mode-use`  
**Created**: 2025-10-29  
**Status**: Draft  
**Input**: User description: "lean mode use referential integrity \n\n## Symptoms\n\n- Add a symptom type setup page, similar to the medications page\n- a user can set up a name, default severity and default impact\n- Symptom logs should do a lookup to te symptom type and show a searchable dropdown\n- the symptom logs table should change to reflect the use of the symptom type id\n- also move the end date time entry to a back-end only field, it doesn;t have to be captured rather infer it from the duration minutes field.\n- improve the ui for duration minutes to allow for minutes(default) and hours\n\n## medication\n\n- medication logs should do a lookup to the medications table and show a searchable dropdown\n- the medication logs table should change to reflect the use of the medication id"

## User Scenarios & Testing *(mandatory)*

### Prioritization Summary

As a patient user, I can create and manage standardized symptom types (name, default severity, default impact) so that logging symptoms becomes faster and more consistent.

**Why this priority**: Enables data normalization and speeds up daily logging; prerequisite for referential integrity in symptom logs.

**Independent Test**: Verify a user can create, edit, and deactivate a symptom type and that it appears in a selectable list when logging a symptom without relying on medication changes.

**Acceptance Scenarios**:

1. **Given** no symptom types exist, **When** the user creates a new symptom type with name, default severity, default impact, **Then** the type is saved and listed in the symptom type table.
2. **Given** an existing symptom type, **When** the user edits its default severity and impact, **Then** subsequent new symptom logs pre-fill those updated defaults.
3. **Given** an existing symptom type, **When** the user deactivates it, **Then** it no longer appears in the logging dropdown but historical logs still show the original name.

---

### User Story 2 - Log Symptoms via Type Dropdown (Priority: P2)

As a patient user, I can log a symptom by selecting a predefined symptom type from a searchable dropdown, auto-populating severity and impact defaults, and specifying duration in minutes or hours, so that logging is quicker and data consistent.

**Why this priority**: Builds on symptom types to provide the referential logging efficiency; daily usage scenario.

**Independent Test**: A tester can create a symptom type first, then log a symptom selecting it and verify default propagation and duration conversion without touching medication features.

**Acceptance Scenarios**:

1. **Given** at least one symptom type exists, **When** the user opens the symptom logging form, **Then** a searchable dropdown lists active types.
2. **Given** the user selects a type with defaults, **When** the form loads, **Then** severity and impact fields pre-fill but remain editable.
3. **Given** the user enters a duration in hours mode (e.g., 2 hours), **When** the log is saved, **Then** the persisted duration minutes equals 120 and end time is inferred from start + duration.
4. **Given** the user leaves severity blank after selecting a type, **When** saving, **Then** the default severity is applied (unless explicitly changed).

---

### User Story 3 - Log Medication via Searchable Dropdown (Priority: P3)

As a patient user, I can log medication intake by selecting an existing medication from a searchable dropdown (rather than free-text), so that records reference a canonical medication entry.

**Why this priority**: Extends referential integrity to medication logs; improves accuracy and future analytics; less frequent than symptom logging hence lower priority.

**Independent Test**: Tester can create one medication (pre-existing system feature), then log a medication intake selecting it and verify stored foreign key without needing symptom log features.

**Acceptance Scenarios**:

1. **Given** active medications exist, **When** the user opens medication logging form, **Then** a searchable dropdown lists them by name + purpose snippet.
2. **Given** the user selects a medication, **When** saving the log, **Then** the log stores the medication reference and displays medication name in summaries.
3. **Given** a medication is marked inactive, **When** logging a new medication, **Then** the inactive one is excluded from dropdown but historical logs still show it.

---

### User Story 4 - Infer Symptom End Time (Priority: P4)

As a patient user, I only need to enter symptom start time and duration (minutes or hours) and the system infers end time, reducing form complexity.

**Why this priority**: Improves usability; dependent on duration handling; nice-to-have after core referential changes.

**Independent Test**: Provide start time + duration, verify calculated end time appears in summaries/log details without user input field.

**Acceptance Scenarios**:

1. **Given** a start time and duration are entered, **When** saving, **Then** end time = start time + duration is stored and shown in detail views.
2. **Given** duration is edited from 30 minutes to 2 hours, **When** saving, **Then** end time recalculates accordingly.

---

P1 enables data model foundation. P2 provides daily logging efficiency. P3 extends integrity to medications. P4 streamlines UX further.

### Edge Cases

- No active symptom types exist when user wants to log a symptom (show empty state guidance, allow creation shortcut?).
- User searches for a symptom type string with no matches (show "No matches" and offer create link if permission).
- Duration entered as 0 or negative (reject with validation message).
- Very long duration (> 24h) attempted: entry is blocked; user instructed to split into multiple logs (since hard cap 1440 minutes).
- Duration between >12h and ≤24h entered: user sees warning and must explicitly confirm (checkbox) before save proceeds.
- Medication list extremely long (hundreds) — dropdown still performant and searchable.
- User deactivates a symptom type currently used in an in-progress log (log should fail gracefully or refresh list).
- Time zone changes across logs (end time inference must respect user’s local time at logging moment).
- User tries to log symptom without selecting a type (validation blocks submission, suggests selecting or creating type).
- User switches duration units (minutes ↔ hours) mid-entry; value conversion preserves intended total minutes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a Symptom Type management interface allowing create, edit, deactivate of types with fields: name (unique per user), default severity, default impact, active flag.
- **FR-002**: System MUST present a searchable dropdown of active Symptom Types when creating a symptom log.
- **FR-003**: System MUST auto-populate severity and impact values in a symptom log from selected Symptom Type defaults if user does not override them.
- **FR-004**: System MUST store symptom logs referencing Symptom Type via a stable identifier (foreign key) instead of duplicating name/severity/impact text.
- **FR-005**: System MUST allow user override of severity and impact per log while retaining the type reference.
- **FR-006**: System MUST provide duration input supporting minutes (default) and hours selection, converting hours to total minutes internally.
- **FR-007**: System MUST infer symptom end time from start time + duration and NOT require a direct end time input field in the logging UI.
- **FR-008**: System MUST validate duration > 0 and ≤ 1440 minutes (24h); values > 1440 MUST be rejected with guidance to split into multiple logs.
- **FR-009**: System MUST continue displaying historical logs using deactivated symptom types (show stored name and link disabled state).
- **FR-010**: System MUST provide a searchable dropdown of active medications when creating a medication log.
- **FR-011**: System MUST store medication logs referencing Medication via identifier instead of duplicating medication name text.
- **FR-012**: System MUST exclude inactive medications and symptom types from dropdown lists while keeping them in historical views.
- **FR-013**: System MUST handle empty state when no symptom types exist (present guidance and optional create action).
- **FR-014**: System MUST support fast search response (<1 second perceived) for up to 500 symptom types or medications (user perspective of immediacy).
- **FR-015**: System MUST prevent logging a symptom without selecting a symptom type (blocking validation message).
- **FR-016**: System MUST provide unit switch (minutes/hours) maintaining underlying total minutes consistency when toggled.
- **FR-017**: System MUST ensure referential integrity: logs cannot reference deleted symptom types or medications; deletion must be modeled as deactivation rather than removal to preserve history.
- **FR-018**: System MUST audit changes to Symptom Type default severity/impact so subsequent analyses can account for configuration shifts.
- **FR-019**: System MUST support partial accessibility: dropdown searchable via keyboard and screen reader labels.
- **FR-020**: System MUST warn users when entering duration > 12h and ≤ 24h to confirm accuracy.
- **FR-022**: System MUST require explicit user confirmation (e.g., checkbox) for durations > 12h and ≤ 24h before allowing save; absence of confirmation blocks submission.
- **FR-021**: System MUST implement dual severity/impact representation: store numeric value (1–10) and derive categorical label (Mild 1–3, Moderate 4–6, Severe 7–8, Critical 9–10) for analytics & UI display.

### Key Entities *(include if feature involves data)*

- **SymptomType**: Represents a reusable definition of a symptom for a user. Attributes: identifier, user owner, name (unique per user), default severity, default impact, active flag, created timestamp, updated timestamp.
- **SymptomLog**: Individual occurrence referencing SymptomType. Attributes: identifier, symptom_type_id, user id, start time, duration_minutes, inferred end time (derived), severity_numeric, severity_label, impact_numeric, impact_label (labels derived from numeric), notes (if existing system supports), created timestamp.
- **Medication**: Existing entity (canonical medication definitions). Attributes (existing) plus active flag for selection filtering.
- **MedicationLog**: Individual intake referencing Medication. Attributes: identifier, medication_id, user id, intake time, dosage (if existing), notes, created timestamp.
- **AuditEntry**: Captures changes to SymptomType defaults: identifier, entity type, entity id, changed fields, previous values, new values, timestamp, user id.

## Assumptions *(added)*

- Users already have a medication setup page; Symptom Type page will mimic its interaction style for consistency.
- Severity and impact scales exist (e.g., numeric 1-10 or categorical). We assume numeric 1-10 for defaults and overrides.
- Severity and impact scales clarified: numeric 1–10 stored; categorical labels derived (Mild 1–3, Moderate 4–6, Severe 7–8, Critical 9–10).
- Duration upper bound default assumption: 1440 minutes (24h) unless clarified.
- Searchable dropdown uses client-side filtering for up to 500 items; beyond that may require incremental loading (out of current scope).
- Time zone stored per timestamp (UTC with local conversion assumed) — inference uses start time zone context.
- Deactivation preferred over deletion to retain historical integrity and analytics.
- Accessibility baseline: keyboard navigation, ARIA labels, visible focus states.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User can create a new Symptom Type and see it in dropdown within ≤ 5 seconds end-to-end (perceived immediate availability).
- **SC-002**: Logging a symptom via dropdown (select + save) takes ≤ 30 seconds for first-time user; ≤ 10 seconds for repeat user (after learning).
- **SC-003**: 95% of symptom log submissions auto-populate severity/impact without manual override (indicates usefulness of defaults) during first month post-launch.
- **SC-004**: 0% of new symptom logs missing a type reference (enforced referential integrity).
- **SC-005**: End time inference accuracy = 100% (no manual corrections needed) in QA test set of ≥ 50 logs.
- **SC-006**: Dropdown search returns relevant results (case-insensitive match) and displays first character typed suggestions within ≤ 1 second for dataset of 500 items.
- **SC-007**: Accessibility: Symptom Type dropdown and duration unit switch achieve ≥ 90% keyboard operability tasks success in manual accessibility review.
- **SC-008**: Duration validation prevents 100% of invalid entries (0, negative) in test scenarios.
- **SC-009**: Medication logs store medication references correctly for 100% of new entries during regression tests (no orphan medication name strings).
- **SC-010**: Historical logs remain viewable after deactivation with 0 data loss incidents recorded in QA.

## Clarifications

### Session 2025-10-29

- Q: Maximum duration limit for symptom logs? → A: Hard cap 1440 minutes (24h); block entries above this and instruct user to split.
- Q: Severity/Impact scale definition? → A: Dual storage: numeric 1–10 with auto label mapping (Mild 1–3, Moderate 4–6, Severe 7–8, Critical 9–10).
- Q: Maximum duration behavior—warn only or block beyond threshold? → A: Warn + require confirmation for >12h and ≤24h; block >24h (cap already defined).

## Out of Scope

- Bulk import of symptom types.
- Predictive suggestions beyond simple default propagation.
- Performance optimization for >500 items (future enhancement).

## Risks

- User confusion if severity/impact scales differ from existing mental models.
- Large lists may reduce performance perception if not optimized.
- Incorrect duration unit switching could cause end time miscalculations if not clearly labeled.

## Dependencies

- Existing Medication entity and management page.
- Authentication/user context availability for ownership of types and logs.

## Glossary

- "Referential Integrity": Logs referencing canonical entities rather than duplicating attribute text, preserving consistency and enabling analytics.
- "Symptom Type": Template definition for repeated symptom occurrences.

## Functional Requirement Acceptance Matrix (Added)

| Requirement | Acceptance Criteria (Pass Conditions) |
|-------------|---------------------------------------|
| FR-001 Symptom Type management | Create with unique name -> 201; Edit defaults updates subsequent new log prefill; Deactivate hides from dropdown while historical log still shows name; uniqueness conflict returns 409. |
| FR-002 Symptom Type dropdown | At least one active type -> GET /symptom-types returns list; logging form fetch shows only active types. Empty state when none. |
| FR-003 Auto-populate severity/impact | Create log without overriding severity/impact -> persisted severity_numeric/impact_numeric equal SymptomType defaults. |
| FR-004 Store FK reference | SymptomLog row contains symptom_type_id matching created SymptomType; no duplicated name/severity fields beyond labels. |
| FR-005 Override severity/impact | User changes severity numeric before save -> stored numeric matches override, not default. |
| FR-006 Duration input minutes/hours | Enter 2 hours -> stored duration_minutes = 120; toggle units minutes→hours preserves total minutes. |
| FR-007 Infer end time | Log created with start + duration -> ended_at = started_at + duration_minutes; end time field not in form. |
| FR-008 Duration validation bounds | Duration 0 or >1440 -> 422 with message; 1440 passes; 1441 blocked. |
| FR-009 Historical logs persist deactivated types | Deactivate type -> existing logs query still returns name and label; new log attempt with inactive type -> 422. |
| FR-010 Medication dropdown | Logging form shows active medications only; inactive not listed. |
| FR-011 Medication FK reference | MedicationLog row has medication_id; no duplicated name string. |
| FR-012 Exclude inactive entities | Inactive SymptomType/Medication not returned in dropdown list endpoints; still retrievable directly via detail endpoint or historical log joins. |
| FR-013 Empty state guidance | No types -> logging form shows message and link/button to create Symptom Type. |
| FR-014 Search performance | Client-side filter of 500 items returns filtered subset in ≤1s (manual perf test script). |
| FR-015 Require type selection | Submit symptom log without type -> 422 validation error referencing missing symptom_type_id. |
| FR-016 Unit switch consistency | Switch from 90 minutes to 1.5 hours representation keeps duration_minutes = 90; round-trip conversion stable. |
| FR-017 Referential integrity & deactivation | DELETE not allowed; PATCH deactivate prevents future logs; database FK ON DELETE RESTRICT ensures no orphan removal. |
| FR-018 Audit changes to defaults | Update SymptomType defaults -> AuditEntry created with diff of changed fields and timestamp. |
| FR-019 Accessibility baseline | Keyboard navigation: focusable dropdown, arrow key navigation, screen reader label announces selection; manual audit passes ≥90% tasks. |
| FR-020 Warn long duration | Enter duration 13h (780m) without confirmation -> 422 requiring confirmation; with confirmation -> success. |
| FR-021 Dual severity/impact labels | Severity numeric 7 -> label 'Severe'; numeric 9 -> 'Critical'. Mapping unit tests cover boundaries (3,4,6,7,8,9,10). |
| FR-022 Require confirmation >12h ≤24h | Duration 721–1440 requires confirmation flag true; 720 passes without flag; 1441 blocked irrespective of confirmation. |

This matrix ensures each functional requirement is explicitly testable and aligns with success criteria and user stories.

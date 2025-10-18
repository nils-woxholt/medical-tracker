# Feature Specification: SaaS Medical Tracker (Conditions, Doctors, Symptoms & Medication Diary)

**Feature Branch**: `001-saas-medical-tracker`  
**Created**: 2025-10-15  
**Status**: Draft  
**Input**: User description: "I'm building a SAAS medical tracker web-app - a one stop diary about my conditions, doctors, symptoms and medication. It must look sleek and trust-worthy. It must use a colloquial but sympathetic language tone. It must have: landing page (summary last 5 medication logs, last 5 symptom logs, a 'how do you feel vs yesterday' better or worse), medication page (log medication taken; maintenance of medication meta: purpose, frequency, prescribing doctor, current or not), symptom page (symptom definition + logging), doctor page (name, related condition, phone, email, description), condition passport (diagnosed conditions), notes (tag a doctor or medication and upload a file), login multi-patient system. It must be easy to navigate, mobile friendly, visual with graphs and visuals to show progress."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Log Daily Medication & Symptoms (Priority: P1)

The user (patient) records today's medications taken and any symptoms experienced, then views an updated landing summary reflecting the last 5 medication entries, last 5 symptom entries, and a computed "feel vs yesterday" indicator (better/worse/same) based on symptom severity trend.

**Why this priority**: Daily capture of medication adherence and symptom state is the core value proposition; without logging there is no longitudinal insight.

**Independent Test**: User can create at least one medication log entry and one symptom log entry and immediately see both appear in the landing page lists plus a feel-vs-yesterday status value based solely on underlying data differences.

**Acceptance Scenarios**:

1. **Given** no prior logs today, **When** user submits a medication log with required fields, **Then** it appears at top of the medication summary list.
2. **Given** at least one symptom logged yesterday, **When** user logs a symptom today with lower severity, **Then** feel-vs-yesterday shows "better".
3. **Given** at least one symptom logged yesterday, **When** user logs a symptom today with higher severity, **Then** feel-vs-yesterday shows "worse".
4. **Given** five prior medication logs, **When** a sixth is added, **Then** summary still shows only the five most recent (new one included).
5. **Given** user logs medication with optional notes omitted, **When** viewing the summary, **Then** missing optional fields do not break layout.

---

### User Story 2 - Manage Medication Master Data (Priority: P2)

User maintains the catalog of medications: name, purpose (condition treated), dosage/frequency, prescribing doctor, whether currently active. This master list drives selection when logging medication and allows deactivating old treatments without losing historical logs.

**Why this priority**: Structured medication metadata improves logging speed and accuracy and enables downstream analytics (adherence, changes over time).

**Independent Test**: User can create, edit, deactivate, and list medications; logging flow can select only active medications.

**Acceptance Scenarios**:

1. **Given** a new medication form with all required fields, **When** user saves, **Then** the medication appears in active list.
2. **Given** an active medication, **When** user deactivates it, **Then** it is excluded from active selection but historical logs retain its reference.
3. **Given** a medication with existing logs, **When** user edits frequency, **Then** future logs can reflect new frequency while previous logs remain unchanged.
4. **Given** two medications A and B, **When** user searches by partial name, **Then** matching subset returned (case-insensitive).

---

### User Story 3 - Condition Passport & Doctor Directory (Priority: P3)

User maintains a list of diagnosed conditions (condition name, date diagnosed, status) and associated doctors (name, specialty/condition association, phone, email, description). User can view a compiled "passport" summarizing conditions and linked physicians.

**Why this priority**: Establishes structured medical context enabling better interpretation of logs and future analytics.

**Independent Test**: User can add a condition, link a doctor to that condition, and view a passport summary containing both elements without requiring any medication logging.

**Acceptance Scenarios**:

1. **Given** a new condition entry form, **When** user saves with valid fields, **Then** condition appears in passport list.
2. **Given** a doctor linked to a condition, **When** viewing passport, **Then** doctor is shown under that condition.
3. **Given** a doctor record, **When** user updates contact details, **Then** passport reflects updated data on refresh.
4. **Given** two conditions with different doctors, **When** generating passport, **Then** grouping preserves associations correctly.

---

### Additional Future Stories (Deferred)

- Symptom taxonomy management (define symptom types & severity scales)
- Notes with file upload & tagging (medication, doctor references)
- Visual analytics dashboards (graphs for symptom trends & adherence)
- Multi-patient administrative access controls

### Edge Cases

- No symptom logs for yesterday when computing feel-vs-yesterday (status becomes "unavailable").
- User attempts to log medication for an inactive (deactivated) medication (reject with guidance to reactivate or pick another).
- Duplicate medication name entered differing only by case (normalize & conflict error).
- Deleting a doctor referenced by a condition (block delete; require unlink or soft-deactivate doctor).
- Rapid successive log submissions (ordering maintained by timestamp + stable secondary key).
- Viewing condition passport with zero conditions (show empty state message encouraging first entry).

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST allow a registered user to create a medication log with: timestamp (default now), medication reference, dosage taken (numeric + unit), optional free-form note.
- **FR-002**: System MUST compute and display a list of the 5 most recent medication logs for the current user on the landing page (sorted descending by timestamp).
- **FR-003**: System MUST allow a user to create a symptom log with: timestamp, symptom type (free text initially), severity (bounded scale 1–5), optional note.
- **FR-004**: System MUST compute and display the 5 most recent symptom logs for the current user on the landing page (sorted descending by timestamp).
- **FR-005**: System MUST derive the "feel vs yesterday" status as one of {better, worse, same, unavailable} using average severity of yesterday vs today; unavailable if no logs yesterday or today.
- **FR-006**: System MUST allow creation of medication master records with: name (unique per user, case-insensitive), purpose/condition text, frequency description, prescribing doctor reference (optional), active flag.
- **FR-007**: System MUST allow editing of existing medication master records (except historical logs remain unchanged).
- **FR-008**: System MUST allow deactivating a medication; inactive medications MUST NOT appear in medication log selection lists but remain selectable in historical views.
- **FR-009**: System MUST allow creation of condition records: name, diagnosis date, status (active, resolved), optional notes.
- **FR-010**: System MUST allow creation of doctor records: name, associated condition (optional link), phone, email, description.
- **FR-011**: System MUST allow linking an existing doctor to a condition and updating that linkage.
- **FR-012**: System MUST provide a condition passport view summarizing all conditions with nested doctors.
- **FR-013**: System MUST prevent creation of duplicate medication names differing only by case (e.g., "Ibuprofen" vs "ibuprofen").
- **FR-014**: System MUST enforce authentication (login required) for all pages except a marketing/landing pre-login page (if implemented later).
- **FR-015**: System MUST ensure that users can only access, create, or modify their own records (multi-tenant isolation).
- **FR-016**: System MUST record created/updated timestamps for all entities (medication master, logs, symptoms, doctors, conditions).
- **FR-017**: System MUST support pagination or bounded retrieval when listing more than 50 logs (default page size ≤ 25).
- **FR-018**: System MUST display validation errors in user-friendly, sympathetic tone.
- **FR-019**: System MUST provide mobile-friendly layout for landing, medication, symptoms, passport, doctors pages.
- **FR-020**: System MUST provide visual indicators showing per-symptom severity change vs previous log of same type.

### Key Entities *(include if feature involves data)*

- **MedicationMaster**: name (unique per user), purpose, frequency description, prescribingDoctorId?, active flag, createdAt, updatedAt.
- **MedicationLog**: id, userId, medicationMasterId, dosageValue, dosageUnit, timestamp, note?, createdAt.
- **SymptomLog**: id, userId, symptomType, severity (1–5), note?, timestamp, createdAt.
- **Condition**: id, userId, name, diagnosisDate, status (active|resolved), notes?, createdAt, updatedAt.
- **Doctor**: id, userId, name, phone, email, description?, primaryConditionId?, createdAt, updatedAt.
- **ConditionDoctorLink**: (conceptual join if many-to-many later) conditionId, doctorId.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: User can log a medication and a symptom in under 60 seconds (from page load to confirmation) on first use.
- **SC-002**: 95% of daily log submissions complete without validation error on first attempt.
- **SC-003**: Landing page shows updated summaries and feel-vs-yesterday within 2 seconds of new log submission.
- **SC-004**: ≥ 80% of early pilot users report navigation is "easy" or "very easy" in a day-1 survey.
- **SC-005**: Mobile viewport (375px) renders forms without horizontal scrolling; interaction success rate ≥ 95% in usability test.
- **SC-006**: ≥ 70% of users who log medication on day 1 also log a symptom by day 3.
- **SC-007**: Zero unauthorized data access incidents in access audit during initial release period.

# Tasks: Lean Mode Referential Integrity (Feature 004)

Feature Directory: `specs/004-lean-mode-use`
Source Docs: `plan.md`, `spec.md`, `data-model.md`, `research.md`, `contracts/feature-004.openapi.yaml`

## Phase 1: Setup

Purpose: Establish environment & baseline artifacts required before foundational and story tasks.

- [ ] T001 Ensure backend virtual environment active (`backend/.venv`) and dependencies synced (no new deps in Lean Mode)
- [ ] T002 Verify presence of OpenAPI contract `specs/004-lean-mode-use/contracts/feature-004.openapi.yaml` (must exist before implementation)
- [ ] T003 Create placeholder migration file `backend/alembic/versions/<timestamp>_symptom_type_initial.py`
- [ ] T004 Add `tasks.md` (this file) to version control
- [ ] T005 Create backend model module file `backend/app/models/symptom_type.py`
- [ ] T006 Create backend model module file `backend/app/models/symptom_log.py`
- [ ] T007 Confirm `Medication` master model has `active` flag; if missing add field in `backend/app/models/medication.py`
- [ ] T008 Add severity/impact mapping utility `backend/app/services/severity_mapping.py`
- [ ] T009 [P] Add duration validation utility `backend/app/services/duration_validator.py`
- [ ] T010 Create audit model extension (if not present) `backend/app/models/audit_entry.py`

## Phase 2: Foundational

Purpose: Blocking prerequisites: database migration, core validation utilities, and contract test scaffolding.

- [ ] T011 Implement Alembic migration for `symptom_type` table & modify/create `symptom_log` table with constraints in `backend/alembic/versions/<timestamp>_symptom_type_initial.py`
- [ ] T012 [P] Implement `SymptomType` SQLModel class in `backend/app/models/symptom_type.py`
- [ ] T013 Implement `severity_label` & `impact_label` derivation in `backend/app/services/severity_mapping.py`
- [ ] T014 Implement `validate_duration` (caps, confirmation logic) in `backend/app/services/duration_validator.py`
- [ ] T015 [P] Implement `SymptomLog` SQLModel class in `backend/app/models/symptom_log.py`
- [ ] T016 Add active enforcement check utility `backend/app/services/active_fk_guard.py`
- [ ] T017 Add base repository/service scaffolds `backend/app/services/symptom_type_service.py`
- [ ] T018 [P] Add symptom log service scaffold `backend/app/services/symptom_log_service.py`
- [ ] T019 Add medication log service scaffold `backend/app/services/medication_log_service.py`
- [ ] T020 Add contract validation test `backend/tests/contract/test_feature_004_contract.py`
- [ ] T021 Add unit tests for severity mapping `backend/tests/unit/test_severity_mapping.py`
- [ ] T022 [P] Add unit tests for duration validator `backend/tests/unit/test_duration_validator.py`
- [ ] T023 Add unit tests for active FK guard `backend/tests/unit/test_active_fk_guard.py`
- [ ] T024 Integration test for migration constraints `backend/tests/integration/test_migration_feature_004.py`

## Phase 3: User Story 1 (P1) Symptom Type Management

Goal: CRUD + deactivate symptom types with audit logging.
Independent Test Criteria: Create, edit, deactivate a symptom type; dropdown list updates; historical logs retain name.

- [ ] T025 [US1] Implement create endpoint route `backend/app/api/symptom_types.py` (POST /symptom-types)
- [ ] T026 [P] [US1] Implement read/list endpoint route (GET /symptom-types & /symptom-types/{id}) in `backend/app/api/symptom_types.py`
- [ ] T027 [US1] Implement update endpoint (PUT /symptom-types/{id}) in `backend/app/api/symptom_types.py`
- [ ] T028 [US1] Implement deactivate endpoint (PATCH /symptom-types/{id}/deactivate) in `backend/app/api/symptom_types.py`
- [ ] T029 [US1] Add audit logging calls in `backend/app/services/symptom_type_service.py`
- [ ] T030 [US1] Add unique name conflict handling (409) in `backend/app/api/symptom_types.py`
- [ ] T031 [US1] Add integration tests CRUD flow `backend/tests/integration/test_symptom_type_crud.py`
- [ ] T032 [P] [US1] Add unit tests for audit logging diff creation `backend/tests/unit/test_audit_logging.py`
- [ ] T033 [US1] Add dropdown data provider endpoint (if separate) or reuse list with query param filter in `backend/app/api/symptom_types.py`
- [ ] T034 [US1] Frontend component: Symptom Type list page `frontend/src/components/symptom-types/SymptomTypeTable.tsx`
- [ ] T035 [US1] Frontend form component `frontend/src/components/symptom-types/SymptomTypeForm.tsx`
- [ ] T036 [US1] Frontend API client functions `frontend/src/services/symptomTypes.ts`
- [ ] T037 [US1] Frontend integration tests (component) `frontend/__tests__/SymptomTypeForm.test.tsx`
- [ ] T038 [US1] E2E test create/edit/deactivate `frontend/tests/e2e/symptom-type-crud.spec.ts`

## Phase 4: User Story 2 (P2) Log Symptoms via Dropdown

Goal: Logging symptoms referencing SymptomType with defaults and duration logic.
Independent Test Criteria: Select type, defaults apply, duration/hours conversion works, confirmation required for long durations, end time inferred.

- [ ] T039 [US2] Implement create symptom log endpoint (POST /symptom-logs) `backend/app/api/symptom_logs.py`
- [ ] T040 [P] [US2] Implement list endpoint (GET /symptom-logs?filters) `backend/app/api/symptom_logs.py`
- [ ] T041 [US2] Implement severity/impact default fill logic in `backend/app/services/symptom_log_service.py`
- [ ] T042 [US2] Implement duration inference & confirmation validation in `backend/app/services/duration_validator.py`
- [ ] T043 [US2] Implement active SymptomType guard in `backend/app/services/active_fk_guard.py`
- [ ] T044 [US2] Integration test symptom log creation & long duration confirmation `backend/tests/integration/test_symptom_log_creation.py`
- [ ] T045 [US2] Frontend logging form update `frontend/src/components/logging/SymptomLogForm.tsx`
- [ ] T046 [P] [US2] Frontend severity/impact auto-fill logic `frontend/src/components/logging/useSymptomDefaults.ts`
- [ ] T047 [US2] Frontend duration unit switch component `frontend/src/components/logging/DurationInput.tsx`
- [ ] T048 [US2] Frontend searchable dropdown `frontend/src/components/common/SearchableDropdown.tsx`
- [ ] T049 [US2] Component tests (duration & defaults) `frontend/__tests__/SymptomLogForm.test.tsx`
- [ ] T050 [US2] E2E test symptom logging flow `frontend/tests/e2e/symptom-log.spec.ts`

## Phase 5: User Story 3 (P3) Medication Log Dropdown

Goal: Logging medication intake via canonical selection.
Independent Test Criteria: Select medication, log stores FK, inactive meds excluded.

- [ ] T051 [US3] Implement medication log create endpoint (POST /medication-logs) `backend/app/api/medication_logs.py`
- [ ] T052 [P] [US3] Implement medication log list endpoint (GET /medication-logs) `backend/app/api/medication_logs.py`
- [ ] T053 [US3] Implement active medication guard in `backend/app/services/active_fk_guard.py`
- [ ] T054 [US3] Integration test medication log creation & inactive exclusion `backend/tests/integration/test_medication_log_creation.py`
- [ ] T055 [US3] Frontend medication log form update `frontend/src/components/logging/MedicationLogForm.tsx`
- [ ] T056 [US3] Frontend medication dropdown reuse `frontend/src/components/common/SearchableDropdown.tsx`
- [ ] T057 [US3] Component tests medication log form `frontend/__tests__/MedicationLogForm.test.tsx`
- [ ] T058 [US3] E2E test medication logging flow `frontend/tests/e2e/medication-log.spec.ts`

## Phase 6: User Story 4 (P4) Infer Symptom End Time

Goal: Remove end time input; infer on backend; ensure display accuracy.
Independent Test Criteria: Start + duration yields correct end time; edits recalc end time.

- [ ] T059 [US4] Remove end time field from frontend form `frontend/src/components/logging/SymptomLogForm.tsx`
- [ ] T060 [US4] Backend inference logic finalize & ensure ended_at stored `backend/app/services/symptom_log_service.py`
- [ ] T061 [US4] Update schema/read model to show inferred end time `backend/app/api/symptom_logs.py`
- [ ] T062 [US4] Update component tests for end time removal `frontend/__tests__/SymptomLogForm.test.tsx`
- [ ] T063 [US4] E2E test verifying inferred end time display `frontend/tests/e2e/symptom-log-endtime.spec.ts`

## Phase 7: Polish & Cross-Cutting

Goal: Logging enrichment, documentation, accessibility, readiness review.

- [ ] T064 Add structured logging fields (entity_type, action, duration_bucket) `backend/app/services/symptom_log_service.py`
- [ ] T065 [P] Add structured logging for symptom type actions `backend/app/services/symptom_type_service.py`
- [ ] T066 Add accessibility attributes to dropdown `frontend/src/components/common/SearchableDropdown.tsx`
- [ ] T067 Add quickstart documentation update `specs/004-lean-mode-use/quickstart.md`
- [ ] T068 Add performance profiling script for dropdown `frontend/src/scripts/profile_dropdown.ts`
- [ ] T069 [P] Add final contract diff test `backend/tests/contract/test_feature_004_contract.py`
- [ ] T070 Add readiness review checklist update in `reports/quality-gate-summary.md`
- [ ] T071 Add migration documentation snippet `specs/004-lean-mode-use/data-model.md`
- [ ] T072 Final accessibility audit test script `frontend/tests/a11y/symptom-log-a11y.spec.ts`

## Dependency Graph (User Story Order)

US1 (Symptom Type Management) -> US2 (Symptom Symptom Logging via Dropdown) -> US3 (Medication Logging Dropdown) -> US4 (End Time Inference)

Foundational (Phase 2) must precede all User Stories.

## Parallel Execution Examples

- T012 and T015 can run in parallel (separate model files).
- T021, T022, T023 unit tests can run in parallel after services ready.
- T032 audit diff tests parallel with T031 integration once CRUD implemented.
- Frontend components T045, T046, T047, T048 can be parallel after backend endpoints available.

## Implementation Strategy (MVP First)

MVP Scope: Complete US1 + foundational backend (Phases 2 & 3) to deliver Symptom Type management and its contract tests. Defer symptom logging (US2) until types stable.

Incremental Delivery:

1. Migrate & define models.
2. CRUD Symptom Type endpoints + tests (deployable MVP).
3. Add Symptom logging with duration confirmation & inference.
4. Extend to Medication logging.
5. Polish with end time inference UI removal and structured logging.

## Format Validation

All tasks follow required pattern: `- [ ] T### [P?] [US#?] Description with file path`. Parallelizable tasks marked with [P]. Story phases include [USn]. Non-story phases omit story labels.

## Task Counts

- Total Tasks: 72
- US1 Tasks: 14 (T025-T038)
- US2 Tasks: 12 (T039-T050)
- US3 Tasks: 8 (T051-T058)
- US4 Tasks: 5 (T059-T063)
- Setup Tasks: 10 (T001-T010)
- Foundational Tasks: 14 (T011-T024)
- Polish Tasks: 9 (T064-T072)

## Independent Test Criteria Summary

- US1: CRUD + deactivate + dropdown presence
- US2: Defaults apply, duration conversion, long-duration confirmation, end time inference
- US3: Medication FK logging & inactive exclusion
- US4: End time correctly inferred on create/edit, field removed from form

## Parallel Opportunities Identified

Listed in Parallel Execution Examples section; additional concurrency possible for distinct frontend components post-backend stabilization.

## MVP Scope Recommendation

Deliver Phases 1-3 (through US1) for initial value: normalized symptom types enabling consistent logging groundwork.

---

Generated by speckit.tasks workflow.

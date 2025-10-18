# Tasks: SaaS Medical Tracker (Logs, Medication Master, Conditions & Doctors)

**Input**: Design documents from `/specs/001-saas-medical-tracker/`
**Prerequisites**: plan.md (required), spec.md (required), research.md (available), data-model.md (pending), contracts/ (pending)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize repo layout, toolchains, and baseline configs so subsequent phases can focus on feature logic.

- [x] T001 Create directory structure per plan (backend/app/{api,core,models,services,schemas,telemetry}, backend/tests/{unit,integration,contract}, frontend/src/{app,components,lib,styles}, frontend/tests/{unit,e2e}, contracts, scripts)
- [x] T002 Initialize backend Python project (pyproject.toml or requirements + lock) in `backend/` with FastAPI, SQLModel, pydantic, uvicorn, pytest, httpx, pytest-cov, alembic
- [x] **T003** - Initialize Alembic in backend/ (database migrations framework)
- [x] **T004** - Initialize frontend Next.js with TypeScript App Router, shadcn/ui
- [x] **T005** - Add ESLint configuration in `frontend/` with TypeScript, React, and accessibility rules
- [x] T006 Add Ruff (or flake8) + mypy config in `backend/` (`pyproject.toml` or tool config files)
- [x] T007 [P] Add shared `.editorconfig` and `.gitignore` at repo root
- [x] T008 [P] Create initial README.md at root referencing feature and dev commands
- [x] T009 Set up Python virtual environment / uv config and lock dependencies (`backend/requirements.lock` or uv generated)
- [x] T010 Add pre-commit config with black/ruff/mypy/eslint hooks (`.pre-commit-config.yaml`)
- [x] T011 Configure basic GitHub Actions / CI skeleton (lint, typecheck, test, backend build) `.github/workflows/ci.yml`
- [x] T012 [P] Add LICENSE and CODEOWNERS files
- [x] T013 [P] Add scripts: `scripts/generate-types.ps1` (calls openapi-typescript when contract exists), `scripts/run-dev.ps1` (concurrent backend/frontend)
- [x] T014 Configure environment sample `.env.example` (JWT_SECRET, DATABASE_URL=sqlite:///app.db, etc.)
- [x] T015 [P] Add Makefile or package.json scripts for convenience (optional) at root for aggregate commands
- [x] T016 Add initial backend `app/main.py` with FastAPI app factory placeholder
- [x] T017 Add frontend base layout & global style imports (`frontend/src/app/layout.tsx`, `globals.css`)
- [x] T018 [P] Add initial telemetry placeholders (`backend/app/telemetry/__init__.py`) with TODOs for metrics
- [x] T019 Add basic logging config (`backend/app/core/logging.py`) and wire to `main.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infra & cross-cutting concerns required before any user story’s domain features.
**Blocking Rule**: User story phases must not begin until every foundational task is complete.

- [x] T020 Define initial OpenAPI stub `contracts/openapi.yaml` with info + empty paths section
- [x] T021 Implement settings module (`backend/app/core/settings.py`) loading env vars & defaults
- [x] T022 [P] Configure DB engine + session dependency (`backend/app/core/db.py`) for SQLite
- [x] T023 Create base SQLModel entities skeleton file (`backend/app/models/base.py` with metadata)
- [x] T024 Create Pydantic base schema module (`backend/app/schemas/base.py` for shared configs)
- [x] T025 Implement auth stub: minimal JWT util (`backend/app/core/auth.py`) issue/verify tokens
- [x] **T026** Implement comprehensive dependency injection patterns (`backend/app/core/dependencies.py`) with database sessions, authentication, configuration, and service layer components following FastAPI best practices
- [x] **T027** [P] Add global exception handlers & error response model (`backend/app/core/errors.py`)
- [x] T028: Middleware system (request ID, timing, security headers) ✅
- [x] T029 Add metrics endpoint scaffold (`backend/app/telemetry/metrics.py`) exporting Prometheus registry ✅
- [x] T030 Wire telemetry & middleware in `app/main.py` ✅
- [x] T031 Implement initial CI contract diff placeholder job (references openapi.yaml even if sparse) ✅
- [x] T032 [P] Setup frontend API client generator placeholder `frontend/src/lib/api/client.ts` referencing future generated types ✅
- [x] T033 [P] Add frontend design system tokens / Tailwind config (`frontend/tailwind.config.ts`) ✅
- [x] T034 Document dev flow in `README.md` (run backend, frontend, type generation) update ✅
- [x] T035 Add initial unit test harness backend (`backend/tests/unit/test_sanity.py`), frontend (`frontend/tests/unit/sanity.test.ts`) ✅
- [x] T036 [P] Add Playwright config (`frontend/tests/e2e/playwright.config.ts`) and placeholder spec ✅
- [x] T037 Ensure coverage thresholds config (backend `pytest.ini`, frontend `vitest.config.ts`)
- [x] T038 [P] Update `.github/workflows/ci.yml` adding coverage report & bundle size guard placeholder
- [x] T039 Add accessibility testing placeholder (`frontend/tests/unit/a11y.setup.ts`) with axe config
- [x] T040 Confirm lint/type/test pipeline passes (manual run documented in README)

---

## Phase 3: User Story 1 - Log Daily Medication & Symptoms (Priority: P1) 🎯 MVP

**Goal**: Enable users to log medication & symptom entries and view landing page summaries plus dynamic feel-vs-yesterday status.
**Independent Test**: User can create one medication log + one symptom log and see both in landing summaries & computed status.

### Tests (Write First, Then Implement)

- [x] T041 [P] [US1] Contract tests for /logs/medications & /logs/symptoms & /feel-vs-yesterday in `backend/tests/contract/test_logs.py`
- [x] T042 [P] [US1] Backend integration test for feel-vs-yesterday logic `backend/tests/integration/test_feel_vs_yesterday.py`
- [x] T043 [P] [US1] Frontend component test: log forms & summary lists `frontend/tests/unit/logging-forms.test.tsx`
- [x] T044 [P] [US1] E2E test logging flow `frontend/tests/e2e/us1-logging.spec.ts`

### Implementation (US1)

- [x] T045 [P] [US1] Define MedicationLog & SymptomLog models `backend/app/models/logs.py`
- [x] T046 [P] [US1] Add migrations for log tables `backend/alembic/versions/*_create_logs.py`
- [x] T047 [P] [US1] Create schemas for logs & feel response `backend/app/schemas/logs.py`
- [x] T048 [US1] Implement feel vs yesterday service `backend/app/services/feel_service.py`
- [x] T049 [US1] Implement logs router (create/list) `backend/app/api/logs.py`
- [x] T050 [US1] Implement feel vs yesterday endpoint `backend/app/api/feel.py`
- [x] T051 [US1] Update openapi.yaml paths for logs & feel endpoints
- [x] T052 [US1] Generate TS types `contracts/types/` via script after contract update
- [x] T053 [US1] Implement frontend logging forms (med + symptom) `frontend/src/app/(landing)/components/log-forms.tsx`
- [x] T054 [US1] Implement landing summaries (last 5 lists) `frontend/src/app/(landing)/components/summaries.tsx`
- [x] T055 [US1] Implement feel status component `frontend/src/app/(landing)/components/feel-status.tsx`
- [x] T056 [US1] Wire API client calls & optimistic UI updates `frontend/src/lib/api/logging.ts`
- [x] T057 [US1] Add accessibility adjustments (labels, aria-live for status) `frontend/src/app/(landing)/components/feel-status.tsx`
- [x] T058 [US1] Add logging/metrics instrumentation to backend API router endpoints
- [x] T059 [US1] Update E2E test data selectors in `us1-logging.spec.ts` if needed
- [x] T060 [US1] Update README feature section with US1 usage example
- [x] T061 [US1] Quality gate: run Lighthouse & record scores (attach JSON) `docs/perf/us1-lighthouse.json`

**Checkpoint**: US1 independently functional (MVP).

---

## Phase 4: User Story 2 - Manage Medication Master Data (Priority: P2)

**Goal**: CRUD & deactivate medication master records; selection limited to active meds.
**Independent Test**: User can create, edit, deactivate medications; logs only allow active selections.

### Tests (US2)

- [x] T062 [P] [US2] Contract tests for /medications endpoints `backend/tests/contract/test_medications.py`
- [x] T063 [P] [US2] Integration test deactivation behavior `backend/tests/integration/test_medication_deactivate.py`
- [x] T064 [P] [US2] Frontend component test medication form & list `frontend/tests/unit/medications.test.tsx`

### Implementation (US2)

- [x] T065 [P] [US2] Define MedicationMaster model `backend/app/models/medication.py`
- [x] T066 [P] [US2] Migration for medication master table `backend/alembic/versions/*_create_medication_master.py`
- [x] T067 [P] [US2] Schemas for medication master `backend/app/schemas/medication.py`
- [x] T068 [US2] Service for medication CRUD + deactivate `backend/app/services/medication.py`
- [x] T069 [US2] Router for medications `backend/app/api/v1/endpoints/medications.py`
- [x] T070 [US2] Update openapi.yaml with medication paths
- [x] T071 [US2] Regenerate TS types after contract update
- [x] T072 [US2] Frontend medication management page `frontend/src/app/dashboard/medications/page.tsx`
- [x] T073 [US2] Medication form & search component `frontend/src/components/medications/`
- [x] T074 [US2] Frontend medication management components (list, form, search) `frontend/src/components/medications/`
- [x] T075 [US2] Add dashboard navigation and routing for medication management
- [x] T076 [US2] Add logging & metrics instrumentation `backend/app/api/medications.py`
- [x] T077 [US2] Update docs with medication management section `README.md`
- [x] T078 [US2] Lighthouse & accessibility check for medications page `docs/perf/us2-lighthouse.json`

**Checkpoint**: US2 complete & independent (US1 unaffected).

---

## Phase 5: User Story 3 - Condition Passport & Doctor Directory (Priority: P3)

**Goal**: Manage conditions & doctors, produce aggregated passport view.
**Independent Test**: User adds a condition, links doctor, views passport with association.

### Tests (US3)

- [x] T079 [P] [US3] Contract tests for /conditions, /doctors, /passport `backend/tests/contract/test_passport.py`
- [x] T080 [P] [US3] Integration test doctor-condition link `backend/tests/integration/test_doctor_condition_link.py`
- [x] T081 [P] [US3] Frontend component test passport rendering `frontend/tests/unit/passport.test.tsx`

### Implementation (US3)

- [x] T082 [P] [US3] Define Condition & Doctor models `backend/app/models/medical_context.py`
- [x] T083 [P] [US3] Migration for condition & doctor tables `backend/alembic/versions/*_create_condition_doctor.py`
- [x] T084 [P] [US3] Schemas for condition & doctor `backend/app/schemas/medical_context.py`
- [x] T085 [US3] Services for condition CRUD & doctor CRUD/link `backend/app/services/medical_context_service.py`
- [x] T086 [US3] Routers for conditions, doctors, passport `backend/app/api/medical_context.py`
- [x] T087 [US3] Update openapi.yaml with condition, doctor, passport paths
- [x] T088 [US3] Regenerate TS types after contract update
- [x] T089 [US3] Passport page `frontend/src/app/passport/page.tsx`
- [x] T090 [US3] Doctor management page `frontend/src/app/doctors/page.tsx`
- [x] T091 [US3] Components: condition form, doctor form, passport list `frontend/src/app/passport/components/*`
- [x] T092 [US3] Logging & metrics instrumentation `backend/app/api/medical_context.py`
- [x] T093 [US3] Accessibility & Lighthouse check passport/doctor pages `docs/perf/us3-lighthouse.json`

**Checkpoint**: US3 complete & independent.

---

## Phase 6: Polish & Cross-Cutting

**Purpose**: Hardening, performance, accessibility, security alignment, and docs.

- [x] T094 Add threat review document `docs/security/threat-review.md`
- [x] T095 [P] Add performance profiling script `scripts/profile_backend.py`
- [x] T096 [P] Add web vitals collection endpoint `/telemetry/web-vitals` `backend/app/api/telemetry.py`
- [x] T097 Add tracing headers propagation update `backend/app/core/middleware.py`
- [x] T098 [P] Add caching layer placeholder (NOT ENABLED) comment & doc `backend/app/services/cache_placeholder.py`
- [x] T099 Update openapi.yaml descriptions & tags refinements
- [x] T100 Run full CI & quality gate summary doc `docs/release/usmvp-quality-report.md`
- [x] T101 [P] Update README quickstart & usage examples per all stories
- [x] T102 Accessibility regression audit across pages `docs/a11y/audit-round2.md`
- [x] T103 [P] Add DB migration rollback test `backend/tests/integration/test_migrations.py`
- [x] T104 Final cleanup: remove unused TODO comments

---

## Dependencies & Execution Order

### Story Order

1. US1 (MVP) → 2. US2 → 3. US3 (independent after foundational; sequential for focus)

### High-Level Dependencies

- Phase 1 → Phase 2 → (US1, US2, US3) → Phase 6
- Contract changes (T051, T070, T087) precede type generation (T052, T071, T088)
- Models before migrations before routers (where listed) except parallelizable flagged tasks

### Parallel Opportunities

- Setup parallel: T007, T008, T012, T013, T015, T018 can run simultaneously
- Foundational parallel: T022, T027, T028, T032, T033, T036, T038, T039
- US1 parallel clusters: (T045,T046,T047) models/migration/schemas; tests T041–T044; frontend components (T053–T055)
- US2 & US3 model/schema/migration groups parallel once started

## MVP Scope Suggestion

Deliver through T061 (end of US1) for MVP; defer medication master and passport to subsequent releases.

## Task Counts

- Total Tasks: 104
- Phase 1: 19
- Phase 2: 21 (T020–T040)
- US1: 21 (T041–T061)
- US2: 17 (T062–T078)
- US3: 15 (T079–T093)
- Polish: 11 (T094–T104)

## Format Validation

All tasks follow `- [ ] T### [P]? [US?] Description with file path` format. Story phases include labels `[US1]`, `[US2]`, `[US3]`; non-story phases omit story labels. Parallelizable tasks marked `[P]` where independent.

# Tasks: Login UI & Conditional Access

Update (2025-10-28): Backend auth tests stabilized. Adjustments made:

> - Added package markers to avoid test module import collisions.
> - Normalized registration status codes to 201 across integration & contract tests.
> - Enhanced conflict response shape (EMAIL_EXISTS + EMAIL_IN_USE compatibility).
> - Implemented functional `/auth/me` identity endpoint replacing stub for login integration tests.
> - Added missing `async_client` fixture alias and corrected session timeout helper.
> - Unified identity envelope shape for consistency.
> All auth-related tests now passing (73 passed / 1 skipped under -k auth).

**Input**: plan.md, spec.md, data-model.md, contracts/auth.yaml, quickstart.md
**Feature Branch**: 003-implement-login-ui

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure baseline repo tooling supports the feature work and contract-first flow.

- [x] T001 Align backend telemetry directory readiness (`backend/app/telemetry/`) for new auth metrics
- [x] T002 Ensure OpenAPI contract generation script recognizes delta (`scripts/generate-types.ps1`) and add note if needed
- [x] T003 [P] Verify frontend test harness config for new data-testids (`frontend/tests/setup.ts`)
- [x] T004 [P] Confirm existing auth endpoints present in root `contracts/openapi.yaml` and reference delta file path in README (spec addendum)

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish any missing primitives & guards required before story slices begin.

- [x] T005 Implement `/auth/me` identity endpoint contract stub in `backend/app/api/auth_identity.py`
- [x] T006 Add masked email utility in `backend/app/services/masking.py`
- [x] T007 [P] Add Pydantic schema for AuthResponse identity extension in `backend/app/schemas/auth.py`
- [x] T008 [P] Add cookie settings constants (Secure, HttpOnly, SameSite) in `backend/app/core/security.py`
- [x] T009 Integrate identity endpoint router into FastAPI app (`backend/app/main.py`)
- [x] T010 Wire contract tests scaffold for auth endpoints in `backend/tests/contract/test_auth_contract.py`
- [x] T011 [P] Add frontend shared auth client in `frontend/src/lib/auth/client.ts`
- [x] T012 [P] Add frontend masking util (mirrors backend) in `frontend/src/lib/auth/mask.ts`
- [x] T013 Create protected layout guard (no flash) in `frontend/src/app/(protected)/layout.tsx`
- [x] T014 Instrument base metrics registry additions (`backend/app/telemetry/metrics_auth.py`)
- [x] T015 Add structured log pattern for auth events in `backend/app/telemetry/logging_auth.py`
- [x] T016 [P] Update quickstart with identity endpoint usage (`specs/003-implement-login-ui/quickstart.md`)

## Phase 3: User Story 1 - Access Gate & Login (Priority: P1) 🎯 MVP

**Goal**: Unified access screen with working login preventing protected content flash.
**Independent Test**: Fresh session → visit protected route → see access screen → perform login → redirect to dashboard without pre-auth protected render.

### Tests (write first; ensure initial fail)

- [x] T017 [P] [US1] Backend contract test for login success/failure (`backend/tests/contract/test_login.py`)
- [x] T018 [P] [US1] Backend integration test guarding protected route (`backend/tests/integration/test_access_guard.py`)
- [x] T019 [P] [US1] Frontend component test for LoginForm (`frontend/__tests__/LoginForm.test.tsx`)
- [x] T020 [P] [US1] Frontend e2e test login flow (`frontend/tests/e2e/login.spec.ts`)

### Implementation (US1)

- [x] T021 [P] [US1] Implement login handler enhancements (generic error) `backend/app/api/auth_login.py`
- [x] T022 [P] [US1] Add failure path masking logic usage `backend/app/services/auth_service.py`
- [x] T023 [US1] Add duplicate submission guard state to login endpoint `backend/app/api/auth_login.py`
- [x] T024 [US1] Create AccessScreen route `frontend/src/app/access/page.tsx`
- [x] T025 [P] [US1] Implement LoginForm component `frontend/src/components/auth/LoginForm.tsx`
- [x] T026 [P] [US1] Implement access screen mode toggle logic `frontend/src/components/auth/AuthToggle.tsx`
- [x] T027 [US1] Add loading state overlay & disable logic `frontend/src/components/auth/LoginForm.tsx`
- [x] T028 [US1] Integrate guard layout with cookie-based state detection `frontend/src/app/(protected)/layout.tsx`
- [x] T029 [US1] Add generic error messaging (no enumeration) `frontend/src/components/auth/LoginForm.tsx`
- [x] T030 [US1] Add accessibility attributes & testids `frontend/src/components/auth/LoginForm.tsx`
- [x] T031 [US1] Backend logging hooks for login attempts `backend/app/telemetry/logging_auth.py`
- [x] T032 [US1] Metrics increments on login success/failure `backend/app/telemetry/metrics_auth.py`
- [x] T033 [US1] Update OpenAPI delta with identity example `specs/003-implement-login-ui/contracts/auth.yaml`
- [x] T034 [US1] Frontend auth client login method `frontend/src/lib/auth/client.ts`

## Phase 4: User Story 2 - Registration & First Entry (Priority: P2)

**Goal**: Registration from same access screen with automatic login + success banner.
**Independent Test**: Fresh session → register new unique email → auto-login → dashboard + banner.

### Tests (US2)

- [x] T035 [P] [US2] Backend contract test for registration success/conflict (`backend/tests/contract/test_register.py`)
- [x] T036 [P] [US2] Frontend component test for RegisterForm (`frontend/__tests__/RegisterForm.test.tsx`)
- [x] T037 [P] [US2] E2E test registration flow (`frontend/tests/e2e/register.spec.ts`)

### Implementation (US2)

- [x] T038 [P] [US2] Implement register handler with password strength validation `backend/app/api/auth_register.py`
- [x] T039 [US2] Add generic conflict response path `backend/app/api/auth_register.py`
- [x] T040 [P] [US2] Extend auth service for registration + immediate session `backend/app/services/auth_service.py`
- [x] T041 [US2] Create RegisterForm component `frontend/src/components/auth/RegisterForm.tsx`
- [x] T042 [US2] Add password strength meter guidance `frontend/src/components/auth/RegisterForm.tsx`
- [x] T043 [US2] Banner component for first registration success `frontend/src/components/auth/RegistrationBanner.tsx`
- [x] T044 [US2] Preserve field state on validation errors `frontend/src/components/auth/RegisterForm.tsx`
- [x] T045 [US2] Integrate register flow with access screen toggle `frontend/src/components/auth/AuthToggle.tsx`
- [x] T046 [US2] Metrics increments for registration attempts `backend/app/telemetry/metrics_auth.py`
- [x] T047 [US2] Structured logs for registration outcomes `backend/app/telemetry/logging_auth.py`
- [x] T048 [US2] Update contract examples for registration `specs/003-implement-login-ui/contracts/auth.yaml`

## Phase 5: User Story 3 - Authenticated Top Bar Identity & Logout (Priority: P3)

**Goal**: Display identity (display name or masked email) in top bar + accessible logout control clearing session.
**Independent Test**: Login → identity visible (masked if no display name) → logout → access screen; no protected flicker.

### Tests (US3)

- [x] T049 [P] [US3] Backend contract test for logout idempotency (`backend/tests/contract/test_logout.py`)
- [x] T050 [P] [US3] Frontend component test for TopBarIdentity (`frontend/__tests__/TopBarIdentity.test.tsx`)
- [x] T051 [P] [US3] E2E test logout flow (`frontend/tests/e2e/logout.spec.ts`)

### Implementation (US3)

- [x] T052 [P] [US3] Implement logout handler cookie clearing `backend/app/api/auth/logout.py`
- [x] T053 [US3] Add idempotent logout logic to auth service `backend/app/services/auth_service.py`
- [x] T054 [P] [US3] TopBarIdentity component with truncation `frontend/src/components/auth/TopBarIdentity.tsx`
- [x] T055 [P] [US3] LogoutButton component with ARIA & testids `frontend/src/components/auth/LogoutButton.tsx`
- [x] T056 [US3] Tooltip/accessible description for truncated identity `frontend/src/components/auth/TopBarIdentity.tsx`
- [x] T057 [US3] Add progress indicator during logout `frontend/src/components/auth/LogoutButton.tsx`
- [x] T058 [US3] Metrics increments on logout `backend/app/telemetry/metrics_auth.py`
- [x] T059 [US3] Structured logs for logout outcomes `backend/app/telemetry/logging_auth.py`
- [x] T060 [US3] Identity derivation via `/auth/me` integration `frontend/src/lib/auth/client.ts`

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Regression, accessibility, performance, coverage, docs completeness.

- [ ] T061 Add accessibility axe audit script updates (`frontend/tests/e2e/accessibility.spec.ts`)
- [ ] T062 [P] Performance measurement script for login/register (`scripts/profile_backend.py`)
- [ ] T063 Regression suite run & coverage check updates (`backend/run_pytest_uv.ps1`, `frontend/package.json` scripts)
- [ ] T064 [P] Bundle size diff guard addition (`frontend/package.json`) & threshold config
- [ ] T065 Update documentation of masking logic (`docs/security/threat-review.md`)
- [ ] T066 Add testids to all new components (`frontend/src/components/auth/*.tsx`)
- [ ] T067 [P] Update quickstart with final flows & test commands (`specs/003-implement-login-ui/quickstart.md`)
- [ ] T068 Add README section for login feature summary (`README.md`)
- [ ] T069 [P] Final metrics validation script addition (`backend/scripts/metrics_probe.py`)
- [ ] T070 Consolidate structured log examples in docs (`docs/feature_ideas/implement_login.md`)

## Dependencies & Execution Order

Phase Ordering:

1. Setup → 2. Foundational (blocking) → 3. US1 → 4. US2 → 5. US3 → 6. Polish

User Story Independence:

- US1 can start once Foundational done.
- US2 independent of US1 implementation details (shares toggle component) but can begin after Foundational.
- US3 depends on `/auth/me` (from Foundational) and login flow completion semantics (cookie issued); starts after US1 ideally but can parallel after US1 endpoint stable.

## Parallel Opportunities

- Marked [P] tasks across phases (telemetry setup, utilities, client libs, component creations) can proceed simultaneously by different contributors.
- All contract tests (T017, T035, T049) can be authored in parallel once schemas known.
- Frontend component implementations (LoginForm, RegisterForm, TopBarIdentity, LogoutButton) can progress concurrently post Foundational.

## Implementation Strategy

MVP = Phase 1 + Phase 2 + User Story 1 (login working, guarded layout). Deliver early for stakeholder review.
Incremental follow: User Story 2 (registration), then User Story 3 (logout/identity), then Polish full regression (SC-009).

## Task Counts

Total Tasks: 70

- Setup: 4
- Foundational: 12
- US1: 17 (Tests 4, Impl 13)
- US2: 14 (Tests 3, Impl 11)
- US3: 12 (Tests 3, Impl 9)
- Polish: 11

## Independent Test Criteria Summary

- US1: Login flow + protected route guard redirect
- US2: Registration auto-login + success banner display
- US3: Identity display + logout idempotent redirect

## MVP Scope Recommendation

Include tasks through T034 (end of US1 implementation). Stop, validate performance & accessibility baseline, then proceed.

## Format Validation

All tasks follow: - [ ] T### optional [P] optional [USx] Description with explicit file path.

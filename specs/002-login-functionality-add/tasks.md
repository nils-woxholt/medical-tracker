# Task Breakdown: User Authentication (Login & Registration)

**Feature Branch**: `002-login-functionality-add`
**Source**: `spec.md`, `plan.md`, `data-model.md`, `quickstart.md`, `contracts/openapi.yaml`

---

## Phase 1: Setup

Minimal environment & scaffolding enabling subsequent story phases.

- [X] T001 Initialize backend auth package structure (`backend/app/api/auth/__init__.py`) & placeholder router file (`backend/app/api/auth/routes.py`)
- [X] T002 Create backend services directory scaffold if absent (`backend/app/services/__init__.py`)
- [X] T003 Add OpenAPI generation script hook reference in README (update `backend/README.md`) for auth endpoints
- [X] T004 Add frontend auth components folder (`frontend/src/components/auth/`) with placeholder README
- [X] T005 Ensure OpenAPI types generation script references new contract paths (`scripts/generate-types.ps1`)
- [X] T006 [P] Add initial test folders for dedicated auth tests (`backend/tests/unit/auth/`, `backend/tests/integration/auth/`)
- [X] T007 Update backend settings to include auth constants (idle timeout, lockout) (`backend/app/core/settings.py`)
- [X] T008 [P] Add audit logging categories enumerations (`backend/app/telemetry/audit_events.py`)

## Phase 2: Foundational (Blocking Prerequisites)

Data model, migrations, utilities required by all user stories.

- [X] T009 Create/extend User model with lockout fields (`failed_attempts`, `lock_until`) (`backend/app/models/user.py`)
- [X] T010 Create Session model/entity (`backend/app/models/session.py`)
- [X] T011 Generate Alembic migration for user and session changes (`backend/alembic/versions/xxxx_add_auth_tables.py`)
- [X] T012 Implement password hashing utility (bcrypt) (`backend/app/services/password_hashing.py`)
- [X] T013 Implement email normalization helper (`backend/app/services/email_normalization.py`)
- [X] T014 Implement session service (create, touch, revoke, cleanup) (`backend/app/services/session_service.py`)
- [X] T015 Implement lockout evaluation helper (`backend/app/services/lockout.py`)
- [X] T016 [P] Implement audit event recorder (`backend/app/telemetry/audit_recorder.py`)
- [X] T017 Implement structured logging helpers for auth flows (`backend/app/telemetry/logging_auth.py`)
- [X] T018 [P] Add metrics counters & gauge definitions (`backend/app/telemetry/metrics_auth.py`)
- [X] T019 Implement auth cookie helper (set, clear attributes) (`backend/app/services/cookie_helper.py`)
- [X] T020 Add backend dependency injection wiring for services (`backend/app/core/dependencies_auth.py`)
- [X] T021 [P] Frontend: add auth API client wrapper using generated types (`frontend/src/lib/api/authClient.ts`)
- [X] T022 Frontend: add session context provider scaffold (`frontend/src/lib/auth/sessionContext.tsx`)

## Phase 3: User Story 1 - Return User Logs In (Priority: P1)

Implements core login capability for existing users.

- [X] T023 [US1] Implement login endpoint (POST /auth/login) (`backend/app/api/auth/login.py`)
- [X] T024 [P] [US1] Implement logout endpoint (POST /auth/logout) (`backend/app/api/auth/logout.py`)
- [X] T025 [US1] Implement auth middleware/session extraction (`backend/app/core/middleware/session_middleware.py`)
- [X] T026 [P] [US1] Frontend login page with form & validation (`frontend/src/app/(auth)/login/page.tsx`)
- [X] T027 [US1] Frontend protected route guard/hook (`frontend/src/lib/auth/useSessionGuard.ts`)
- [X] T028 [P] [US1] Backend unit tests: password hashing & lockout reset (`backend/tests/unit/auth/test_password_and_lockout.py`)
- [X] T029 [US1] Backend integration tests: login success/failure (`backend/tests/integration/auth/test_login.py`)
- [X] T030 [P] [US1] Frontend component tests: login form validation (`frontend/__tests__/LoginForm.test.tsx`)
- [X] T031 [US1] E2E test: login flow & redirect back to protected page (`frontend/tests/e2e/auth/login.spec.ts`)
- [X] T031A [FR-017] [US1] Preserve original route: implement & test redirect logic capturing pre-auth path (middleware + login success) (`frontend/src/lib/auth/useSessionGuard.ts`, `backend/app/core/middleware/session_middleware.py`, `frontend/tests/e2e/auth/login_redirect.spec.ts`)
- [X] T032 [US1] Add audit logging calls (success/failure) in login & logout handlers (`backend/app/api/auth/login.py`, `backend/app/api/auth/logout.py`)

## Phase 4: User Story 2 - New User Registers (Priority: P2)

Registration path establishing account and session.

- [X] T033 [US2] Implement registration endpoint (POST /auth/register) (`backend/app/api/auth/register.py`)
- [X] T034 [P] [US2] Email uniqueness & normalization validation integration (`backend/app/services/email_normalization.py`)
- [X] T035 [US2] Frontend registration page UI & validation (`frontend/src/app/(auth)/register/page.tsx`)
- [X] T036 [P] [US2] Backend integration tests: registration success/failure (`backend/tests/integration/auth/test_register.py`)
- [X] T037 [US2] Frontend component tests: registration form (`frontend/__tests__/RegisterForm.test.tsx`)
- [X] T038 [US2] E2E test: register then auto-authenticated experience (`frontend/tests/e2e/auth/register.spec.ts`)
- [X] T039 [US2] Audit logging: registration event (`backend/app/api/auth/register.py`)

## Phase 5: User Story 3 - Session Persistence & Demo Access (Priority: P3)

Continuity & demo path.

- [X] T040 [US3] Implement session status endpoint (GET /auth/session) (`backend/app/api/auth/session.py`)
- [X] T041 [P] [US3] Implement demo access endpoint (POST /auth/demo) (`backend/app/api/auth/demo.py`)
- [X] T042 [US3] Extend session middleware for idle timeout enforcement (`backend/app/core/middleware/session_middleware.py`)
- [X] T043 [US3] Frontend session refresh hook (`frontend/src/lib/session.ts`)
- [X] T044 [P] [US3] Frontend demo access UI (banner injected in dashboard layout) (`frontend/src/components/auth/DemoSessionBanner.tsx`)
- [X] T045 [US3] Backend integration tests: session persistence & timeout (`backend/tests/integration/auth/test_session_timeout.py`)
- [X] T046 [P] [US3] Backend integration tests: demo session isolation (`backend/tests/integration/auth/test_demo_session.py`)
- [X] T047 [US3] Frontend component tests: demo banner visibility (`frontend/__tests__/DemoSessionBanner.test.tsx`)
- [X] T048 [US3] E2E test: demo access flow & timeout (`frontend/tests/e2e/auth/demo_session.spec.ts`)
- [X] T049 [US3] Audit logging: demo session initiation (`backend/app/api/auth/demo.py`)

## Phase 6: Polish & Cross-Cutting

Refinements, accessibility, performance, observability finalization.

- [X] T050 [FR-016] Add accessibility enhancements (auto-focus first input, focus management) (`frontend/src/app/(auth)/login/page.tsx`, `frontend/src/app/(auth)/register/page.tsx`)
- [X] T051 [P] Add metrics emission in endpoints (counters, gauge adjustments) (`backend/app/api/auth/*.py`)
- [X] T052 Improve structured log context (user id/session id correlation) (`backend/app/telemetry/logging_auth.py`)
- [X] T053 [P] Implement session cleanup scheduled task (idle expiry) (`backend/app/services/session_cleanup.py`)
- [X] T054 Security hardening review & minor fixes (`backend/app/api/auth/*.py`, `frontend/src/lib/auth/*`)
- [X] T055 [P] Contract fuzzing tests using schemathesis for /auth/* (`backend/tests/contract/test_auth_contract.py`)
- [X] T056 Add rate limiting integration if available (placeholder) (`backend/app/services/rate_limit.py`)
- [X] T057 Final audit & metrics validation script (`backend/tests/integration/auth/test_audit_metrics.py`)
- [X] T058 Frontend: add logout menu item & session expired UX (`frontend/src/components/auth/LogoutMenu.tsx`)
- [X] T059 Final documentation updates (README, quickstart adjustments) (`specs/002-login-functionality-add/quickstart.md`, `backend/README.md`)

---

## Dependency Graph (Story Order)

1. Setup (Phase 1)
2. Foundational (Phase 2)
3. US1 (Phase 3) – depends on Foundational
4. US2 (Phase 4) – depends on Foundational (shared user model) but can parallel some test tasks with late US1 endpoint completion
5. US3 (Phase 5) – depends on session service & middleware from US1
6. Polish (Phase 6) – depends on all prior

## Parallel Execution Examples

- During Phase 2: T016, T018, T021 can run parallel while core models (T009–T015) progress.
- Phase 3: T024, T026, T028, T030 can run parallel to T023 & T025 sequential pieces.
- Phase 5: T041, T044, T046, T047 can run parallel while T040, T042, T043 provide base continuity.
- Phase 6: T051, T053, T055 can run parallel while T050 and T052 refine UX/logging.

## Independent Test Criteria per Story

- US1: Successful login + redirect; failed login generic error; logout clears session.
- US2: Unique registration creates account + immediate auth; duplicate email rejection; password policy enforcement.
- US3: Session persists across navigation; idle timeout triggers re-auth flow; demo session clearly labeled & isolated.

## MVP Recommendation

Implement through Phase 3 (US1) for a deployable MVP enabling returning user login & logout plus foundational structure.

## Validation

All tasks follow required checklist format with IDs, optional [P] markers, and story labels for story phases.

## Counts

Total Tasks: 59 (no change)
Phase 1: 8
Phase 2: 14 (4 completed newly: T012–T015)
Phase 3 (US1): 10 (1 in progress: T023)
Phase 4 (US2): 7
Phase 5 (US3): 10
Phase 6 (Polish): 10
Parallelizable tasks (marked [P]): 20

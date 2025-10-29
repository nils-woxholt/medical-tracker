# Implementation Plan: Lean Mode Referential Integrity (Feature 004)

**Branch**: `004-lean-mode-use` | **Date**: 2025-10-29 | **Spec**: `specs/004-lean-mode-use/spec.md`
**Input**: Feature specification from `/specs/004-lean-mode-use/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Introduce referential integrity for symptom and medication logging by replacing free-text duplication with canonical `SymptomType` and `Medication` entities. Enforce validated duration with hard 24h cap (confirmation for >12h) and dual severity/impact scales (numeric 1–10 + derived categorical labels). Provide CRUD for Symptom Types, integrate searchable dropdowns (client-side filtering ≤500 items), and ensure lean observability (creation + validation error logs). Accessibility baseline (keyboard navigation, ARIA roles) included.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI, SQLModel, Alembic, structlog, prometheus-client, passlib (existing), jose (auth), pydantic
**Storage**: PostgreSQL (prod), SQLite (test/dev) via SQLModel
**Testing**: pytest (unit/integration), contract tests (OpenAPI schema validation), Playwright (frontend e2e), Vitest/Jest (component), new data validation tests for duration/severity mapping
**Target Platform**: Backend Linux container / local dev Windows; Frontend Next.js (Node 18+)
**Project Type**: Web SaaS (separate backend + frontend folders)
**Performance Goals**: Dropdown filter response < 1s for ≤500 items; SymptomType CRUD endpoints p95 latency <200ms locally; validation CPU negligible (<1ms per request).
**Constraints**: 24h max duration enforced; confirmation required >12h; severity/impact numeric range 1–10; zero tolerance for orphaned logs after deactivation.
**Scale/Scope**: Initial adoption (single tenant multi-patient) with <5k symptom types and medications; logs volume moderate (<100k) fits PostgreSQL easily.

Additional Notes:

- Observability Lean Mode: log create/update/deactivate + validation errors; metrics deferred to Strict Mode.
- Accessibility: dropdown and form fields keyboard navigable; ARIA roles; severity labels human-friendly.
- Security: All new endpoints require authenticated user; role model unchanged; input validation ensures numeric bounds and presence of FK.
  
## Constitution Check

Status: PASS (Lean Mode) – All required affirmations addressed below. Will re-affirm post Phase 1 when data model + contracts finalized.

1. Accessibility: New pages/components (Symptom Type management, logging form enhancements) must meet existing bundle threshold (<200KB critical JS). Keyboard navigation + ARIA roles defined; no large lib additions planned.
2. OpenAPI: CRUD endpoints for `/symptom-types` and updated logging endpoints will have contracts drafted in Phase 1 (task scheduled). No implementation before contract commit.
**Test Strategy**:

- Unit: severity/impact mapping, duration validators.
- Integration: CRUD flow, log creation referencing FK.
- Contract: Schema diff vs generated OpenAPI.
- E2E: Playwright scenario create symptom type then log symptom referencing it.
- Coverage Goal: Maintain ≥85% statements for new backend modules; critical validators 100% branch.

**Observability**: Creation/update/deactivate events + validation errors logged with request id/user id. Metrics/traces deferred (Strict Mode backlog).
**Security**: Auth required; no new roles. Input validation ensures numeric bounds (1–10) and FK existence. Deactivation prevents new logs referencing inactive entity (to implement check).
**Complexity Tracking**: No violations; repository pattern not introduced; using existing models/services structure.
**Performance & Error Budgets**: New endpoints expected low latency; budgets unchanged. Error handling returns 422 for validation issues.

Deferred (Strict Mode Backlog): Detailed Prometheus metrics, distributed tracing spans for CRUD/list endpoints, server-side search for large lists.
Remediation Tasks (to schedule when activating Strict Mode): add FK active-state enforcement test; add per-endpoint Prometheus counters & latency histograms; implement server-side search if item count >500.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: Option 2 (Web application with separate `backend/` and `frontend/`). Existing repo already matches this; feature touches `backend/app/models`, `backend/app/api` (new or extended routers), and `frontend/src/components` & pages for forms/dropdowns.

## Complexity Tracking

### When Violations Exist

Fill ONLY if Constitution Check has violations that must be justified.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

## Phases

### Phase 0 (Complete)

- Research decisions documented (`research.md`): duration cap, severity/impact mapping, dropdown strategy, observability scope.
- Constitution check PASS in Lean Mode.

### Phase 1 (In Progress Next)

- Implement SQLModel entities & Alembic migration for `symptom_type`, modify/create `symptom_log` table.
- Add constraints & indexes per data-model.
- Backfill script stub (if legacy free-text exists) – may defer if no legacy data.
- OpenAPI contract committed (done) and validated against generated schema test.
- Add unit tests for mapping + duration validator.

### Phase 2

- Implement CRUD API routes for SymptomType; implement symptom logging & medication logging validators.
- Service-layer enforcement of inactive SymptomType/Medication blocking.
- Integration tests: create -> log -> deactivate -> attempt new log (expect 422/400).
- Contract tests: ensure responses conform.

### Phase 3

- Frontend components: Symptom Type management page, enhanced logging form with dropdowns & confirmation checkbox.
- Client-side filtering performance check (≤500 items <1s).
- Playwright e2e scenario covering long-duration confirmation.

### Phase 4

- Observability polish: structured log fields (entity_type, action, duration_bucket), prepare metrics backlog items (not implemented yet).
- Documentation: quickstart.md update, tasks.md finalize.
- Quality gate summary & readiness review.

### Phase 5 (Strict Mode Prep - Deferred)

- Prometheus counters + histograms, distributed tracing spans, server-side search for large datasets.

## Quality Gates Summary

Build/Lint: All markdown artifacts (spec.md, research.md, data-model.md, plan.md) pass lint after fixes.
Contracts: `contracts/feature-004.openapi.yaml` created; pending automated diff test post implementation.
Testing Plan: Unit (validators, mapping) + integration (CRUD + inactive enforcement) + e2e (long duration confirmation) defined.
Performance: Targets documented (<200ms p95 CRUD, <1s dropdown filter) with no conflicts.
Security: Auth required for all new endpoints; validation prevents orphaned references; deactivation enforcement planned.
Observability: Lean Mode logging events enumerated; metrics/tracing deferred to Strict Mode backlog.
Accessibility: Keyboard navigation + ARIA roles flagged; no large bundle increase expected.

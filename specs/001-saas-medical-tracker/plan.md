# Implementation Plan: SaaS Medical Tracker (Logs, Medication Master, Conditions & Doctors)

**Branch**: `001-saas-medical-tracker` | **Date**: 2025-10-16 | **Spec**: `spec.md` (same directory)
**Input**: Feature specification from `/specs/001-saas-medical-tracker/spec.md`

**Note**: Plan Phase - populating Summary & Technical Context (Phase 0). Constitution gates to be affirmed next.

## Summary

Implement initial vertical slice of a medical tracking SaaS enabling: (1) daily logging of medications and symptoms with landing page summaries & "feel vs yesterday" derivation, (2) CRUD & deactivate for medication master data, and (3) condition passport with doctor directory linkage. Frontend: Next.js (App Router) with shadcn/ui, responsive/mobile-first. Backend: FastAPI contract-first endpoints producing OpenAPI used to generate TypeScript client. Persistence: start with SQLite (file-based) for rapid iteration; abstract via SQLModel enabling seamless later migration to PostgreSQL. Authentication stub: initial simple session/JWT placeholder (local only) to enforce per-user isolation; OIDC integration deferred. Observability: structured logging + basic metrics (request count, latency histograms) and web vitals capture pipeline placeholder. Accessibility & performance budgets applied from constitution (Lighthouse ≥90, critical JS ≤200KB). No advanced analytics dashboards, notes/file uploads, or multi-patient admin yet.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend), Node 20 LTS  
**Primary Dependencies**: FastAPI, SQLModel (over SQLAlchemy Core), pydantic v2, uvicorn; Next.js (App Router), React 18, shadcn/ui, Tailwind CSS, openapi-typescript, Axios (or fetch wrapper)  
**Storage**: SQLite (file `app.db`) via SQLModel for Phase 0/1; migration path to PostgreSQL planned (Alembic migrations scaffolded early)  
**Testing**: pytest + httpx for API; coverage via pytest-cov. Frontend: Vitest + React Testing Library for components, Playwright for e2e P1 story (log medication & symptom); contract tests auto-generated from OpenAPI using Schemathesis (planned)  
**Target Platform**: Development on Windows/macOS; containerized runtime (Linux) target; Next.js server (Node) + FastAPI ASGI (uvicorn)  
**Project Type**: Web (separate frontend and backend directories; shared generated types)  
**Performance Goals**: API p95 ≤300ms (standard endpoints), landing page TTI ≤2s on mid‑tier mobile (throttled 4G, Moto G Power class)  
**Constraints**: Critical route JS bundle ≤200KB gzip; symptom + medication log list queries ≤50 rows default; severity computation O(n) per day where n logs/day (expected small <100)  
**Scale/Scope**: Pilot phase ≤500 users, daily logs per user ≤40 (meds+symptoms), total initial screens: landing, medication list+form, symptom list+form, condition passport, doctor list+form (≈6 primary views)  

## Constitution Check (Initial)

Status: PRELIMINARY (Phase 0). Will re-affirm after research & design artifacts.

| Gate | Assessment | Notes / Actions |
|------|------------|-----------------|
| 1. Accessibility budgets defined | PASS | Apply global layout + shadcn/ui; ensure forms keyboard navigable; Lighthouse ≥90 target documented; bundle budget noted (≤200KB). |
| 2. OpenAPI contract drafted pre-implementation | PARTIAL | Endpoints enumerated but OpenAPI YAML/JSON not yet authored. Action: create `contracts/openapi.yaml` in Phase 1 before coding services. |
| 3. Test strategy enumerated | PASS | Unit (pytest/Vitest), component (RTL), contract (schemathesis + generated TS types), e2e (Playwright for P1 logging flow), coverage thresholds backend 80% / frontend 70%. |
| 4. Observability additions listed | PARTIAL | Plan for structured logging & latency metrics; need concrete metric names + trace id propagation doc in `research.md`. |
| 5. Security impacts analyzed | PARTIAL | Basic per-user isolation via userId scoping; auth provider stub (JWT local). Need threat review for duplicate name normalization & input validation list. |
| 6. Complexity tracking needed? | PASS | No extra abstractions beyond minimal layers (API routers, models, service functions). |
| 7. Performance & error budgets unaffected | PASS | Budgets reiterated; expected low load; confirm after prototype profiling. |

Violations / Follow-ups: Items marked PARTIAL generate research tasks.

## Project Structure

Selected: Option 2 (Web application with separate frontend + backend) plus generated shared types.

```text
backend/
  app/
    api/            # FastAPI routers (med_logs, symptom_logs, medications, conditions, doctors, auth)
    core/           # config, logging setup, settings
    models/         # SQLModel entities
    services/       # business logic (feel_vs_yesterday, validation helpers)
    schemas/        # pydantic request/response models (mirrored in OpenAPI)
    telemetry/      # metrics & tracing utilities
  tests/
    unit/
    integration/
    contract/       # contract validation, schemathesis

frontend/
  src/
    app/            # Next.js App Router routes
      (landing)/
      medications/
      symptoms/
      passport/
      doctors/
    components/     # Shared UI components/forms
    lib/            # API client (generated types + lightweight wrapper)
    styles/
  tests/
    unit/           # component tests (Vitest + RTL)
    e2e/            # Playwright

contracts/
  openapi.yaml      # Source of truth for API (manually curated or extracted then curated)
  types/            # Generated TS client types (openapi-typescript output)

scripts/            # Helper scripts (codegen, lint, coverage)
```

**Structure Decision**: Adopt separated `backend/` + `frontend/` + `contracts/` scheme; removed unused single-project/mobile templates. Keeps abstractions minimal per Simplicity principle; telemetry isolated for observability.

## Complexity Tracking

### When Violations Exist

Fill ONLY if Constitution Check has violations that must be justified.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | N/A | N/A |

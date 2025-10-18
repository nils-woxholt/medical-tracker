<!--
Sync Impact Report
Version change: (none prior) → 1.0.0
Modified principles: (initial adoption)
Added sections: Core Principles; Platform & Stack Constraints; Development Workflow & Quality Gates; Governance
Removed sections: none
Templates requiring updates:
	.specify/templates/plan-template.md ✅ updated
	.specify/templates/spec-template.md ✅ updated
	.specify/templates/tasks-template.md ✅ updated
	.specify/templates/agent-file-template.md ⚠ pending (auto-generated content still placeholder driven; no conflicting references)
	.specify/templates/commands/* (directory not found – N/A)
Deferred TODOs: none
-->

# Full Stack Web Application Constitution

## Core Principles

### I. Accessibility & Performance First

All user-facing pages MUST meet minimum Core Web Vitals (LCP ≤ 2.5s, CLS ≤ 0.1, FID/INP good) and achieve Lighthouse scores ≥ 90 for Performance, Accessibility, and Best Practices before a feature exits its MVP story phase. Semantic HTML, ARIA only when necessary, keyboard navigation, and color contrast compliance (WCAG 2.1 AA) are mandatory. Performance budgets: each page bundle (Next.js route) ≤ 200KB gzipped critical JS (excluding lazy-loaded chunks); images MUST be optimized via Next.js Image component; blocking network requests minimized (≤ 3 critical path requests). Rationale: Ensures inclusive, fast baseline reduces retrofitting cost, improves SEO & conversion.

### II. Contract-First API & Shared Types

Every new backend capability starts with an OpenAPI contract (FastAPI auto docs acceptable once defined) and JSON schema definitions that generate/validate shared TypeScript client types. No backend implementation code merges without a reviewed contract. Breaking change detection is automated via contract diff in CI; unapproved breaking diffs block merge. Rationale: Stabilizes frontend-backend collaboration, prevents over-implementation, enables strong typing & mocks.

### III. Test-Driven Development & Layered Quality Gates

For each user story: write failing tests before implementation (component tests for UI via React Testing Library, API contract tests, and at least one e2e flow via Playwright for P1 stories). Minimum coverage thresholds: 80% statements for changed backend modules, 70% for frontend components in scope (quality over chasing 100%). Red → Green → Refactor cycle enforced; flakey tests are P0 to stabilize. Rationale: Enforces confidence, documents intent, and reduces integration defects.

### IV. Observability & Error Transparency

All API endpoints MUST include structured logging (request id, user/session id, latency, status) and expose metrics (latencies, error rates) via Prometheus-compatible endpoint. Frontend captures unhandled errors & performance metrics (web vitals) and emits to logging endpoint with PII scrubbing. Distributed tracing (trace id propagated via headers) required for cross-service calls. Rationale: Rapid diagnosis reduces MTTR and supports data-driven optimization.

### V. Security, Privacy & Simplicity

Security controls (authn via JWT/OIDC, role/permission checks, input validation using pydantic schemas) MUST exist before exposing endpoints publicly. Secrets are never committed; environment configuration via `.env` + secret store in deployment. Dependencies scanned weekly; critical vulnerabilities block release. Simplicity rule: Introduce abstraction (service layer, caching, queueing) only once a measurable need (latency, throughput, code duplication) is documented in the plan's Complexity Tracking table. Rationale: Protects user data & velocity; avoids architecture drift.

## Platform & Stack Constraints

Frontend: Next.js (App Router), TypeScript strict mode, shadcn/ui components, Tailwind CSS.
Backend: FastAPI (Python ≥3.11), uvicorn ASGI server, pydantic v2 for validation, SQLModel or
SQLAlchemy for persistence, Postgres as primary database. Package/build: pnpm (frontend), uv/poetry
or pip-tools (choose one per service; default: uv with requirements.lock). API auth via OIDC/JWT with
FastAPI dependencies. CORS locked to known origins. Infrastructure scripts MUST be idempotent.

Performance Budgets:

- API p95 latency ≤ 300ms for standard requests, ≤ 1000ms for heavy analytics endpoints.
- Error rate (5xx) < 0.5% rolling 7d.
- Cold start (first request after deploy) ≤ 2s.

Data & Schema:

- OpenAPI contract canonical; Type generation via `openapi-typescript` for client.
- DB migrations via Alembic; each migration linked to feature spec.

Deployment & Environments:

- Branch previews (frontend) auto-deployed; staging mirrors production config (minus scale).
- Feature flags for incomplete work—no dead code behind commented blocks.

## Development Workflow & Quality Gates

Pull Request Checklist (MUST all be affirmative):

1. Contract updated (if API change) & diff clean (no unapproved breaking changes).
2. Tests added & passing (unit, component; e2e for P1 stories) with coverage thresholds met.
3. Accessibility & performance budgets validated (attach Lighthouse JSON for affected pages).
4. Security scanning (dependencies + static analysis) passed; no new critical/high vulns.
5. Observability: new endpoints expose logs & metrics; trace propagation verified.
6. Complexity table updated if introducing new abstraction.
7. Changelog entry (or aggregation commit) for user-visible behavior.

CI Pipeline Stages (fail-fast):

- Lint & Type Check (ESLint strict, mypy optional if Python types enforced, ruff linting).
- Contract Diff & Schema Validation.
- Test (unit/component) → Integration/API → e2e (parallelizable groups).
- Build & Bundle Size Guard (fail if > budget).
- Security & License Scan.
- Deploy Preview (frontend) & ephemeral API env for QA.

Release Governance:

- Semantic versioning for the product: MAJOR (breaking public API / contract), MINOR (new feature, non-breaking), PATCH (bug/security fix, perf improvements without contract change).
- Database migrations backward compatible for at least one MINOR unless justified.

## Governance

Hierarchy: This Constitution overrides conflicting wiki/docs. Amendments follow: (1) Draft change
PR including rationale & version bump classification; (2) Review by at least one backend + one
frontend maintainer; (3) If MAJOR, require RFC with migration plan and 2-core maintainer approval.

Review & Enforcement: Each PR template MUST link to gates satisfied. A weekly compliance sweep
samples merged PRs—violations trigger retro action items. Breaking change attempts without process
are reverted. Complexity justifications older than 90 days are re-validated or simplified.

Versioning of Constitution: Semantic rules—MAJOR (principle removed/redefined incompatibly), MINOR
(new principle/section or materially expanded rule), PATCH (clarifications only). This adoption is
1.0.0 (initial baseline). Last Amended date updates on any change other than pure formatting.

Sunset & Exceptions: Temporary exceptions allowed only with an expiry date ≤ 30 days documented in
Complexity Tracking table + retro follow-up task id.

**Version**: 1.0.0 | **Ratified**: 2025-10-15 | **Last Amended**: 2025-10-15

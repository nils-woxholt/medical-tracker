<!--
Sync Impact Report
Version change: 1.0.0 → 1.1.0 (MINOR)
Modified principles: Accessibility & Performance; Contracts; Testing; Observability; Governance
Added sections: Operating Modes; Fast Track Exceptions; Lean Mode Checklist; Strict Mode Gates
Removed sections: none (restructured)
Templates requiring updates:
  .specify/templates/plan-template.md (validate Lean/Strict tags)
  .specify/templates/spec-template.md (add mode declaration) ⚠ pending
Deferred TODOs: none
-->

# Full Stack Web Application Constitution

## Core Principles

### Operating Modes

We operate in two modes:

- Lean Mode (default for new features / early iteration): prioritize shipping validated user value quickly with minimal but meaningful safeguards.
- Strict Mode (stabilization, pre-release, compliance-sensitive work): apply full quality, performance, accessibility, and contract rigor.

A feature switches to Strict Mode when tagged `stabilize:<feature>` or entering a release milestone.

### I. Accessibility & Performance (Lean → Strict)

Lean Mode:

- Use semantic HTML (landmarks, headings) and avoid obvious contrast issues.
- No hard budgets; avoid known anti-patterns (large blocking images, huge unoptimized libraries).
- Run Lighthouse ad hoc; fix egregious regressions.

Strict Mode:

- LCP ≤ 2.5s, CLS ≤ 0.1, good INP/FID.
- Lighthouse ≥ 90 (Performance, Accessibility, Best Practices).
- Route critical JS ≤ 200KB gzipped (excluding lazy chunks).
- ≤ 3 critical path blocking requests.

Rationale: Lean reduces friction early; Strict enforces sustainable excellence.

### II. Contracts & Types (Progressive Rigor)

Lean Mode:

- New endpoint must have a documented request/response shape (Pydantic schema or TypeScript interface) in code or a short comment block.
- Mark endpoints as "provisional" until reused by another feature or exposed publicly.

Strict Mode:

- OpenAPI contract updated & diff reviewed before merge.
- Shared types generated automatically (e.g. `openapi-typescript`) and consumed.

Rationale: Defers heavy ceremony until stability matters.

### III. Testing Strategy (Minimum First, Depth Later)

Lean Mode Minimum:

- At least one test covering changed logic (unit OR component).
- Critical flows (login, data creation) require a simple e2e smoke test.
- No coverage percentage enforcement; focus on value & correctness.

Strict Mode:

- Coverage thresholds: backend changed modules ≥ 80%, frontend in-scope components ≥ 70%.
- e2e path for primary user journeys.
- Red → Green → Refactor encouraged (not blocked by lack of refactor stage).

Flaky tests tracked; resolution prioritized during stabilization.

### IV. Observability & Errors (Progressive Enhancement)

Lean Mode:

- Structured error logging with request id (or generated UUID) & user/session if available.
- Central error boundary on frontend reporting basic info (scrub PII).

Strict Mode:

- Standard request logs (latency, status) + metrics (latency histograms, error rates).
- Distributed trace id propagation.
- Frontend web vitals emission.

### V. Security & Privacy (Non-Negotiable Baseline)

Always (both modes):

- Hashed passwords, validated input (Pydantic).
- Auth checks on protected endpoints.
- No secrets in code; use environment variables.
- Dependency audits weekly (blocking only for critical vulnerabilities in Strict Mode).

Optional Strict Additions:

- License scanning.
- Expanded permission model.

### VI. Simplicity & Incremental Abstraction

Introduce service layers, caching, queues, or complex patterns only after a brief justification (one paragraph) in the PR description referencing measurable pain (duplication, latency, throughput). Expiry: justification auto-expires after 60 days unless reconfirmed.

### Performance & Reliability Targets (Strict Mode Only)

- API p95 latency ≤ 300ms standard, ≤ 1000ms heavy analytics.
- 5xx error rate < 0.5% rolling 7d.
- Cold start ≤ 2s.

Lean Mode: monitor qualitatively; formal thresholds applied at stabilization.

### Data & Schema

- Lean: migrations tied to features; keep them reversible where easy.
- Strict: every migration references its spec ID and includes downgrade logic unless impossible.

### Deployment & Environments

Lean:

- Branch previews optional for minor UI tweaks.
- Feature flags encouraged for incomplete features.

Strict:

- Consistent staging environment mirroring production (scale aside).
- No dead code; remove behind flags once stable.

## Workflow & Quality Gates

### Lean Mode Pull Request Checklist (must all be affirmative or explicitly annotated)

1. Changed logic has at least one test OR marked trivial.
2. If API change: request/response shape documented.
3. No obvious security regression.
4. Changelog line if user-visible.
5. TODOs not left without an issue link (or intentionally scoped).

Optional (recommended): quick Lighthouse check if UI-heavy.

### Strict Mode Additional Gates

- OpenAPI diff clean (no unapproved breaking changes).
- Coverage thresholds met.
- Performance & accessibility budgets validated (attach Lighthouse JSON).
- Metrics/tracing for new endpoints.
- Dependency & license scan clean.
- Bundle size check (fail if over budget).

### CI Stages

Lean Mode (fail-fast):

1. Lint & Type Check.
2. Minimal Test Suite (unit/component + smoke e2e).
3. Build.

Strict Mode adds:

1. Contract Diff.
2. Full Test Matrix (unit → integration → e2e).
3. Bundle Size & Performance Budget.
4. Security & License Scan.
5. Preview Deploys.

### Fast Track Exceptions

For urgent changes:

- Label `fast-track` with expiry ≤ 14 days.
- Must not touch authentication, data persistence schema, or introduce new external dependencies without review.
- Auto review in daily sweep; unresolved items converted to stabilization tasks.

## Governance

Simplified:

- Lean PR: single maintainer review OR auto-merge after successful CI + next-day async review.
- Strict PR: at least one backend + one frontend reviewer.

Amendments:

- Minor (add/relax Lean guidance) require single maintainer approval.
- Major (removing Strict safeguards) require RFC + two maintainers.

Weekly Review:

- Sample merged Lean PRs for missed essentials (tests / security / shape docs).
- Retro tasks created for systemic gaps.

Versioning of Constitution:

- MAJOR: incompatible removal of a safeguard.
- MINOR: mode adjustments, new optional practices.
- PATCH: clarifications.

This revision is MINOR (introduces Lean/Strict mode and relaxes certain defaults).

Sunset & Exceptions:

- Exceptions tracked via label or a simple table in `docs/cleanup/` (optional).
- Auto-expire enforcement encourages follow-up.

**Version**: 1.1.0 | **Ratified**: 2025-10-15 | **Last Amended**: 2025-10-29

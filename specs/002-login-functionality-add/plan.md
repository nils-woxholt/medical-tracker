# Implementation Plan: User Authentication (Login & Registration)

**Branch**: `002-login-functionality-add` | **Date**: 2025-10-19 | **Spec**: `specs/002-login-functionality-add/spec.md`
**Input**: Feature specification from `/specs/002-login-functionality-add/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Introduce foundational user authentication enabling: email/password registration, login, logout, demo (ephemeral) access, session persistence with 30‑minute inactivity timeout, and brute force mitigation (lock after 5 failures for 15 minutes). Backend (FastAPI) exposes contract‑first endpoints; frontend (Next.js) consumes typed client generated from OpenAPI. Sessions implemented using an HTTP-only secure cookie carrying a signed JWT access token (rolling renewal on activity) plus refresh logic (longer-lived refresh token if adopted later). Demo access is via a preconfigured account - data is stored normally. Observability: structured logs + metrics for auth flows; security: enumeration-resistant errors, rate limiting, audit events.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend)  
**Primary Dependencies**: FastAPI, SQLModel/SQLAlchemy, passlib[bcrypt], python-jose[cryptography] (JWT), email-validator, Next.js 14 (App Router), React 18, Tailwind, openapi-typescript  
**Storage**: SQLite primary (users, sessions/lock metadata); demo sessions persisted
**Testing**: pytest + httpx (backend unit/integration), schemathesis (contract fuzz), vitest + RTL (frontend unit/component), Playwright (e2e P1 stories), contract tests (OpenAPI diff)  
**Target Platform**: Linux container deployment (dev + CI), browsers (modern evergreen)  
**Project Type**: Web application (separate backend & frontend projects)  
**Performance Goals**: Login & registration p95 server latency ≤ 300ms; session refresh p95 ≤ 150ms; bundle increase for auth UI ≤ +20KB gzipped critical path  
**Constraints**: 30‑min idle timeout; 5‑attempt lockout 15 min; password ≥8 chars w/ letter+number; cookies Secure, HttpOnly, SameSite=Lax  
**Scale/Scope**: Initial target ≤ 10k registered users, ≤ 100 concurrent logins/minute (sufficient for MVP); design keeps stateless scaling path (session store choices allow horizontal scaling)

**Open Questions / NEEDS CLARIFICATION**: NONE (spec clarifications resolved)

## Constitution Check

### Pre-Phase 0 Gate Assessment

| # | Requirement | Status | Notes |
|---|-------------|--------|-------|
| 1 | Accessibility & performance budgets | PASS | Bundle delta target & existing a11y score ≥90 defined; auth pages included. |
| 2 | Contract-first endpoints | PARTIAL | Contract draft to be produced in Phase 1 (planned). |
| 3 | Test strategy enumerated | PASS | Unit, component, contract, e2e (Playwright for P1) listed with coverage thresholds. |
| 4 | Observability additions listed | PASS | Structured logs + metrics + audit events enumerated. |
| 5 | Security impacts analyzed | PASS | Lockout, enumeration protection, idle timeout, cookie settings specified. |
| 6 | Complexity tracking prepared | PASS | No violations yet; table empty. |
| 7 | Performance/error budgets | PASS | p95 auth latency & error budget (<0.5% 5xx) aligned with constitution. |

Gate Result: PROCEED (Contract draft creation is an explicit Phase 1 action.)

## Constitution Gate Post-Design Re-Validation

All gates re-evaluated after drafting research, data model, contract, and quickstart. No regressions introduced.

| Gate | Delta Since Pre-Check | Final Status | Additional Notes |
|------|-----------------------|--------------|------------------|
| Clarity | No new ambiguities | PASS | Data model & state transitions reinforce requirements |
| Feasibility | Confirmed migrations & session strategy viable | PASS | No novel infrastructure required |
| Value | Unchanged | PASS | Proceed to task breakdown |
| Security | Threat review aligns; no new risks | PASS | CSRF note retained; future MFA flagged OOS |
| Observability | Metrics mapped to code touchpoints | PASS | Will add trace/span names during implementation |
| Contract | Stable draft | PASS | Ready for type generation & schemathesis |

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
backend/
├── app/
│   ├── api/
│   │   ├── auth/            # New auth router (login, register, logout, demo, session)
│   │   └── __init__.py
│   ├── models/              # User model (extend if not present), session/lock metadata if persisted
│   ├── services/            # Auth service (hashing, token issuance, lockout logic)
│   ├── core/                # Settings/security utilities (may host cookie & JWT helpers)
│   └── telemetry/
├── tests/
│   ├── unit/auth/           # Password hashing, lockout logic tests
│   ├── integration/auth/    # Endpoint tests (login/register/logout/demo/session)
│   ├── contract/            # OpenAPI diff & schema tests
│   └── e2e/ (optional backend-focused flows)

frontend/
├── src/
│   ├── app/(auth)/login/page.tsx        # Login page (App Router)
│   ├── app/(auth)/register/page.tsx     # Registration page
│   ├── components/auth/                 # Form components, demo banner
│   ├── lib/api/                         # Generated API client layer (OpenAPI types)
│   ├── lib/auth/                        # Session helper (current user fetch, redirect logic)
│   └── styles/
├── tests/
│   ├── unit/auth/                       # Form validation & helpers
│   ├── component/auth/                  # UI interactions (RTL)
│   └── e2e/                             # Playwright flows (login, register, lockout)
```

**Structure Decision**: Web application with clear separation. Backend adds `auth` API router & service layer; frontend adds dedicated App Router pages and shared typed client. Testing mirrored per layer.

## Complexity Tracking

Currently none. Table will be populated only if we introduce: distributed session store (e.g., Redis), advanced rate limiter infrastructure, or additional abstraction (e.g., repository pattern) beyond MVP scope.

| Violation | Why Needed | Simpler Alternative Rejected Because | Expiry |

|-----------|------------|--------------------------------------|--------|

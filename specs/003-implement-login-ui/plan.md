# Implementation Plan: Login UI & Conditional Access

**Branch**: `003-implement-login-ui` | **Date**: 2025-10-25 | **Spec**: `specs/003-implement-login-ui/spec.md`
**Input**: Feature specification from `specs/003-implement-login-ui/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Introduce a unified access screen (login + register) guarding protected routes, surface authenticated identity + logout in the dashboard top bar, enforce password strength (≥10 chars, ≥2 classes), prevent dashboard flash pre-auth, and provide generic errors to avoid enumeration. Auth uses HTTP-only SameSite secure cookie carrying a JWT; frontend derives state via identity endpoint without direct token access. Performance, accessibility, and regression success criteria (SC-001..SC-009) govern completion. Metrics and structured logs added for auth actions.

## Technical Context

**Language/Version**: Frontend: TypeScript (Next.js App Router, React 18); Backend: Python 3.11 (FastAPI)  
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy, passlib; Next.js, React, TailwindCSS, shadcn/ui, React Testing Library, Vitest, Playwright  
**Storage**: SQLite (dev) existing User & Session tables; no new persistent tables for AccessScreenState (ephemeral)  
**Testing**: Backend: pytest (unit/integration/contract); Frontend: Vitest (component/unit), Playwright (e2e P1 flows), axe accessibility scans  
**Target Platform**: Web browsers (desktop & mobile ≥320px width); backend server (Linux/Windows)  
**Project Type**: Dual web (frontend + backend)  
**Performance Goals**: SC-001 login ≤4s load→dashboard (90%); SC-002 registration ≤6s (95%); SC-006 error feedback ≤1s (95%)  
**Constraints**: Accessibility ≥90 (access screen & top bar); bundle delta ≤25KB gzipped; no dashboard flash pre-auth; duplicate submissions suppressed  
**Scale/Scope**: Slice covers login/register/logout UI integration + identity display; excludes MFA, password reset, broader profile editing.

## Constitution Check

Pre-Design Gate (Initial):

1. Accessibility budgets: Defined (≥90 score; LCP ≤2.5s unchanged; bundle delta target ≤25KB). PASS
2. OpenAPI contract: Existing auth endpoints present; feature delta `contracts/auth.yaml` prepared. PASS
3. Test strategy: Component + contract + e2e (login/register/logout) + regression (SC-009). PASS
4. Observability: Add metrics counters/histogram; structured auth action logs; trace propagation unchanged. PASS
5. Security: JWT via HTTP-only cookie; generic errors; password constraints; input validated. PASS
6. Complexity: No new architectural layers; table empty. PASS
7. Performance & error budgets: New goals align with constitution; no degradation expected. PASS

Post-Design Confirmation:
All endpoints & data model shapes codified in `data-model.md` and `contracts/auth.yaml`; no additional clarifications required. Metrics naming consistent with existing Prometheus exposition. No violations introduced.

### Remediation Tasks (tracked for implementation)

- Implement histogram `auth_action_duration_seconds` and counters `auth_attempts_total`, `auth_logout_total`.
- Ensure `/auth/me` endpoint returns display_name & masked identity.

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
│   ├── api/ (auth routers)
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/ (auth service, masking util)
│   └── telemetry/
├── alembic/
└── tests/

frontend/
├── src/
│   ├── app/ (access screen route, protected layout)
│   ├── components/ (LoginForm, RegisterForm, AuthToggle, TopBarIdentity, LogoutButton)
│   ├── lib/ (auth client, masking function)
│   └── styles/
└── tests/ (unit, e2e)

specs/003-implement-login-ui/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
```

**Structure Decision**: Maintain existing dual-project separation (Next.js frontend + FastAPI backend). Feature introduces new UI components and minor backend telemetry additions; no new project boundaries.

## Complexity Tracking

None

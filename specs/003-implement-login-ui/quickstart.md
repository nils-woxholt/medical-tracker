# Quickstart: Implement Login UI & Conditional Access

## Goal

Add unified access screen (login/register), identity display + logout to top bar, using HTTP-only cookie JWT for auth state, with performance, accessibility, and regression guarantees.

## Prerequisites

- Branch: `003-implement-login-ui`
- Contract delta: `specs/003-implement-login-ui/contracts/auth.yaml`
- Data model: `specs/003-implement-login-ui/data-model.md`

## Backend Steps

1. Add/verify auth routers align with contract (`/auth/login`, `/auth/register`, `/auth/logout`).
2. Ensure responses set HTTP-only, Secure, SameSite=Lax (or Strict if compatible) cookie with JWT.
3. Implement masking utility for email (server OR client) if display_name absent.
4. Add metrics (implemented):
   - Counter: `authentication_attempts_total{result,method}` (login attempts incl locked)
   - Counter: `auth_logout_total{result}`
   - Histogram: `auth_action_duration_seconds{action, result}` (buckets: 0.01..5.0)
   - Generic ops counter reused for registration: `operations_total{operation="registration",type="auth",status}`
5. Emit structured logs (implemented) fields:
   - `event`: `auth.login` | `auth.logout` | `auth.session.created` | `auth.lockout.trigger` | `auth.identity.lookup`
   - Common: `user_id`, `session_id`, `success`, `duration_ms`, optional `failure_reason`, `masked_identity`
6. Expose identity endpoint `/auth/me` (read masked identity & display_name).

## Frontend Steps

1. Create access screen route (e.g. `src/app/access/page.tsx`) with toggle between Login and Register modes.
2. Components:
   - `LoginForm.tsx` / `RegisterForm.tsx`
   - `AuthToggle.tsx` (buttons styled with accessibility: `aria-selected`)
   - `TopBarIdentity.tsx` (displays display_name or masked identity; tooltip on truncated)
   - `LogoutButton.tsx` (handles in-flight state)
3. Guard protected layouts: server component / client hook checks `/auth/me`; redirect to access screen without dashboard flash.
4. State management: local component state (AccessScreenState) + react-query/fetch for auth calls.
5. Prevent duplicate submissions: disable buttons while submitting; show spinner.
6. Mobile layout: vertical stacking, min touch targets ≥44px, no horizontal scroll at 320px.
7. Accessibility: focus first field on mode switch; link error messages via `aria-describedby`; ensure color contrast.

## Testing Strategy

- Unit/Component (Vitest): form validation, toggle, masking function.
- Contract Tests (pytest): endpoints adhere to schema (status codes, bodies, cookie set).
- E2E (Playwright): login success, registration success, invalid login, logout.
- Performance (synthetic): measure timing marks; ensure SC-001..SC-002.
- Accessibility: axe run on access screen & dashboard top bar → score ≥90.
- Regression (Polish phase): all suites pass; coverage not below baseline; no new accessibility violations.

## Observability Verification

- Check `/metrics` for samples of `auth_action_duration_seconds` and `auth_logout_total` after exercising flows.
- Confirm login attempts produce `authentication_attempts_total{result="success"|"failure"|"locked"}` increments.
- Verify logout success increments `auth_logout_total{result="success"}`; simulate failure paths if added.
- Structured logs include `event` field with names above; avoid leaking raw password or full email (masked when appropriate).
- Trace headers propagate through auth endpoints if tracing enabled.

## Error Messages (Client)

- Login fail: "Check your details and try again."
- Register conflict: "Could not complete registration." (generic)
- Network issue: "Connection issue. Try again; your data is still here."

## Masking Function (Reference)

```ts
export function maskEmail(email: string): string {
  const [local, domain] = email.split('@');
  if (!domain) return email;
  const visible = local.length >= 3 ? local.slice(0,3) : local;
  return `${visible}...@${domain}`;
}
```

## Metrics Naming Rationale

`authentication_attempts_total` retained for backward compatibility; new metrics prefixed with `auth_` keep domain grouping. `auth_action_duration_seconds` pairs action & result labels to keep cardinality low (4 actions * 2 results typical).

## Identity Endpoint Usage

Backend: `GET /auth/me` returns masked identity or 401 if no valid session.

Frontend example (using existing AuthClient):

```ts
import { authClient } from '@/lib/auth/client';

async function loadIdentity() {
   const identity = await authClient.getIdentity(); // returns { id, emailMasked, displayName } | null
   if (!identity) {
      // redirect to /access or show login screen
   } else {
      // render top bar identity
   }
}
```

Use a periodic revalidation (e.g. on focus) rather than aggressive polling.

## Rollout Checklist

- [ ] Contract delta reviewed & merged
- [ ] Backend endpoints implemented with cookie + masking
- [ ] Metrics visible & labeled
- [ ] Frontend forms and guard implemented
- [ ] Tests (unit, e2e) green & coverage thresholds met
- [ ] Accessibility audit ≥90
- [ ] Performance timings logged within SC thresholds
- [ ] Polish regression pass (SC-009)

## Risks & Mitigations

- Cookie SameSite incompatibility for future cross-site flows → can adjust to Lax early; revisit if needed.
- Masking confusion for short local parts → show full local if <3 chars then ellipsis.

## Next

Proceed to task breakdown (`tasks.md`) for implementation sequencing.

# Quickstart: User Authentication Feature

## Prerequisites

- Backend: Python 3.11, run with `uv run` inside `backend/`
- Frontend: Node 18+, run with `npm run dev` inside `frontend/`
- SQLite running (configure DATABASE_URL in backend environment)

## Backend Steps

1. Install new deps (already in pyproject): `uv run pip install -e .` (managed by uv add if new libs needed later).
2. Create auth router: `app/api/auth/*.py` implementing register, login, logout, session, demo endpoints.
3. Add models/fields to existing User model (failed_attempts, lock_until) & create migration (Alembic).
4. Implement password hashing (passlib bcrypt) and session service (create, fetch, touch, revoke, cleanup expired).
5. Add middleware for session cookie extraction and idle timeout enforcement.
6. Emit structured logs + metrics counters (authentication_attempts_total, session_status_checks_total, demo_session_creations_total, security_events_total).
7. Export OpenAPI and regenerate frontend types: from repo root `pwsh ./scripts/generate-types.ps1` (or npm script referencing openapi file).

## Frontend Steps

1. Generate API types: `npm run generate-types` (ensure backend running to refresh contract if pulling live or use committed YAML).
2. Implement pages: `/login`, `/register` under App Router with shared form components.
3. Add demo access button (calls /auth/demo then navigates to authenticated landing page).
4. Add session hook to fetch `/auth/session` and provide current user context; protect client routes by redirecting unauthenticated users.
5. Add lockout & generic error handling: show single generic error for invalid credentials or lock state (with optional countdown if desired later).
6. Accessibility pass: ensure focus trapping in any modal, inputs labeled, error messages aria-live polite.

## Testing Strategy

- Backend unit: hashing, lockout transitions, session expiry.
- Backend integration: full happy/negative paths for each endpoint.
- Contract: run schemathesis against /auth/* paths.
- Frontend component: form validation and error messaging.
- E2E (Playwright): register → login → logout; failed attempts leading to lock; demo access flow; session timeout simulation.

## Observability

- Metrics endpoint `/metrics` exposes auth & system counters.
- Audit log events (`audit_event`) include user/session correlation.
- Contract fuzz tests (`pytest -k contract`) validate schema resilience.

## Security Checklist

- Cookies: HttpOnly; env-based Secure + SameSite (Strict in production, Lax elsewhere)
- No user enumeration in error bodies (generic invalid credentials)
- Lockout enforced after threshold failures
- Password rules validated client + server side
- Rate limiting applied to login & demo endpoints (in-memory placeholder)
- CSRF token (double submit) to be added for non-XHR contexts (future hardening)

## Next Steps

After merging: run soak test for auth endpoints latency & error rate; monitor lockout & rate limit metrics.
Add Redis-backed rate limiter & persistent audit storage in next iteration.

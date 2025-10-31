# Project

## overview

This is a medical tracker service that allows users to log in and track their medical data over time. The service includes user authentication, data entry, and data visualization features.

## starter prompt

I'm building a SAAS medical tracker web-app - a one stop diary about my conditions, doctors, symptoms and medication.

### It must have

- landing page (summary last 5 medication logs, last 5 symptom logs, a 'how do you feel vs yesterday' better or worse),
- medication page (log medication taken; maintenance of medication meta: purpose, frequency, prescribing doctor, current or not),
- symptom page (symptom definition + logging),
- doctor page (name, related condition, phone, email, description),
- condition passport (diagnosed conditions),
- notes (tag a doctor or medication and upload a file), login multi-patient system.

### It must be

- easy to navigate,
- mobile friendly,
- visual with graphs and visuals to show progress.
- It must look sleek and trust-worthy.
- It must use a colloquial but sympathetic language tone.

## backend Service

This folder contains the backend service for our application.

- this is a python FastAPI project
- always run using `uv run`
- always test using `uv run pytest`
- DONT use `pip install` - ALWAYS use `uv add`
- when running ALEMBIC migrations use `uv run alembic`
- NOTE make sure that you are in the backend folder when running the command

### Backend technology

- python
- FastAPI
- SQLite
- Alembic (for migrations)
- passlib (for password hashing)
- pytest (for testing)
- UV (for running the app and managing dependencies)

## Frontend Service

- The Frontend is built with nextjs
- always run using 'npm run dev' command
- make sure that you are in the frontend folder by using the full path `cd C:\dev\lseg\spec-kit\todo\frontend` when running the command
- when running playwright tests, run them silently with `npx playwright test --quiet` to reduce noise in the output
- when running npm tests, run them silently with `npm test -- --silent` to reduce noise in the output

### Frontend technology

- nextjs
- React
- Typescript
- jest (for testing)
- Playwright (for e2e testing)
- styled using tailwindcss and shadcn/ui components

### spec-kit tasks

- when completing tasks, update the checklist in tasks.md to indicate that the task is complete

## Authentication (Exclusive Cookie Session Flow)

We now use ONLY an HTTP-only session cookie (`session`) for authentication. No JWT, Bearer tokens, or refresh/access token flows are documented or supported in the current phase. Any legacy token endpoints present in code are deprecated and should not be referenced in new work or tests.

### Active Endpoints

- `POST /auth/register` — Creates a user and sets the `session` cookie (opaque session ID). Accepts `email`, `password`, optional `display_name`, and optionally `first_name` / `last_name`.
- `POST /auth/login` — Authenticates and refreshes the `session` cookie; returns `{ data: { id, email, display_name? } }`.
- `GET /auth/me` — Resolves the current identity from the session cookie.

The versioned path `/api/v1/auth/register` intentionally returns 501 for contract compatibility; always use the root `/auth/register` and `/auth/login` for cookie issuance.

### Session Cookie Properties

- Name: `session` (HTTP-only; SameSite=Lax; Secure=false in dev/test — set Secure=true in production).
- Value: Opaque server-managed session ID (no embedded claims).
- Automatically sent by the browser; scripted tests capture `Set-Cookie` and inject manually.

### Testing Guidance

- Prefer API login flow: register/login → parse `session` cookie → inject into Playwright context before visiting protected routes.
- Fallback UI login: submit form at `/access?mode=login` using test IDs if cookie parsing becomes brittle.
- Never store auth state in `localStorage`; there is no token to persist.
- Assert authenticated state by waiting for UI markers (e.g. `log-forms-tabs`) rather than just URL changes.

### Implementation Notes

- Use password length ≥10 in tests (covers stricter validation).
- Name derivation rules: `first_name` from `display_name` or email local part; `last_name` fallback `User`.
- Protected endpoints must depend on the session-capable fallback (e.g. `get_current_user_id_or_session`). Avoid introducing token-only dependencies.

### Pitfalls & Remedies

- 401 on login: treat generically (invalid credentials). Do not leak which part failed.
- Missing authenticated content after login: verify `Set-Cookie` header (domain=`localhost`, path=`/`, name=`session`). Ensure REST client / Playwright added cookie.
- `/api/v1/auth/register` 501 is expected; do not “fix” by copying register logic there.

### Playwright Helper Example

```js
// Cookie-only auth helper
const reg = await request.post('/auth/register', { data: { email, password, display_name } });
const login = await request.post('/auth/login', { data: { email, password } });
const setCookieHeader = login.headers()['set-cookie'];
const sessionId = /session=([^;]+)/.exec(setCookieHeader)[1];
await context.addCookies([{ name: 'session', value: sessionId, domain: 'localhost', path: '/' }]);
// Now navigate to protected pages.
```

### Future Hardening (not yet implemented)

- Set `Secure=true` in production; evaluate `SameSite=Strict` or add CSRF tokens for unsafe cross-origin requests.
- Add logout endpoint invalidating server-side session.
- Introduce idle + absolute expiry (rolling renewal on activity).

### Medication Log Shim

Medication log endpoints accept only the session cookie; remove any outdated comments implying token usage when encountered.

## Database Table Naming Convention

All SQLModel ORM tables MUST declare an explicit `__tablename__` in snake_case:

- Example: `SymptomType` model -> `__tablename__ = "symptom_type"`
- Multi-word names use single underscores (`symptom_log`, `medication_log`).
- Do not rely on SQLModel's implicit auto name (e.g. `symptomtype`).
- Alembic migrations MUST use the same snake_case name; if a legacy table exists without underscore, create a migration to rename (`ALTER TABLE symptomtype RENAME TO symptom_type`).
- When adding models: choose snake_case, set `__tablename__`, run `uv run alembic revision --autogenerate -m "add <table>"`, then `uv run alembic upgrade head`.

Testing enforcement: a unit test (`test_tablename_convention.py`) asserts snake_case usage. Keep it updated as you add new models.

# Medical Tracker Backend

FastAPI backend for the SaaS Medical Tracker application.

## Features

- Daily medication and symptom logging
- Medication master data management
- Condition passport and doctor directory
- Feel vs yesterday computation
- Authentication (login, registration, session management)
- Structured logging and metrics

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (development) / PostgreSQL (production)
- **ORM**: SQLModel
- **Validation**: Pydantic v2
- **Migrations**: Alembic
- **Testing**: pytest + httpx
- **Linting**: Ruff + mypy

## Development Setup

1. **Python 3.11+ required**
1. **Install dependencies** (use uv only):

```bash
uv sync --extra dev
```

1. **Setup environment**:

```bash
cp ../.env.example .env
# Edit .env with your settings
```

1. **Initialize database**:

```bash
uv run alembic upgrade head
```

### Clean Initial Schema (Consolidated Migration)

For a brand new deployment with no existing data, you can start from the single
consolidated migration `20251031_160000_initial_consolidated.py` found in
`alembic/versions/`. This migration creates all required tables in one step:

```text
users, sessions, medications, conditions, doctors, doctor_condition_links,
symptom_type, symptom_log, audit_entry
```

To use the clean consolidated base instead of the historical chain:

1. Remove older migration version files (keep the consolidated one).
2. Ensure the `alembic_version` table is absent (drop database or delete file for SQLite).
3. Run:

```bash
uv run alembic upgrade head
```

If you already applied earlier migrations in an environment with data DO NOT
switch to the consolidated migration; keep the linear history to preserve
integrity.

### Legacy Migration Deprecation Strategy

The repository still contains historical Alembic revision files for traceability
and auditing, but they are now marked as **deprecated**. New deployments should
ignore these and rely solely on the consolidated migration
`20251031_160000_initial_consolidated.py`.

Why keep deprecated files?

- They document the evolution path prior to consolidation.
- They prevent accidental confusion if someone references an old commit.
- Tooling limitations prevented physical deletion inside the automation context.

How to fully prune them in your local clone (optional):

1. Backup your database if it contains data you care about.
1. Ensure the consolidated migration has not been modified locally.
1. Delete all files in `backend/alembic/versions/` EXCEPT the consolidated migration:

   - `20251031_160000_initial_consolidated.py`

1. Drop the existing database (for SQLite remove the `.db` file) OR truncate the `alembic_version` table.
1. Recreate schema:

```bash
uv run alembic upgrade head
```

Identifying deprecated files:

- They include banner comments indicating deprecation and often a `branch_labels` value containing `"deprecated"`.
- Do **not** add new features on top of deprecated revisions; create a new revision from head if you need post-initial changes.

Adding future migrations (post consolidation):

1. Make your model changes (ensure snake_case table naming).
1. Generate a revision:

```bash
uv run alembic revision --autogenerate -m "add <feature>"
```

1. Verify only the intended changes are present.
1. Upgrade:

```bash
uv run alembic upgrade head
```

1. Update tests & docs accordingly.

If you accidentally applied deprecated migrations after consolidation:

- Easiest fix for dev: drop the DB and re-run the consolidated migration.
- For persisted data: write a manual migration script to align schema; avoid mixing chains.

### Table Naming Convention

All SQLModel ORM models must define an explicit `__tablename__` in snake_case
(e.g. `symptom_log`, `audit_entry`). A test enforces this (`tests/unit/test_tablename_convention.py`).
When adding new tables:

1. Set `__tablename__` explicitly.
1. Use single underscores between words.
1. Create an Alembic revision with matching snake_case table name.
1. Run:

```bash
uv run alembic upgrade head
```

1. Update docs if introducing a new domain concept.

1. **Run server**:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API & Observability

- OpenAPI docs: <http://localhost:8000/docs> (non-production only)
- ReDoc: <http://localhost:8000/redoc>
- Metrics endpoint: <http://localhost:8000/metrics> (Prometheus format)
- Auth endpoints summary:
  - POST /auth/register
  - POST /auth/login
  - POST /auth/logout
  - GET /auth/session
  - POST /auth/demo (creates a temporary demo session)

### Lean Mode Cookie Auth & Test Log Endpoints

The minimal in-memory medication log test endpoints at `/api/v1/medications/logs/medications`
(defined within `app/api/v1/endpoints/medications.py`) now use the fallback dependency
`get_current_user_id_or_session`.

This means:

- A valid `session` cookie (issued by `/auth/login` or `/auth/register`) OR a legacy Bearer token
  will authorize access.
- Prior documentation stating they were unauthenticated is outdated; they now require user context
  consistent with the rest of the application.
- These endpoints are a temporary shim for integration/contract tests and store data only in
  process memory—do not rely on them for production behavior.

If you add new protected routes, prefer `get_current_user_id_or_session` so UI cookie flows work
without introducing parallel token-only code paths.

### Metrics Added (Auth)

| Metric | Labels | Description |
|--------|--------|-------------|
| authentication_attempts_total | result, method | Login attempts (success, failure, locked) |
| session_status_checks_total | valid | Session status endpoint hits |
| demo_session_creations_total | success | Demo session creation attempts |
| security_events_total | event_type, severity | Rate limit & security related events |

### Audit Events

Emitted via structured logging (`audit_event`):
`auth.login.success`, `auth.login.failure`, `auth.lockout.trigger`, `auth.register.success`, `auth.logout`, `auth.demo.start`

### Generate TypeScript client types

```powershell
pwsh ./scripts/generate-types.ps1
```

## Testing

```bash
# All tests
uv run pytest

# Coverage
uv run pytest --cov=app

# Specific file
uv run pytest tests/integration/auth/test_login.py

# Contract fuzzing (Schemathesis)
uv run pytest -k contract
```

## Code Quality

```bash
# Lint and format
uv run ruff check .
uv run ruff format .

# Type checking  
uv run mypy .

# Pre-commit hooks
uv run pre-commit run --all-files

## Rate Limiting

Basic in-memory rate limiting added to login & demo endpoints (non-production) to reduce abuse. Emits `security_events_total{event_type="rate_limit"}` on throttling. Replace with Redis-backed limiter for production.

## Session Cookie Hardening

Environment-aware defaults:
- Production: `Secure=True`, `SameSite=Strict`
- Non-production: `Secure=False`, `SameSite=Lax`

All cookies are `HttpOnly`.

## Expired Session UX

Frontend detects expired session client-side & prompts user (logout menu). Server enforces via middleware.
```

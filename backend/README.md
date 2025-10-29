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

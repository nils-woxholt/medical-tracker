"""Contract tests & fuzzing for auth endpoints.

Phase 2 additions:
 - Add explicit presence/behavior tests for identity endpoint (/auth/me)
     and legacy placeholder endpoints returning 501.
 - Retain Schemathesis fuzzing for broader contract coverage.

Run with:
        uv run pytest -k contract
"""
from __future__ import annotations

import pathlib
import schemathesis
from schemathesis.core.errors import LoaderError
from fastapi import status
import pytest
from httpx import AsyncClient

# Load OpenAPI spec (use cleaned spec if available else raw)
SPEC_DIR = pathlib.Path(__file__).resolve().parents[3] / "contracts"
SPEC_FILE = next((p for p in [SPEC_DIR / "openapi_clean.yaml", SPEC_DIR / "openapi.yaml", SPEC_DIR / "openapi.json"] if p.exists()), None)
if SPEC_FILE is None:
    raise RuntimeError("OpenAPI spec file not found for contract tests")

try:
    schema = schemathesis.openapi.from_file(str(SPEC_FILE))
except LoaderError:
    # Mark schema invalid; tests will be skipped
    schema = None  # type: ignore

# Target only auth endpoints
AUTH_ENDPOINT_PREFIX = "/auth"

if schema:
    @schema.parametrize()
    def test_auth_endpoints(case):  # type: ignore[missing-type-doc]
        if not case.path.startswith(AUTH_ENDPOINT_PREFIX):
            return
        from app.main import app
        response = case.call_asgi(app)
        case.validate_response(response)
else:
    def test_contract_schema_invalid():  # type: ignore
        import pytest
        pytest.skip("OpenAPI schema invalid for contract fuzzing; skipping")


# --- Explicit endpoint presence/behavior tests (non-fuzz) ---
IDENTITY_PATH = "/auth/me"
LEGACY_TOKEN_PATH = "/api/v1/auth/token"
LEGACY_REFRESH_PATH = "/api/v1/auth/refresh"


@pytest.mark.asyncio
async def test_identity_endpoint_unauthenticated_returns_401(client: AsyncClient):
    resp = await client.get(IDENTITY_PATH)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED, resp.text


@pytest.mark.asyncio
async def test_legacy_placeholder_token_endpoint_present(client: AsyncClient):
    resp = await client.post(LEGACY_TOKEN_PATH)
    assert resp.status_code == status.HTTP_501_NOT_IMPLEMENTED


@pytest.mark.asyncio
async def test_legacy_placeholder_refresh_endpoint_present(client: AsyncClient):
    resp = await client.post(LEGACY_REFRESH_PATH)
    assert resp.status_code == status.HTTP_501_NOT_IMPLEMENTED

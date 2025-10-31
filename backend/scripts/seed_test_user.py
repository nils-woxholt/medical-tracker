"""Seed a deterministic test user for local development & E2E.

Usage:
  uv run python scripts/seed_test_user.py --email demo@example.com --password DemoPass123! --display "Demo User"

If the user already exists the script prints a message and exits 0.
Requires backend running at http://localhost:8000.
"""
from __future__ import annotations

import argparse
import sys
import requests

DEFAULT_EMAIL = "demo@example.com"
DEFAULT_PASSWORD = "DemoPass123!"  # Meets length & complexity (>=10 chars, 3 classes)
DEFAULT_DISPLAY = "Demo User"
BASE_URL = "http://localhost:8000"


def register(email: str, password: str, display: str) -> int:
    payload = {"email": email, "password": password, "display_name": display}
    r = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=10)
    if r.status_code == 201:
        print(f"[seed] Created user {email}")
        return 0
    if r.status_code == 409:
        print(f"[seed] User {email} already exists (409)")
        return 0
    print(f"[seed] Unexpected status {r.status_code}: {r.text}", file=sys.stderr)
    return 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", default=DEFAULT_EMAIL)
    ap.add_argument("--password", default=DEFAULT_PASSWORD)
    ap.add_argument("--display", default=DEFAULT_DISPLAY)
    args = ap.parse_args(argv)
    return register(args.email, args.password, args.display)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
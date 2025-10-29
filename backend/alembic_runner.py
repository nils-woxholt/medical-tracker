"""Shim script to invoke Alembic with proper environment for tests.

Allows subprocess calls to use `python backend/alembic_runner.py upgrade head` instead of relying on a global 'alembic' executable.
"""
from __future__ import annotations
import os
import sys
from alembic.config import CommandLine


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    cl = CommandLine()

    # Inject DATABASE_URL override if present
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        os.environ["ALEMBIC_DATABASE_URL"] = db_url  # optional, if env.py chooses to read it

    # Execute Alembic command using CommandLine.main which parses and runs
    exit_code = cl.main(argv)
    return int(exit_code) if isinstance(exit_code, int) else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

"""List all tables in the SQLite database for migration verification.

Run:
    uv run python scripts/list_tables.py
"""
import sqlite3
import os
import json
from pathlib import Path

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

def extract_sqlite_path(db_url: str) -> str:
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    if db_url.startswith("sqlite://"):
        return db_url.replace("sqlite://", "")
    return db_url

db_path = extract_sqlite_path(DB_URL)
if not Path(db_path).exists():
    print(json.dumps({"error": f"Database file not found: {db_path}"}))
    raise SystemExit(1)

con = sqlite3.connect(db_path)
cur = con.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = sorted([r[0] for r in cur.fetchall()])
print(json.dumps({"tables": tables}))

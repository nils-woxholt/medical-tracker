"""Utility script to print `users` table columns for debugging migrations.

Run with:
    uv run python scripts/inspect_users_columns.py
"""

import sqlite3
import os
from pathlib import Path

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

def extract_sqlite_path(db_url: str) -> str:
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    if db_url.startswith("sqlite://"):
        return db_url.replace("sqlite://", "")
    # Fallback assume direct path
        
    return db_url

db_path = extract_sqlite_path(DB_URL)
if not Path(db_path).exists():
    print(f"Database file not found: {db_path}")
    raise SystemExit(1)

con = sqlite3.connect(db_path)
cols = [c[1] for c in con.execute("PRAGMA table_info(users)").fetchall()]
print("User columns:", cols)

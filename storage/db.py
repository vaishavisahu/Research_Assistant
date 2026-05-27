"""SQLite connection and schema for the research assistant."""
from __future__ import annotations

import sqlite3
from pathlib import Path

# storage/db.py -> project root is two levels up
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "research.db"


def get_connection() -> sqlite3.Connection:
    """Open DB; create data/ if missing. Row access by column name."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_url TEXT,
    title TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS paper_summaries (
    paper_id TEXT PRIMARY KEY,
    abstract TEXT,
    introduction TEXT,
    methods TEXT,
    results TEXT,
    discussion TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (paper_id) REFERENCES papers(id)
);
"""


def init_db() -> None:
    """Create tables if they do not exist."""
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database ready: {DB_PATH}")
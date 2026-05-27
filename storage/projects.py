"""CRUD for titled research projects."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from storage.db import PROJECT_ROOT, get_connection, init_db


def _project_uploads_dir(project_id: str) -> Path:
    path = PROJECT_ROOT / "data" / "projects" / project_id / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_project(title: str) -> dict:
    """
    Insert a new project row and create its on-disk folder.
    Returns dict with id, title, created_at.
    """
    init_db()
    project_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    title = title.strip()
    if not title:
        raise ValueError("Project title cannot be empty")

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO projects (id, title, created_at) VALUES (?, ?, ?)",
            (project_id, title, created_at),
        )
        conn.commit()
    finally:
        conn.close()

    _project_uploads_dir(project_id)
    return {"id": project_id, "title": title, "created_at": created_at}


def list_projects() -> list[dict]:
    """All projects, newest first."""
    init_db()
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, title, created_at FROM projects ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_project(project_id: str) -> dict | None:
    """One project by id, or None."""
    init_db()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, title, created_at FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
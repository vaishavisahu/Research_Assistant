"""Papers and IMRaD summaries per project."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from storage.db import get_connection, init_db
from storage.projects import get_project
from research.schemas import PaperSummary

#mary INSERT into papers + paper_summaries
def save_paper_with_summary(
    project_id: str,
    source_url: str,
    summary: PaperSummary,
) -> dict:
    """
    Insert one paper row + one paper_summaries row.
    Returns {paper_id, project_id, source_url, title}.
    """
    init_db()
    if get_project(project_id) is None:
        raise ValueError(f"Unknown project_id: {project_id}")

    paper_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    title = (summary.title or "").strip() or None

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO papers (id, project_id, source_url, title, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (paper_id, project_id, source_url, title, now),
        )
        conn.execute(
            """
            INSERT INTO paper_summaries
                (paper_id, abstract, introduction, methods, results, discussion, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paper_id,
                summary.abstract,
                summary.introduction,
                summary.methods,
                summary.results,
                summary.discussion,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "paper_id": paper_id,
        "project_id": project_id,
        "source_url": source_url,
        "title": title,
    }

#Read back all five sections of the summary
def get_summary(paper_id: str) -> dict | None:
    """Join papers + paper_summaries for one paper."""
    init_db()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT
                p.id AS paper_id,
                p.project_id,
                p.source_url,
                p.title,
                p.created_at,
                s.abstract,
                s.introduction,
                s.methods,
                s.results,
                s.discussion,
                s.updated_at
            FROM papers p
            JOIN paper_summaries s ON s.paper_id = p.id
            WHERE p.id = ?
            """,
            (paper_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

# All URLs/titles of papers in a project
def list_papers(project_id: str) -> list[dict]:
    """All papers in a project, newest first."""
    init_db()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, project_id, source_url, title, created_at
            FROM papers
            WHERE project_id = ?
            ORDER BY created_at DESC
            """,
            (project_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
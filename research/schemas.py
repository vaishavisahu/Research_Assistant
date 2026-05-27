"""Structured outputs for paper summaries."""
from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field

# Agent must return these 6 fields; Pydantic rejects bad shape
class PaperSummary(BaseModel):
    """Five IMRaD sections — matches paper_summaries columns."""

    title: str | None = Field(
        default=None,
        description="Paper title if identifiable from evidence; else null.",
    )
    abstract: str = Field(description="Abstract section as Markdown bullet list.")
    introduction: str = Field(description="Introduction section as Markdown bullet list.")
    methods: str = Field(description="Methods section as Markdown bullet list.")
    results: str = Field(description="Results section as Markdown bullet list; include Key numbers.")
    discussion: str = Field(
        description="Discussion section as Markdown bullet list; include References links at end."
    )

# News schema (for non-paper articles)
class NewsBrief(BaseModel):
    """Structured summary for a news/press article (not a scientific paper)."""

    title: str = Field(description="Headline/title of the article.")
    lede: str = Field(description="1–2 sentence lede summarizing the core news.")
    key_points: list[str] = Field(description="5–10 bullets of concrete key points.")
    key_numbers: list[str] = Field(
        default_factory=list,
        description="Every numeric fact from evidence (counts, %, years, durations).",
    )
    why_it_matters: list[str] = Field(description="3–6 bullets: implications / significance.")
    open_questions: list[str] = Field(
        default_factory=list,
        description="Optional bullets: what remains unknown or unverified from sources.",
    )
    sources: list[str] = Field(
        description="List of source URLs referenced (must include the original URL)."
    )


# Terminal display helper
def summary_to_markdown(summary: PaperSummary) -> str:
    """Pretty-print for terminal (same shape as before)."""
    title = summary.title or "Paper Summary"
    parts = [
        f"# {title}",
        "## Abstract",
        summary.abstract,
        "## Introduction",
        summary.introduction,
        "## Methods",
        summary.methods,
        "## Results",
        summary.results,
        "## Discussion",
        summary.discussion,
    ]
    return "\n\n".join(parts)


def news_to_markdown(brief: NewsBrief) -> str:
    parts = [
        f"# {brief.title}",
        "## Lede",
        brief.lede,
        "## Key points",
        "\n".join([f"- {p}" for p in brief.key_points]) or "- (none)",
        "## Key numbers",
        "\n".join([f"- {p}" for p in brief.key_numbers]) or "- (none in sources)",
        "## Why it matters",
        "\n".join([f"- {p}" for p in brief.why_it_matters]) or "- (none)",
    ]
    if brief.open_questions:
        parts.extend(
            [
                "## Open questions",
                "\n".join([f"- {p}" for p in brief.open_questions]),
            ]
        )
    parts.extend(
        [
            "## Sources",
            "\n".join([f"- {u}" for u in brief.sources]) or "- (none)",
        ]
    )
    return "\n\n".join(parts)


@dataclass
class SummarizeResult:
    """What run_summarize returns: DB-shaped summary plus optional original news brief."""

    summary: PaperSummary
    news_brief: NewsBrief | None
    is_news: bool
"""Manager, judge, and analyst agents (papers + news)."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from agents import Agent

from research.schemas import PaperSummary, NewsBrief
from research.tools import scrape_url, search_with_scrape

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str, **replacements: str) -> str:
    """Load a prompt file; replace {placeholders} for runtime context injection."""
    text = (PROMPTS_DIR / name).read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace(f"{{{key}}}", value)
    return text


def load_analyst_prompt() -> str:
    """Analyst system prompt + few-shot output example (context engineering: examples separate)."""
    base = load_prompt("analyst_system.md")
    example = PROMPTS_DIR / "examples" / "results_bullets.md"
    if example.exists():
        base += "\n\n---\n\n" + example.read_text(encoding="utf-8")
    return base


def load_manager_prompt() -> str:
    """Manager system prompt + few-shot workflow example."""
    base = load_prompt("manager_system.md", date=_date_context())
    example = PROMPTS_DIR / "examples" / "manager_workflow.md"
    if example.exists():
        base += "\n\n---\n\n" + example.read_text(encoding="utf-8")
    return base


def load_news_manager_prompt() -> str:
    base = load_prompt("news_manager_system.md", date=_date_context())
    return base


def load_news_analyst_prompt() -> str:
    base = load_prompt("news_analyst_system.md")
    example = PROMPTS_DIR / "examples" / "news_brief_olo.md"
    if example.exists():
        base += "\n\n---\n\n" + example.read_text(encoding="utf-8")
    return base


class Judgment(BaseModel):
    is_good_enough: bool = Field(
        description="True only when score >= 0.85 and evidence supports a full IMRaD summary."
    )
    score: float = Field(ge=0, le=1)
    reason: str
    missing_information: list[str] = Field(default_factory=list)


def _date_context() -> str:
    return datetime.now().strftime("%B %d, %Y")


judge_agent = Agent(
    name="Judge agent",
    model=MODEL,
    instructions=load_prompt("judge_system.md"),
    output_type=Judgment,
)

analyst_agent = Agent(
    name="Analyst agent",
    model=MODEL,
    instructions=load_analyst_prompt(),
    output_type=PaperSummary,
)

judge_tool = judge_agent.as_tool(
    tool_name="judge_evidence",
    tool_description=(
        "Quality gate: evaluate whether scrape/search evidence is sufficient for a full IMRaD "
        "summary. Call after every scrape or search. Returns score, reason, missing_information."
    ),
)

analyst_tool = analyst_agent.as_tool(
    tool_name="write_paper_summary",
    tool_description=(
        "Specialist writer: return PaperSummary with five string fields "
        "(abstract, introduction, methods, results, discussion). "
        "Each field is Markdown bullets. Call exactly once at the end."
    ),
)

manager_agent = Agent(
    name="Manager agent",
    model=MODEL,
    instructions=load_manager_prompt(),
    tools=[scrape_url, judge_tool, search_with_scrape, analyst_tool],
    output_type=PaperSummary,
)


# News agents (non-paper URLs)
news_analyst_agent = Agent(
    name="News analyst agent",
    model=MODEL,
    instructions=load_news_analyst_prompt(),
    output_type=NewsBrief,
)

news_analyst_tool = news_analyst_agent.as_tool(
    tool_name="write_news_brief",
    tool_description=(
        "Specialist writer: return NewsBrief (title, lede, key_points, key_numbers, "
        "why_it_matters, open_questions, sources). key_numbers must list every numeric "
        "fact from evidence. Call exactly once at the end."
    ),
)

judge_news_agent = Agent(
    name="Judge news agent",
    model=MODEL,
    instructions=load_prompt("judge_news_system.md"),
    output_type=Judgment,
)

judge_news_tool = judge_news_agent.as_tool(
    tool_name="judge_evidence",
    tool_description=(
        "Quality gate for news articles: is scrape sufficient for a factual NewsBrief? "
        "Call after scrape/search. Returns score and missing_information."
    ),
)

news_manager_agent = Agent(
    name="News manager agent",
    model=MODEL,
    instructions=load_news_manager_prompt(),
    tools=[scrape_url, judge_news_tool, search_with_scrape, news_analyst_tool],
    output_type=NewsBrief,
)
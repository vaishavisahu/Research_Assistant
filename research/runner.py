"""Run the multi-agent summarizer (papers + news)."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from agents import Runner, gen_trace_id, trace, flush_traces, custom_span

from research.agents import manager_agent, news_manager_agent, load_prompt
from research.schemas import PaperSummary, NewsBrief, SummarizeResult
from storage.papers import save_paper_with_summary
from storage.projects import get_project

load_dotenv()


def _require_openai_key() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to .env")


def is_news_url(url: str) -> bool:
    u = url.lower()
    if "/news/" in u or "berkeley.edu/news" in u:
        return True
    if "arxiv.org" in u or "pmc.ncbi.nlm.nih.gov" in u or "/doi/" in u:
        return False
    return False


def build_user_prompt(paper_url: str, project_id: str | None = None) -> str:
    if project_id:
        project = get_project(project_id)
        name = project["title"] if project else project_id
        project_context = f"Project: {name} (id: {project_id})."
    else:
        project_context = ""

    template = "run_news_user_template.md" if is_news_url(paper_url) else "run_user_template.md"
    return load_prompt(
        template,
        paper_url=paper_url,
        project_context=project_context,
    )


def news_to_paper_summary(brief: NewsBrief, original_url: str) -> PaperSummary:
    """Map NewsBrief into PaperSummary columns for SQLite + Lesson 6 memory."""
    intro_parts = list(brief.key_points)
    if brief.key_numbers:
        intro_parts.append("**Key numbers (from article):**")
        intro_parts.extend(brief.key_numbers)

    intro = "\n".join(f"- {p}" if not p.startswith("**") else p for p in intro_parts)
    why = "\n".join(f"- {p}" for p in brief.why_it_matters) or "- Not stated in provided sources."
    if brief.open_questions:
        why += "\n\n**Open questions**\n" + "\n".join(f"- {p}" for p in brief.open_questions)

    refs = [original_url] + [u for u in brief.sources if u != original_url]
    discussion = why + "\n\n**References**\n" + "\n".join(f"- {u}" for u in refs)

    results = (
        "\n".join(f"- {n}" for n in brief.key_numbers)
        if brief.key_numbers
        else "- (no numeric facts in sources)"
    )

    return PaperSummary(
        title=brief.title,
        abstract=f"- {brief.lede}",
        introduction=intro or "- Not stated in provided sources.",
        methods="- Not applicable (news article).",
        results=results,
        discussion=discussion,
    )


async def run_summarize(project_id: str, paper_url: str) -> SummarizeResult:
    """Summarize a URL and persist to SQLite."""
    _require_openai_key()
    if get_project(project_id) is None:
        raise ValueError(f"Unknown project_id: {project_id}")

    news = is_news_url(paper_url)
    trace_id = gen_trace_id()
    print("OpenAI trace:", f"https://platform.openai.com/logs/trace?trace_id={trace_id}")
    print("Project id:", project_id)
    print("Mode:", "news" if news else "paper")

    prompt = build_user_prompt(paper_url, project_id)
    agent = news_manager_agent if news else manager_agent

    with trace(workflow_name="summarize", trace_id=trace_id):
        with custom_span("manager.run", {"url": paper_url, "project_id": project_id, "news": news}):
            result = await Runner.run(agent, prompt, max_turns=25)

    final_output = result.final_output
    news_brief: NewsBrief | None = None

    if isinstance(final_output, NewsBrief):
        news_brief = final_output
        summary = news_to_paper_summary(news_brief, paper_url)
    else:
        summary = final_output

    saved = save_paper_with_summary(project_id, paper_url, summary)
    print("Saved paper_id:", saved["paper_id"])

    flush_traces()
    return SummarizeResult(summary=summary, news_brief=news_brief, is_news=news_brief is not None)


async def run_paper_url(paper_url: str, project_id: str | None = None) -> PaperSummary:
    if project_id:
        return (await run_summarize(project_id, paper_url)).summary
    _require_openai_key()
    trace_id = gen_trace_id()
    print("OpenAI trace:", f"https://platform.openai.com/logs/trace?trace_id={trace_id}")
    prompt = build_user_prompt(paper_url)
    agent = news_manager_agent if is_news_url(paper_url) else manager_agent
    with trace(workflow_name="summarize", trace_id=trace_id):
        result = await Runner.run(agent, prompt, max_turns=25)
    flush_traces()
    out = result.final_output
    if isinstance(out, NewsBrief):
        return news_to_paper_summary(out, paper_url)
    return out

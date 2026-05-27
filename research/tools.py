"""Olostep tools for the research agents."""
from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from olostep import Olostep
from agents import function_tool, custom_span

load_dotenv()

OLOSTEP_API_KEY = os.getenv("OLOSTEP_API_KEY")

# Context engineering: send article text, not huge JSON wrappers
SCRAPE_MAX_CHARS = 18_000
SEARCH_PREVIEW_CHARS = 2_500


class OlostepError(RuntimeError):
    """Raised when an Olostep SDK request fails."""


def require_olostep_key() -> str:
    if not OLOSTEP_API_KEY:
        raise OlostepError("OLOSTEP_API_KEY is not set. Add it to .env")
    return OLOSTEP_API_KEY


def get_olostep_client() -> Olostep:
    return Olostep(api_key=require_olostep_key())


def sdk_result_to_dict(result: Any) -> dict[str, Any]:
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "__dict__"):
        return {k: v for k, v in vars(result).items() if not k.startswith("_")}
    return {"value": str(result)}


def compact_json(data: Any, max_chars: int = 10000) -> str:
    text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... [truncated]"


def extract_markdown_from_scrape(data: dict[str, Any]) -> str:
    """Pull markdown body from Olostep scrape response."""
    if data.get("markdown_content"):
        return str(data["markdown_content"])
    nested = data.get("scrape")
    if isinstance(nested, dict) and nested.get("markdown_content"):
        return str(nested["markdown_content"])
    return ""


def is_blocked_content(text: str) -> bool:
    """Detect captcha / bot-check pages (common on PMC and some .gov sites)."""
    if len(text) > 1500:
        return False
    lower = text.lower()
    blocked_markers = (
        "captcha",
        "recaptcha",
        "checking your browser",
        "verificando seu navegador",
        "access denied",
        "please enable javascript",
    )
    return any(m in lower for m in blocked_markers)


def trim_article_markdown(md: str, max_chars: int = SCRAPE_MAX_CHARS) -> str:
    """
    Drop leading nav chrome when possible; keep the article body.
    Heuristic: start at first markdown H1 if it appears after nav junk.
    """
    if len(md) <= max_chars:
        return md

    # Prefer starting near first level-1 heading (skip tiny leading lines)
    match = re.search(r"\n# [^\n]+\n", md)
    if match and match.start() > 200:
        md = md[match.start() + 1 :]

    if len(md) <= max_chars:
        return md
    return md[:max_chars] + "\n\n... [truncated for context]"


def build_scrape_payload(url: str, raw: dict[str, Any]) -> dict[str, Any]:
    md = extract_markdown_from_scrape(raw)
    if is_blocked_content(md):
        return {
            "url": url,
            "status": "blocked_or_thin",
            "markdown_chars": len(md),
            "preview": md[:800],
            "hint": "Page may be captcha or paywall; try search_with_scrape.",
        }

    trimmed = trim_article_markdown(md)
    title = None
    meta = raw.get("page_metadata") or raw.get("metadata")
    if isinstance(meta, dict):
        title = meta.get("title")

    return {
        "url": url,
        "status": "ok",
        "title": title,
        "markdown_chars": len(md),
        "markdown_content": trimmed,
    }


@function_tool
async def scrape_url(url: str) -> str:
    """Fetch one URL and return trimmed article Markdown (not raw API JSON).

    Use when the user provided a specific URL (paper, news, journal page).
    Do NOT use for open-ended discovery — use search_with_scrape instead.
    Do NOT call twice on the same URL in one run.
    """
    try:
        with custom_span("olostep.scrape_url", {"url": url}):
            scrape = get_olostep_client().scrapes.create(
                url=url,
                formats=["markdown"],
            )
            raw = sdk_result_to_dict(scrape)
            payload = build_scrape_payload(url, raw)
            return compact_json(payload, max_chars=20_000)
    except Exception as exc:
        raise OlostepError(f"Olostep Scrape API failed: {exc}") from exc


@function_tool
async def search_with_scrape(query: str, limit: int = 3) -> str:
    """Search the public web and scrape top hits as Markdown previews.

    Use when scrape_url returned blocked/thin content OR judge_evidence score < 0.85.
    Query should be 3–8 words: headline + institution (e.g. "Berkeley olo color Oz").
    Do NOT use when scrape_url already returned a full article body.
    """
    scrape_options = {"formats": ["markdown"], "timeout": 25}
    try:
        with custom_span("olostep.search_with_scrape", {"query": query, "limit": limit}):
            search = get_olostep_client().searches.create(
                query=query,
                limit=limit,
                scrape_options=scrape_options,
            )
            data = sdk_result_to_dict(search)
            links = data.get("links", [])[:limit]
            rows = []
            for link in links:
                md = link.get("markdown_content") or ""
                if is_blocked_content(md):
                    preview = md[:400]
                else:
                    preview = trim_article_markdown(md, max_chars=SEARCH_PREVIEW_CHARS)
                rows.append({
                    "title": link.get("title") or "Untitled",
                    "url": link.get("url") or "",
                    "markdown_chars": len(md),
                    "markdown_preview": preview,
                })
            return compact_json({"query": query, "results": rows}, max_chars=12_000)
    except Exception as exc:
        raise OlostepError(f"Olostep Search with Scrape failed: {exc}") from exc

"""Summarize a URL (paper or news) and save to a project."""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.runner import run_summarize
from research.schemas import summary_to_markdown, news_to_markdown


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python scripts/run_paper.py <PROJECT_ID> <URL>")
        print("Example:")
        print("  python scripts/list_projects.py")
        print('  python scripts/run_paper.py <id> "https://arxiv.org/abs/1706.03762"')
        sys.exit(1)

    project_id = sys.argv[1]
    url = sys.argv[2]
    result = asyncio.run(run_summarize(project_id, url))

    print("\n" + "=" * 60)
    print("FINAL REPORT (also saved to DB)")
    print("=" * 60 + "\n")

    if result.news_brief:
        print(news_to_markdown(result.news_brief))
    else:
        print(summary_to_markdown(result.summary))


if __name__ == "__main__":
    main()

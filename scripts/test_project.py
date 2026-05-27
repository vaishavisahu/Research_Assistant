"""Lesson 2 smoke test: create and list a titled project."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storage.projects import create_project, list_projects


def main() -> None:
    created = create_project("CRISPR Gene Editing Review")
    print("Created project:")
    print(f"  id:    {created['id']}")
    print(f"  title: {created['title']}")

    print("\nAll projects:")
    for p in list_projects():
        print(f"  - {p['title']} ({p['id'][:8]}...)")


if __name__ == "__main__":
    main()
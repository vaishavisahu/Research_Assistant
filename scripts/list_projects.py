import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from storage.projects import list_projects

for p in list_projects():
    print(f"{p['title']}")
    print(f"  id: {p['id']}\n")
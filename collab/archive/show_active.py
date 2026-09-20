"""Print active Claude/Codex collaboration tasks from collab/STATUS.md.

For a complete session entrypoint, use read_collab.py.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "STATUS.md"


def main() -> None:
    text = STATUS.read_text(encoding="utf-8")
    active = _section(text, "## Active Queue")
    if not active.strip():
        print("No active tasks found.")
        return
    print(active.strip())


def _section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    next_heading = text.find("\n## ", start + len(heading))
    if next_heading < 0:
        return text[start + len(heading) :]
    return text[start + len(heading) : next_heading]


if __name__ == "__main__":
    main()

"""
Collab triage helper.
Run from repo root: python collab/tools/read_collab.py

Prints:
  1. Unresponded Codex notes (newer than latest Claude note)
  2. Claude-owned pending tasks from _state.yaml, sorted by priority
  3. Agent status
"""
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

COLLAB = Path(__file__).resolve().parent.parent
CLAUDE_NOTES = COLLAB / "claude_notes"
CODEX_NOTES = COLLAB / "codex_notes"
STATE_FILE = COLLAB / "_state.yaml"

DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_")


def note_date(path: Path) -> str:
    m = DATE_RE.match(path.name)
    return m.group(1) if m else "0000-00-00"


def latest_claude_mtime() -> float:
    files = [f for f in CLAUDE_NOTES.glob("*.md") if DATE_RE.match(f.name)]
    if not files:
        return 0.0
    return max(f.stat().st_mtime for f in files)


def latest_date(folder: Path) -> str:
    files = [f for f in folder.glob("*.md") if DATE_RE.match(f.name)]
    if not files:
        return "0000-00-00"
    return max(note_date(f) for f in files)


def unresponded_codex_notes() -> list[Path]:
    cutoff = latest_claude_mtime()
    files = [f for f in CODEX_NOTES.glob("*.md") if DATE_RE.match(f.name)]
    newer = [f for f in files if f.stat().st_mtime > cutoff]
    return sorted(newer, key=lambda f: f.stat().st_mtime)


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    with STATE_FILE.open() as fh:
        return yaml.safe_load(fh) or {}


def main():
    latest_claude = latest_date(CLAUDE_NOTES)
    unresponded = unresponded_codex_notes()

    print("=" * 60)
    print("COLLAB TRIAGE")
    print("=" * 60)

    print(f"\nLatest Claude note : {latest_claude}")

    print(f"\n── Unresponded Codex notes ({len(unresponded)}) ──")
    if unresponded:
        for f in unresponded:
            print(f"  {note_date(f)}  {f.name}")
        print(f"\n  → Open next: collab/codex_notes/{unresponded[-1].name}")
    else:
        print("  (none — Codex notes are fully responded)")

    state = load_state()

    print(f"\n── Claude-owned pending tasks ──")
    tasks = [t for t in state.get("pending_tasks", []) if t.get("owner") == "claude"]
    tasks.sort(key=lambda t: t.get("priority", 99))
    if tasks:
        for t in tasks:
            print(f"  [{t.get('priority', '?')}] {t['id']}")
            print(f"      {t.get('summary', '')[:100]}")
    else:
        print("  (no Claude-owned tasks in queue)")

    print(f"\n── Agent status ──")
    for agent, info in state.get("agents", {}).items():
        print(f"  {agent}: {info.get('status')}  last={info.get('last_activity')}  task={info.get('last_task_id')}")

    print()


if __name__ == "__main__":
    main()

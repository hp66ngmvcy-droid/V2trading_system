"""One-shot Claude/Codex collab entrypoint.

Run this when the user says: "read collab/".
It prints the minimum context needed to start work without reopening completed
notes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "STATUS.md"
STATE = ROOT / "_state.yaml"

PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}


@dataclass(frozen=True)
class Task:
    task_id: str
    priority: str
    ready: bool
    note: str


def main() -> None:
    status_text = _read(STATUS)
    state_text = _read(STATE)
    tasks = _pending_tasks(state_text)
    ready_tasks = sorted(
        [task for task in tasks if task.ready],
        key=lambda task: (PRIORITY_ORDER.get(task.priority, 99), task.task_id),
    )
    next_task = ready_tasks[0] if ready_tasks else None

    print("# Read Collab")
    print()
    print("Use this output as the session entrypoint. Do not reopen completed notes marked DONE + REVIEWED.")
    print()
    print("## Source Of Truth")
    print("- Machine state: collab/_state.yaml")
    print("- Human summary: collab/STATUS.md")
    print("- Completion history: collab/task_history.jsonl")
    print()
    print("## Next Task")
    if next_task is None:
        print("No ready task found. Ask Claude to create or unblock the next task.")
    else:
        print(f"- id: {next_task.task_id}")
        print(f"- priority: {next_task.priority.upper()}")
        print(f"- note: collab/{next_task.note}")
        print()
        print("Read only this task note, plus agent memory if needed:")
        print("- collab/agent_memory/codex/patterns.md")
        print("- collab/shared/system_constraints.md only if the task touches core architecture")
    print()
    print("## Active Queue")
    active = _section(status_text, "## Active Queue")
    print(active.strip() if active.strip() else "No active queue section found.")
    print()
    print("## Skip These Completed Tasks")
    completed = _section(status_text, "## Completed And Reviewed")
    print(completed.strip() if completed.strip() else "No completed section found.")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    next_heading = text.find("\n## ", start + len(heading))
    if next_heading < 0:
        return text[start + len(heading) :]
    return text[start + len(heading) : next_heading]


def _pending_tasks(text: str) -> list[Task]:
    tasks: list[Task] = []
    in_pending = False
    current: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if line == "pending_tasks:":
            in_pending = True
            continue
        if in_pending and line and not line.startswith(" ") and not line.startswith("-"):
            _append_task(tasks, current)
            break
        if not in_pending:
            continue
        stripped = line.strip()
        if stripped.startswith("- id:"):
            _append_task(tasks, current)
            current = {"id": stripped.split(":", 1)[1].strip()}
        elif ":" in stripped and current:
            key, value = stripped.split(":", 1)
            current[key.strip()] = value.strip().strip('"')
    else:
        _append_task(tasks, current)
    return tasks


def _append_task(tasks: list[Task], current: dict[str, str]) -> None:
    if not current:
        return
    tasks.append(
        Task(
            task_id=current.get("id", ""),
            priority=current.get("priority", "normal"),
            ready=current.get("ready", "false").lower() == "true",
            note=current.get("note", ""),
        )
    )


if __name__ == "__main__":
    main()

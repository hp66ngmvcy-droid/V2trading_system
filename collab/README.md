# Claude + Codex Collab

When the user says `read collab/`, do this:

```bash
python collab/tools/read_collab.py
```

Then open only the next task note printed by the helper.

Start here manually:

1. Read [STATUS.md](STATUS.md).
2. Skip anything marked `DONE` and `REVIEWED`.
3. Open only the active note you are about to work on.
4. When work is complete, write a concise completion note in `codex_notes/` and update `STATUS.md`, `_state.yaml`, and `task_history.jsonl`.

This folder is an agent handoff lane, not a scratchpad. Keep notes short, link to code paths, and preserve old notes as audit history.

## Folders

- `claude_notes/` — Claude task briefs and idea routing.
- `codex_notes/` — Codex completion notes, implementation summaries, and open questions.
- `shared/` — constraints and decisions both agents should know.
- `tools/` — small local helpers for maintaining the collab index.

## Token-Saving Rule

`_state.yaml` is the machine-readable source of truth. `STATUS.md` is the first-pass human summary. If a task is marked done and reviewed in either place, trust the summary and do not reread the full note unless a new task references it.

## Agent Shortcut

The phrase `read collab/` means:

1. Run `python collab/tools/read_collab.py`.
2. Read the one next task note it prints.
3. Skip completed notes.
4. Do the task if the user asked to continue, or report the next task if they only asked for status.

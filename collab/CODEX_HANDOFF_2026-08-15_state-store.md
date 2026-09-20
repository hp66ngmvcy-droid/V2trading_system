# Codex Handoff — 2026-08-15 — SQLite State Store

Claude has built `~/Dev/shared/tools/state_cli.py` (platform-wide, not V2-local)
and seeded `collab/state.db` with current strategy state. The script is shared
across all Dev projects — each project uses its own collab/state.db.
Your job is to wire it into the existing tooling and update the heal command.
Stop and confirm after each item.

---

## Item 1 — Update `.claude/commands/heal.md`

Replace the _state.yaml read/write steps with state_cli.py calls. Specifically:

**Step 1** (read system state): change
> Read `collab/_state.yaml`

to:
> Run `python3 ~/Dev/shared/tools/state_cli.py status` and read the output.

**Step 3** (create collab task notes for approved ideas): change the _state.yaml
`pending_tasks` append step to:
```
python3 ~/Dev/shared/tools/state_cli.py add-task <id> \
  --owner codex --priority <N> \
  --summary "<summary>" \
  --note "claude_notes/<file>" \
  --next-action "<action>"
```

**Step 4** (heal the queue): replace the _state.yaml consistency checks with:
```
python3 ~/Dev/shared/tools/state_cli.py generate-status
```
This regenerates STATUS.md from the DB. No manual yaml editing needed.

**Step 5** (report): add at the end:
```
python3 ~/Dev/shared/tools/state_cli.py generate-status
```

Do NOT delete `_state.yaml` — keep as historical record.

---

## Item 2 — Add `generate-status` call to any Codex completion flow

When Codex marks a task done, the pattern is now:

```bash
python3 ~/Dev/shared/tools/state_cli.py complete <task-id> --done-note "codex_notes/<file>"
python3 ~/Dev/shared/tools/state_cli.py generate-status
```

When Codex kills or parks a strategy:

```bash
python3 ~/Dev/shared/tools/state_cli.py strategy <name> KILLED --wf-pf <N> --reason "<reason>"
python3 ~/Dev/shared/tools/state_cli.py generate-status
```

Document this pattern in `collab/PROTOCOL.md` under a new section:
**"Agent State Commands"** — paste the two patterns above.

---

## Item 3 — Run tests

```bash
venv/bin/python3 -m pytest tests/ -q
```

Must stay at 405+. state_cli.py is stdlib-only (sqlite3, argparse, pathlib) — no
new dependencies, no test changes expected.

---

## Item 4 — Smoke test the CLI

Run these and confirm output looks correct:

```bash
python3 ~/Dev/shared/tools/state_cli.py status
python3 ~/Dev/shared/tools/state_cli.py generate-status
cat collab/STATUS.md | head -30
```

---

## Hard rules

- Paper mode only. No live trading.
- Do not modify scoring gates, approval gates, or strategy files.
- Do not install new packages (sqlite3 is stdlib).
- state.db must never be committed to git if a .gitignore entry is not present — check and add `collab/state.db` to `.gitignore` if missing.
- Do not delete `_state.yaml` or `task_history.jsonl` — archive only.

---

## What Claude already did

- Built `collab/state_cli.py` (SQLite CRUD + STATUS.md generator)
- Seeded `collab/state.db` with all 15 strategy states (9 ACTIVE, 3 KILLED, 1 PARKED, 2 RESEARCH)
- Verified `status` command output correct

Codex picks up from Item 1.

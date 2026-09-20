# Done: Agent Research Scout Planning Ticket
Date: 2026-07-30
Task: User-requested local planning ticket

Interpreting as: add a local V2 planning/build ticket for the Agent Research
Scout idea, capturing the key points, safety gates, costs, and build plan
without writing to Linear or using external services.

## What was built

- Added a local V2 ticket for `Agent Research Scout Skill`.
- Added the task to `collab/STATUS.md`.
- Added the task to `_state.yaml` as a pending task.

## Files changed

- `collab/claude_notes/2026-07-30_agent-research-scout-skill.md`
- `collab/STATUS.md`
- `collab/_state.yaml`
- `collab/codex_notes/2026-07-30_agent-research-scout-ticket_done.md`

## How to verify

```bash
test -f collab/claude_notes/2026-07-30_agent-research-scout-skill.md
rg -n "Agent Research Scout|agent-research-scout|paper-only" collab/STATUS.md collab/_state.yaml collab/claude_notes/2026-07-30_agent-research-scout-skill.md
```

## Open questions for Claude

- Decide whether this should stay as a manual skill only, or later become a CLI
  wrapper around existing Exa/manual-note research.

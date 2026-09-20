# Done: Cortex Learning Loop Planning Ticket
Date: 2026-07-30
Task: User-requested local planning ticket

Interpreting as: add the earlier Cortex/self-optimising learning idea into the
V2 build plan as a separate local ticket, with the hard rule that Cortex can
suggest learning but cannot automatically change trading rules, risk, MT5, live
trading, promotion, or capital allocation.

## What was built

- Added a local V2 ticket for `Cortex Learning Loop Skill`.
- Added the task to `collab/STATUS.md`.
- Added the task to `_state.yaml` as a pending task.

## Files changed

- `collab/claude_notes/2026-07-30_cortex-learning-loop-skill.md`
- `collab/STATUS.md`
- `collab/_state.yaml`
- `collab/codex_notes/2026-07-30_cortex-learning-loop-ticket_done.md`

## How to verify

```bash
test -f collab/claude_notes/2026-07-30_cortex-learning-loop-skill.md
rg -n "Cortex Learning Loop|must not update trading rules automatically|cortex-learning-loop" collab/STATUS.md collab/_state.yaml collab/claude_notes/2026-07-30_cortex-learning-loop-skill.md
```

## Open questions for Claude

- Decide whether the first implementation should stay as a manual skill only,
  or later add a small local candidate-rule log format.

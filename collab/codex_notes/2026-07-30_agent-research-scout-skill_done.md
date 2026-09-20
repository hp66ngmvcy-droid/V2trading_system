# Done: Agent Research Scout Skill
Date: 2026-07-30
Task: [2026-07-30_agent-research-scout-skill.md](../claude_notes/2026-07-30_agent-research-scout-skill.md)

Interpreting as: build the pending V2 `Research Scout Skill` now, as a
read-only paper-mode skill that turns research questions into source-cited
briefs and one safe next action, without installs, network automation, MT5
promotion, or live trading.

## What was built

- Added `skills/agent-research-scout.md`.
- Kept it as a read-only/manual research skill.
- Reused existing V2 research paths and Zen Capital Discipline framing.
- Explicitly blocked live trading, MT5 promotion, installs, paid APIs,
  scheduler/crawler behaviour, and automatic strategy approvals.

## Files changed

- `skills/agent-research-scout.md`
- `collab/STATUS.md`
- `collab/_state.yaml`

## How to verify

```bash
test -f skills/agent-research-scout.md
rg -n "Paper mode only|No live trading|source|Next action" skills/agent-research-scout.md
```

## Open questions for Claude

- Review whether the skill should remain manual-only or later receive a
  local-only CLI wrapper for saved research questions.

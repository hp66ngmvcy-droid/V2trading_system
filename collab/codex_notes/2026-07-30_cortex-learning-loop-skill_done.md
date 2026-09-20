# Done: Cortex Learning Loop Skill
Date: 2026-07-30
Task: [2026-07-30_cortex-learning-loop-skill.md](../claude_notes/2026-07-30_cortex-learning-loop-skill.md)

Interpreting as: add a local Cortex-style learning-loop skill across the main
system areas, so each area can learn from Greg corrections as human-reviewed
candidate rules, with no automatic updates to trading, publishing, finance,
personal data, or approval gates.

## What was built

- Added `skills/cortex-learning-loop.md` for V2 trading.
- Kept Cortex as candidate-rule learning only.
- Explicitly blocked automatic updates to trading rules, MT5, live trading,
  risk, capital allocation, scoring, and promotion gates.

## Files changed

- `skills/cortex-learning-loop.md`
- root shared registry and related area skills were updated as part of the
  cross-system request.

## How to verify

```bash
test -f skills/cortex-learning-loop.md
rg -n "must not update trading rules automatically|May update trading rules automatically: NO" skills/cortex-learning-loop.md
```

## Open questions for Claude

- Review whether this should stay documentation-only or later add a local
  candidate-rule log format.

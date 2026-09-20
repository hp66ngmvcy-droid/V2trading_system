# KILL Note — BAF_v1
Date: 2026-07-31
Author: Claude (council review)
Status: KILLED

## Strategy
Breakout and Fade — fade false breakouts above/below 4H rolling high/low.
File: `src/tar_system/strategies/baf_v1.py`

## Evidence
- WF PF=0.90 on 832 trades — confirmed losing on large, statistically meaningful sample
- 832 trades over ~2 years = ~1.5 trades/day; spread cost destruction at this frequency
- Gold 2024–2026 structure: persistent breakouts ($3,000→$4,300), NOT breakout failures
- RSI 40–60 entry filter = midrange entries = worst fade entry quality
- 1-bar confirmation lag = entering after initial momentum reversal = systematically late

## Verdict
KILL — confirmed losing system on large sample. High trade count means noise already averaged out.
Edge does not exist in current regime. Do not retune.

## Actions Taken
- Strategy file retained at `src/tar_system/strategies/baf_v1.py` (do not delete — code reference)
- Agent memory written: `collab/agent_memory/baf_v1_killed_2026-07-31.md`
- Idea note retired: council note `collab/claude_notes/2026-06-18_BAF_v1-breakout-and-fade.md`

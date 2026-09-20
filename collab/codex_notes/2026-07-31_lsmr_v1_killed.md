# KILL Note — LSMR_v1
Date: 2026-07-31
Author: Claude (council review)
Status: KILLED

## Strategy
London Session Mean Reversion — fade ATR spikes 07:00–09:00 UTC back to EMA.
File: `src/tar_system/strategies/lsmr_v1.py`

## Evidence
- WF PF=0.72 on 54 trades — below 1.0, system loses money
- Gold 2025–2026 regime: persistent uptrend (+$1,200 in 18 months)
- Trending markets punish mean reversion systematically
- RSI >70/<30 filter fires INTO trend in trending regime
- 07:00–09:00 UTC = highest news-risk window; frequent gap-extensions on macro

## Verdict
KILL — below PF 1.0 on sufficient trade count. Root cause is regime mismatch, not parameters.
Do not retune. Retuning cannot fix a structural regime problem.

## Actions Taken
- Strategy file retained at `src/tar_system/strategies/lsmr_v1.py` (do not delete — code reference)
- Agent memory written: `collab/agent_memory/lsmr_v1_killed_2026-07-31.md`
- Idea note retired: council note `collab/claude_notes/2026-06-18_LSMR_v1-london-session-mean-reversion.md`

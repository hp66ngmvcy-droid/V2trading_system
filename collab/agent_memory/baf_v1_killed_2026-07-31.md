# Agent Memory — BAF_v1 KILLED
Date: 2026-07-31
Status: KILLED
Strategy: baf_v1 — Breakout and Fade

## Outcome
WF PF=0.90, 832 trades. Killed by council review 2026-07-31.

## Root Cause
Gold 2024–2026 is a persistent breakout regime — breakouts extend, not fail.
High trade count (832) means result is statistically stable: the edge is not there in this regime.
Spread cost destruction at 1.5 trades/day on an already sub-1.0 PF strategy is compounding loss.

## Hard Rules
- Do not retune baf_v1
- Do not retest until market structure shifts (e.g., sustained sideways/ranging Gold)
- Strategy file kept at `src/tar_system/strategies/baf_v1.py` — code reference only

## Kill Note
`collab/codex_notes/2026-07-31_baf_v1_killed.md`

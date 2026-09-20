# Agent Memory — LSMR_v1 KILLED
Date: 2026-07-31
Status: KILLED
Strategy: lsmr_v1 — London Session Mean Reversion

## Outcome
WF PF=0.72, 54 trades. Killed by council review 2026-07-31.

## Root Cause
Regime mismatch. Gold trending regime (+$1,200 in 18 months) systematically punishes mean reversion.
London open (07:00–09:00 UTC) frequently extends on macro news — fading is the wrong direction.

## Hard Rules
- Do not retune lsmr_v1
- Do not retest until gold enters a confirmed ranging regime (ADX < 20 sustained)
- Strategy file kept at `src/tar_system/strategies/lsmr_v1.py` — code reference only

## Kill Note
`collab/codex_notes/2026-07-31_lsmr_v1_killed.md`

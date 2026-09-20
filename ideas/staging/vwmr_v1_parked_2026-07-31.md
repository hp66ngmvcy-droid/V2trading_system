# Staging — VWMR_v1
Date: 2026-07-31
Status: PARKED — insufficient trade count
Strategy: vwmr_v1 — Volatility-Weighted Mean Reversion

## Why Parked
Only 14 trades in full backtest — cannot gate or validate statistically.
In-sample PF=1.61 is above 1.40 target but sample is too small to trust.

## Retest Condition
When trade count reaches ≥ 30, run walk-forward and submit to scoring gate.
Do not retune before 30-trade threshold is met.

## What Stays
- Strategy file: `src/tar_system/strategies/vwmr_v1.py` — keep, do not modify
- Idea note: `collab/claude_notes/2026-06-18_VWMR_v1-volatility-weighted-mean-reversion.md`

## Potential
PF=1.61 in-sample + mean reversion logic valid in ranging regimes.
Gold's current range ($4,200–$4,400) may provide more signals over time.
ATR features already in pipeline — implementation cost near zero when trade count permits.

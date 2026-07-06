# Strategy Idea: LSMR_v1 — London Session Mean Reversion

**Date:** 2026-06-18
**Author:** Claude (multi-agent debate synthesis)
**Status:** READY

## Context

Gold (XAUUSD) current regime: volatile mean-reverting around $4,300 institutional floor.
Existing vol_filtered_momentum_v1 returned PF 1.08 — directional trend-follow is weak.
Multi-agent debate (Claude + OpenRouter Gemma) identified London open volatility spike
followed by mean reversion as the strongest exploitable pattern.

## Strategy Logic

**Name:** LSMR_v1 (London Session Mean Reversion)
**Timeframe:** M15
**Symbol:** XAUUSD

Entry (SELL):
- 07:00–09:00 UTC only (London open volatility window)
- Price spikes > 1.5× ATR above 20-bar EMA
- RSI > 70 (overbought on spike)
- Enter SHORT at spike high, stop above 2× ATR above EMA

Entry (BUY):
- Same session window
- Price drops > 1.5× ATR below 20-bar EMA
- RSI < 30
- Enter LONG at spike low, stop below 2× ATR below EMA

Exit:
- Take profit at EMA reversion (reward:risk ≥ 1.5)
- Hard time stop: 2 hours post-entry OR 10:00 UTC, whichever is earlier (debate: 11:00 UTC is too late, unreverted trades are losers)
- Only enter 07:00-07:45 UTC (debate: late London-open entries in macro-volatile regime have worse MR rates)

Parameters to sweep:
- `spike_multiplier`: [1.2, 1.5, 2.0]
- `rsi_extreme`: [65/35, 70/30, 75/25]
- `reward_risk`: [1.5, 2.0]
- `session_start_hour`: [7, 8]
- `session_end_hour`: [9, 10]

## Task

1. Build `src/tar_system/strategies/lsmr_v1.py` — mean reversion class with above params.
2. Build features: EMA-20 distance, RSI-14, ATR-14.
3. Run backtest on XAUUSD M15 — full available history.
4. Sweep parameters. Target: PF > 1.40, Sharpe > 1.0, trades >= 50.
5. If passes gates, run walk-forward validation.

```bash
venv/bin/python -m tar_system.cli run-backtest \
  --strategy lsmr_v1 --symbol XAUUSD --timeframe M15
```

## Success Criteria

- PF >= 1.40, Sharpe >= 1.0, DD <= 5%, trades >= 50
- Walk-forward stability > 50
- If passes: promote to code_candidates

## Rationale

Current regime ($4,200–$4,400 volatile consolidation) favours mean reversion over
trend-following. London open creates predictable volatility spikes that typically
revert within 2 hours as institutional orders are absorbed.

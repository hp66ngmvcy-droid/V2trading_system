# Strategy Idea: VWMR_v1 — Volatility-Weighted Mean Reversion

**Date:** 2026-06-18
**Author:** Claude (multi-agent debate synthesis)
**Status:** READY

## Context

Debate finding: vol_filtered_momentum_v1 PF 1.08 insufficient. Directional bias
failing. ATR spikes in current gold regime are mean-reverting, not trending.
VWMR_v1 sizes entries proportional to ATR spike magnitude — larger spike = larger
position (capped), targeting faster reversion.

## Strategy Logic

**Name:** VWMR_v1 (Volatility-Weighted Mean Reversion)
**Timeframe:** M15
**Symbol:** XAUUSD

Core logic:
- Compute rolling 50-bar ATR median (`atr_median_50`) — already in feature pipeline
- Spike ratio = current_ATR / atr_median_50
- Only trade when spike_ratio in [1.5, 4.0] — too low = no edge, too high = black swan
- Bollinger Band 20/2.0: price outside band triggers candidate entry
- Enter COUNTER to the spike direction (price above upper band → SELL)
- Stop: 1.0× current ATR beyond entry
- Take profit: return to 20-bar SMA (Bollinger midline)

Volatility-weighting:
- Base lot = 0.01 (fixed micro)
- Scale: 1.0× base below 2.0× spike_ratio, 1.2× at 2.0-2.5×, 1.0× above 2.5× (debate: invert sizing — highest spikes carry highest trend-continuation risk)
- Hard cap: 2× base regardless of spike_ratio

Parameters to sweep:
- `spike_ratio_floor`: [1.3, 1.5, 1.8]
- `spike_ratio_ceil`: [2.5, 2.8, 3.2]  # debate: cap at 2.8, above this trend-continuation risk dominates
- `bb_period`: [15, 20, 25]
- `bb_std`: [1.8, 2.0, 2.5]
- `stop_atr_mult`: [0.8, 1.0, 1.2]

## Task

1. Build `src/tar_system/strategies/vwmr_v1.py` using existing ATR features.
2. Add Bollinger Band computation (SMA + rolling std) — no new deps.
3. Backtest XAUUSD M15. Target: PF > 1.40, Sharpe > 1.0, trades >= 60.
4. Sweep params above.
5. If passes: walk-forward validation.

```bash
venv/bin/python -m tar_system.cli run-backtest \
  --strategy vwmr_v1 --symbol XAUUSD --timeframe M15
```

## Success Criteria

- PF >= 1.40, Sharpe >= 1.0, DD <= 5%, trades >= 60
- Walk-forward stability > 50
- spike_ratio_ceil must stay <= 5.0 (avoid overnight gaps)

## Rationale

Vol-weighted sizing exploits the fact that larger ATR spikes in a consolidating
market have statistically faster/larger reversion. Pure fixed-size mean reversion
misses this asymmetry. Bollinger Bands provide the operational entry trigger
without requiring regime detection (strategy is self-contained).

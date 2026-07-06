# Strategy Idea: BAF_v1 — Breakout and Fade

**Date:** 2026-06-18
**Author:** Claude (multi-agent debate synthesis)
**Status:** READY

## Context

Third strategy from multi-agent debate. Targets false breakouts above/below key
intraday levels. Gold at $4,300 has strong institutional floor — breakout attempts
above $4,350 resistance repeatedly fail. BAF_v1 fades these failures.

## Strategy Logic

**Name:** BAF_v1 (Breakout and Fade)
**Timeframe:** M15
**Symbol:** XAUUSD

Level detection:
- Rolling 4-hour high/low (16 bars on M15)
- "Breakout" = close > 4H high + 0.3× ATR (clean break above level)
- "False breakout" confirmation: next bar closes BACK below 4H high

Entry:
- SELL on false breakout above 4H high: entry = close of confirmation bar
- BUY on false breakdown below 4H low: entry = close of confirmation bar
- Only trade 07:00–19:00 UTC (liquid session)
- Stop: 1.5× ATR above/below breakout level
- Target: 4H high/low midpoint (50% retracement back into range)

Filters:
- RSI 40–60 at entry (not overbought/oversold entering fade)
- ATR between 0.4× and 2.5× ATR median (no extreme volatility)
- Breakout exhaustion: close-back bar must have ATR < 0.85× 5-bar mean ATR (debate: confirms exhaustion not structure change)
- Do not trade within 30 min of major news (if `event_flag` available)

Parameters to sweep:
- `breakout_atr_mult`: [0.2, 0.3, 0.5]
- `lookback_bars_4h`: [12, 16, 20]
- `stop_atr_mult`: [1.2, 1.5, 2.0]
- `rsi_band`: [(35,65), (40,60), (45,55)]
- `session_hours`: [(7,19), (8,18), (7,17)]

## Task

1. Build `src/tar_system/strategies/baf_v1.py`.
2. Features needed: rolling N-bar high/low (simple pandas rolling — no new deps), RSI-14, ATR-14.
3. Backtest XAUUSD M15. Target: PF > 1.40, Sharpe > 1.0, trades >= 40.
4. Sweep params above.
5. If passes: walk-forward.

```bash
venv/bin/python -m tar_system.cli run-backtest \
  --strategy baf_v1 --symbol XAUUSD --timeframe M15
```

## Success Criteria

- PF >= 1.40, Sharpe >= 1.0, DD <= 5%, trades >= 40
- Walk-forward stability > 50
- False breakout confirmation bar must close below breakout level (strict)

## Rationale

False breakouts are a well-documented phenomenon near institutional price levels.
Gold's $4,300 floor creates predictable rejection patterns. This strategy requires
a two-bar confirmation to avoid entering on genuine breakouts, limiting whipsaw
risk. The fade entry (not the breakout entry) is the edge.

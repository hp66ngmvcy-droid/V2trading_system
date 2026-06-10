# Research: gold_v2 XAUUSD M15 + M30 Param Sweep — Close MT5 Gap

**Date:** 2026-06-04
**Author:** Claude
**Status:** READY

## Context

`gold_v2` on XAUUSD M15 and M30 both land at the same gap after full Stage 1-3
tuning:

| TF | Sharpe | PF | DD | Trades | Gap |
|----|--------|----|----|--------|-----|
| M5 | 2.25 | 1.36 | 0.19% | 87 | ✅ MT5 ready |
| M15 | 0.95 | 1.14 | 0.62% | 652 | PF +0.06, Sharpe +0.55 needed |
| M30 | 0.94 | 1.14 | 0.81% | 698 | PF +0.06, Sharpe +0.55 needed |

M15 best session: 8-17 UTC, ATR cap 11.73.
M30 best session: 7-16 UTC, ATR cap 10.15.

Both have good trade counts and low DD. The gap is quality-of-signal, not
frequency. M5 passes — same strategy, tighter timeframe, fewer but better
trades (87 vs 652).

## Task

Sweep signal quality parameters on `gold_v2` to reduce low-confidence entries:

1. Check `src/tar_system/strategies/gold_v2.py` — list all tunable params.
2. Identify params that control entry strictness (e.g. min signal strength,
   confirmation bars, RSI filter, ATR floor multiplier).
3. Sweep those params on M15 first, keep ATR cap=11.73, session=8-17.
4. Target: costed PF > 1.20, Sharpe > 1.50, trades >= 30.
5. If M15 finds a passing config, test same params on M30.

```bash
venv/bin/python -m tar_system.cli tune-strategy \
  --strategy gold_v2 --symbol XAUUSD --timeframe M15 \
  --params <swept_params>
```

## Success Criteria

- MT5 gates: Sharpe >= 1.5, PF >= 1.2, DD <= 5%, trades >= 30
- If passes: promote to `ideas/code_candidates/` and write walk-forward note

## Notes

- M5 passes with 87 trades (~1/day). M15 has 652 (~0.5/day). Tighter signal
  filter should reduce trades and improve quality — same direction as M5.
- Do not change ATR cap or session window — those are already optimised.
- If no param combo clears gates at M15, mark both M15 and M30 as KILL.

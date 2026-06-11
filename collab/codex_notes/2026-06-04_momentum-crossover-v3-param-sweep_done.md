# Done: momentum_crossover_v3 XAUUSD M15 Param Sweep

**Date:** 2026-06-11
**Author:** Claude
**Status:** DONE

## Result: KILL

### Sweep Summary

| Params | Trades | Raw PF | Costed PF | Sharpe | Verdict |
|--------|--------|--------|-----------|--------|---------|
| defaults | 12,605 | 0.9403 | 0.9939 | -0.03 | FAIL |
| min_hold_bars=5 | 8,149 | 0.9602 | 1.0006 | -0.04 | FAIL |

### Analysis

`min_hold_bars=5` cut trades from 12,605 → 8,149 (-35%) and Stage 1 costed PF
barely crossed 1.0 (1.0006). However:
- Session filter (Stage 3) found no window that improves results — all hours
- Final costed PF after session: 0.9943 < 1.2 gate
- Sharpe -0.04: no edge
- Still ~5.5 trades/day on M15 — overtrading persists

The strategy's core problem is low win rate (33%) with insufficient R:R to
compensate. No parameter axis fixes this without killing trade count.

### Decision

KILL `momentum_crossover_v3` on XAUUSD M15. Not viable at any min_hold_bars.

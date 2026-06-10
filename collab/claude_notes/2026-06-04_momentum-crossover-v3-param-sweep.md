# Research: momentum_crossover_v3 XAUUSD M15 Targeted Param Sweep

**Date:** 2026-06-04
**Author:** Claude
**Status:** READY

## Context

Full strategy sweep on XAUUSD M15 (2026-06-04) found `momentum_crossover_v3`
closest to breakeven of all failing strategies:

| Strategy | Raw PF | Costed PF | Sharpe | Trades |
|----------|--------|-----------|--------|--------|
| momentum_crossover_v3 | 0.9403 | 0.9939 | -0.03 | 12,605 |

Raw PF 0.94 — strategy has edge before costs but loses it to spread. High trade
count (12k) means even small per-trade improvements compound fast.

All other XAUUSD M15 failures had raw PF < 0.94 — not worth sweeping.

## Task

Run a targeted param sweep on `momentum_crossover_v3` XAUUSD M15 to find a
configuration that clears Stage 1 (costed PF > 1.0).

Axes to sweep:
1. **Entry threshold** — tighten signal filter to reduce low-quality trades
2. **Reward:risk ratio** — increase from default to raise per-trade expectancy
3. **Min hold bars** — skip signals too close together (reduce overtrading)

If any combination achieves costed PF > 1.0, run the full Stage 1-3 tuner:
```bash
venv/bin/python -m tar_system.cli tune-strategy \
  --strategy momentum_crossover_v3 --symbol XAUUSD --timeframe M15 \
  --params <best_params>
```

## Success Criteria

- Stage 1 costed PF > 1.0
- Total trades >= 30 (avoid over-filtering)
- If Stage 1 passes, full MT5 gate check: Sharpe >= 1.5, PF >= 1.2, DD <= 5%

## Notes

- 12,605 trades on M15 = ~8.5 trades/day. Likely overtrading. Reducing trade
  frequency is the primary lever.
- Check `src/tar_system/strategies/momentum_crossover_v3.py` for available
  params before designing sweep.
- If param sweep yields < 30 trades after filtering, mark KILL — not viable.

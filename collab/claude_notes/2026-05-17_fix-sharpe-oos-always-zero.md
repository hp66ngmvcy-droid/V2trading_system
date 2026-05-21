# Fix: sharpe_oos Always 0.0 — KEEP Still Unreachable

**Date:** 2026-05-17  
**Author:** Claude  
**Status:** DONE

## Bug

`stitch_metrics()` in `validation/walk_forward.py` computed total_trades, win_rate,
profit_factor, max_drawdown, expectancy, average_win, average_loss, trade_returns, trade_pnls —
but **never computed `sharpe_ratio`**.

`_merge_walk_forward_metrics()` in `continuous_parameter_search.py` reads:
```python
combined["sharpe_oos"] = float(stitched.get("sharpe_ratio", 0.0) or 0.0)
```

Because the key was absent, `sharpe_oos` was always `0.0`.

`run_gates()` with `require_oos=True` then evaluated `0.0 < min_oos_sharpe (1.0)` →
soft fail `SEARCH_OOS_SHARPE_NOT_MET` → REVIEW on every candidate.

**Effect:** Even after the bootstrap CI fix, KEEP remained unreachable. Every
candidate with valid OOS walk-forward results was still blocked by a spurious
OOS Sharpe failure.

## Fix

Added `_sharpe(returns)` helper to `walk_forward.py` (same formula as
`backtest/metrics.py`). Added `"sharpe_ratio": _sharpe(trade_returns)` to the
`stitch_metrics` return dict. The combined trade returns across all OOS splits
are used to compute the stitched Sharpe.

## Tests

3 regression tests added to `test_optimisation_layer.py`:
- `test_stitch_metrics_includes_sharpe_ratio` — positive returns → positive Sharpe
- `test_stitch_metrics_sharpe_zero_for_empty` — empty input → 0.0
- `test_merge_walk_forward_uses_stitched_sharpe` — stitched Sharpe > 0 for good returns

Full suite: **232 passed**.

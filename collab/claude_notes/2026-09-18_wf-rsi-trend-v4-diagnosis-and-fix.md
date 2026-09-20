---
id: WF-RSI-TREND-V4-FIX-2026-09-18
type: diagnostic
status: DONE
entity: rsi_trend_v4 XAUUSD M15
logged: 2026-09-18
---

# Walk-forward REVIEW diagnosis — rsi_trend_v4 XAUUSD M15

## Background

Best strategy from sweep: rsi_trend_v4 RSI 38/62, ATR 2.0.
Reported: PF=1.090, DD=0.00214, score=71.64, WF verdict=REVIEW.
Open issue: "Investigate why WF verdict stays REVIEW — check window_count and bootstrap CI."

## Root Causes Found (3 issues)

### Issue 1 — Feature store was M1 data mislabelled as M15

`data/features/XAUUSD_M15.parquet` contained 103,053 M1 bars (1-minute bars),
not M15. Source was `data/raw/XAUUSD_M15_merged.csv` which is a tab-delimited
M1 file starting 2026-02-11.

Effect: with default train=200/test=50, the walk-forward produced 2003
micro-windows of 50-minute test periods. Average 0.14 trades per window. Total
274 OOS trades but spread across 2003 windows. The stitch PF bug (see below)
then collapsed to PF=0.23.

Fix: re-imported `data/raw/XAUUSD_M15.csv` (27,591 true M15 bars,
May 2025 – Jul 2026) and rebuilt features. Verified bar interval = 15 min.

### Issue 2 — stitch_metrics computed PF as simple average of per-window PF values

`stitch_metrics()` in `src/tar_system/validation/walk_forward.py` computed:
  `profit_factor = sum(per_window_PF) / n_windows`

When most windows have zero trades (PF=0.0), this average collapses toward 0.
With 2003 windows and 274 trades, stitched PF was 0.23 even though true pooled
PF from trade_returns was 1.079.

Fix: added `_profit_factor_from_returns()` helper that computes PF from pooled
trade_returns: `sum(r>0) / abs(sum(r<0))`. Called by `stitch_metrics()` instead
of the window average. 445/445 tests pass.

File changed: `src/tar_system/validation/walk_forward.py`

### Issue 3 — rsi_trend_v4 not registered in strategy registry

`get_strategy("rsi_trend_v4")` raised KeyError — the strategy was never added
to `REGISTRY` in `src/tar_system/strategies/registry.py`.

Fix: added import of `RSITrendV4` and entry `"rsi_trend_v4": RSITrendV4` to
REGISTRY. No variant overrides needed — defaults match the best-sweep params.

## Walk-forward Results After Fix

Command:
```
PYTHONPATH=src python3 -m tar_system.cli run-walk-forward \
  --strategy rsi_trend_v4 --symbol XAUUSD --timeframe M15 \
  --train-window 4000 --test-window 2000
```

| Metric | Before | After |
|--------|--------|-------|
| window_count | 2003 | 11 |
| stitched PF | 0.23 | 1.44 |
| OOS trades | 274 (across M1 noise) | 67 |
| max_drawdown | 0.00108 | 0.00543 |
| sharpe OOS | — | 1.98 |
| wf_verdict | REVIEW | REVIEW |
| wf_reason | PF 0.23 < 1.10 | stability 0.0 < 50 |

Window sizes chosen: train=4000, test=2000 bars.
Reasoning: 86 trades in 27591 bars = 1 trade per ~320 bars.
11 windows × (2000/320) ≈ 69 OOS trades — comfortably clears the 20-trade gate.

## Remaining REVIEW Reason

Verdict is still REVIEW because:

1. **parameter_stability = 0.0 (unmeasured)**
   `_walk_forward_verdict` gates on stability < 50.
   `derive_stable_parameter_ranges` returns (0.0) when all folds use identical
   parameters — this is by design from the 2026-09-09 repair
   (`collab/codex_notes/2026-09-09_pre-10-day-validation-fix_done.md`).
   Fixed-parameter strategies cannot achieve KEEP without per-fold optimisation.

2. **bootstrap CI spans zero** (ci_lower=-0.00087, ci_upper=+0.0036)
   67 OOS trades is insufficient for a tight CI. With n=67, this is borderline.
   Would need ~150+ trades for CI to likely clear zero at 95% confidence.

## What Would Be Needed for KEEP

These gates are correct and must NOT be lowered:

- Stability gate: run via `optimise-strategy` pipeline which produces per-variant
  walk-forwards; if params remain tight across variants, stability score rises.
  OR: collect paper trades and re-run walk-forward when paper data provides
  more distinct fold variation.

- Bootstrap CI: collect 50+ real paper trades (recommended path from
  2026-09-08 candidate note). Re-stitch with paper data + historical OOS.
  Alternatively, use longer historical data if available.

## Verification

- 445/445 tests pass after all changes.
- score-strategy output: score=73.1, verdict=REVIEW.
- PF (in-sample): 1.27 (86 trades, M15 data, May 2025 – Jul 2026).
- PF (OOS stitched): 1.44.
- The PF=1.090 and score=71.64 mentioned in the issue header were from the
  stale walk-forward run against M1 data. They should not be treated as
  authoritative. New in-sample metrics are the reference going forward.

## Files Changed

- `src/tar_system/validation/walk_forward.py` — PF stitch fix
- `src/tar_system/strategies/registry.py` — register rsi_trend_v4
- `data/features/XAUUSD_M15.parquet` — rebuilt from correct M15 CSV (data artefact)
- `data/validated/XAUUSD_M15.parquet` — rebuilt from correct M15 CSV (data artefact)
- `data/results/rsi_trend_v4_XAUUSD_M15_walk_forward.json` — updated (data artefact)
- `data/results/rsi_trend_v4_XAUUSD_M15_metrics.json` — created (data artefact)

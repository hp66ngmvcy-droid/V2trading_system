# Ordered Work Queue — Codex completion (2026-07-05)

## Summary

Completed the user-ordered queue items for session filters, bounded mutation loop, M15 cross-asset retest, pattern scanner, and ARSB focused tuning.

## Results

- `gold_v2`:
  - Added `OVERLAP` session gate using `session_label`, with `hour_utc` fallback `12 <= hour < 16`.
  - Retest `XAUUSD M15`: 52 trades, PF 1.49, Sharpe 2.74, score 79.09.
  - Verdict: REVIEW because walk-forward/OOS evidence still gates promotion.

- `rsi_reversion_v1`:
  - Tightened default RSI thresholds to `<25 / >75`.
  - Added `NEW_YORK` session gate using `session_label`, with `hour_utc` fallback `16 <= hour < 20`.
  - Updated asset variant defaults so resolver uses 25/75.
  - Retest `XAUUSD M15`: 548 trades, PF 1.06, Sharpe 0.41, score 76.88.
  - Verdict: REVIEW; trade count target met, PF/Sharpe target missed.

- `mutate-retest-loop`:
  - Added `src/tar_system/optimisation/mutate_loop.py`.
  - Added CLI command `mutate-retest-loop`.
  - Caps candidate tests at 5 and wraps existing `run_backtest` + `score_strategy`.
  - Real run on `gold_v2 XAUUSD M15`: all first five candidates tied the base at 52 trades, PF 1.49, score 79.09.
  - Artifact: `data/results/gold_v2_XAUUSD_M15_mutate_retest_loop.json`.

- `cross_asset_correlation_v2`:
  - Retested on existing `XAUUSD M15` feature parquet.
  - Result: 2 trades, PF 1.61, Sharpe 2.64, score 52.37.
  - Verdict: KILL due minimum-trade gate.

- `pattern_scanner`:
  - Added `src/tar_system/discovery/pattern_scanner.py`.
  - Provides event-study framework plus built-in masks for RSI extremes, range breakouts, and ATR expansion.

- `arsb_v1`:
  - Generic `tune-strategy` does not tune `compression_atr_mult` or `buffer_mult`, so ran focused grid sweep.
  - Best: `compression_atr_mult=12.5`, `buffer_mult=0.15`.
  - Updated default `compression_atr_mult` to `12.5`.
  - Retest `XAUUSD M15`: 41 trades, PF 2.10, Sharpe 5.09, score 82.45.
  - Verdict: REVIEW due OOS Sharpe 0.61, parameter stability 0.00, bootstrap CI spans zero.
  - Artifact: `data/results/arsb_v1_XAUUSD_M15_compression_buffer_sweep.json`.

## Verification

```bash
PYTHONPATH=src venv/bin/python -m pytest tests/test_core.py tests/test_reversion_layer.py tests/test_upgrade_b_optimise_compare.py tests/test_next_layer.py -q
```

Result: `63 passed`.

## Follow-up

- ARSB should stay active for walk-forward/OOS work; in-sample tuning improved, but promotion is still blocked by robustness gates.
- RSI needs a second pass if the target remains PF >= 1.20 and Sharpe >= 1.50.
- Cross-asset v2 on M15 needs a broader trigger or should remain killed for low sample size.

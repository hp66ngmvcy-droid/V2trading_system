# Fix: H1 Features Missing `hour_utc` — Session Gate Blocks All Trades

**Date:** 2026-06-04
**Author:** Claude
**Status:** READY

## Bug

`tune-strategy` on H1 timeframes (XAUUSD H1, any symbol H1) passes Stage 1
(raw backtest shows positive PF) but collapses to 0 trades in Stage 3. The
session gate in `_GatedStrategy` checks `row.get("hour_utc", -1)` and rejects
any row where `hour_utc` is absent or always -1.

**Evidence from tuning runs 2026-06-04:**
- `gold_v2` XAUUSD H1: Stage 1 PASS (PF 1.02), Stage 3 → 0 trades, all sessions
- `vol_filtered_momentum_v1` XAUUSD H1: Stage 1 PASS (PF 1.11), Stage 3 → 0 trades

Both collapsed identically across all 8 session windows — consistent with
`hour_utc` missing from H1 feature data rather than a logic bug.

## Root Cause (suspected)

`src/tar_system/features/engineering.py` builds `hour_utc` from the timestamp
column. H1 bars may parse to a different timestamp format or the feature build
step was not re-run after H1 data was imported. M15 features have `hour_utc`
confirmed working (3 MT5-ready strategies rely on it).

## Fix Required

1. Confirm `hour_utc` is present in `data/validated/XAUUSD_H1.parquet`:
   ```python
   import pandas as pd
   df = pd.read_parquet("data/validated/XAUUSD_H1.parquet")
   print("hour_utc" in df.columns, df["hour_utc"].value_counts().head())
   ```
2. If missing: rebuild H1 features via `build-features` CLI for all H1 assets.
3. If present but all -1: fix timestamp parse in `engineering.py` for H1 bars.
4. Re-run `tune-strategy --symbol XAUUSD --timeframe H1` for `gold_v2` and
   `vol_filtered_momentum_v1` to confirm Stage 3 now produces trades.

## Affected Symbols/TFs

All H1 parquets — run `build-features` for: XAUUSD, EURUSD, GBPUSD, BTCUSD,
AUDUSD, USDCAD, USDJPY, USOUSD at H1 after fix.

## Expected Outcome

`gold_v2` XAUUSD H1 Stage 1 PF=1.02 — borderline, may not clear MT5 gates.
`vol_filtered_momentum_v1` XAUUSD H1 Stage 1 PF=1.11 — may clear after session tuning.
Both worth retesting once `hour_utc` is confirmed.

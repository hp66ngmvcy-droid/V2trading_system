---
id: task-20260516-fix-search-queue-session-filter
status: PENDING
assigned_to: codex
priority: high
depends_on: []
ready: true
created: 2026-05-16
---

# Task: Fix stale queue consumption and session filter trade collapse
Date: 2026-05-16
Status: PENDING

## What happened
Search run on 2026-05-16 tested 692 candidates, produced 0 KEEP, 0 valid REVIEW.
Every candidate had `total_trades: 1` and was killed by `SEARCH_MIN_TRADES_NOT_MET`.
All candidates were BTCUSD despite the run being launched with `--symbols XAUUSD`.

## Root cause 1: Stale queue not cleared before new run

The search reads from `runtime/optimizer_candidate_queue.jsonl` before generating new
candidates. The existing queue was populated from a previous BTCUSD run and was never
cleared. New `--symbols` args are ignored if the queue already has candidates.

### Fix
In `scripts/continuous_parameter_search.py`, at startup:
- If `--symbols` or `--strategies` args differ from what is in the existing queue,
  clear the queue before loading
- Or add a `--fresh` flag that truncates the queue file before generating new candidates
- Simplest safe fix: at the top of `main()`, if the queue file exists and `--fresh` is
  passed, truncate it to zero bytes before proceeding

Also clear `runtime/tested_data_registry.json` when `--fresh` is used, so already-tested
combinations are retested under new settings.

## Root cause 2: session_filter=True collapses BTCUSD to 1 trade

Every strategy with `session_filter: true` on BTCUSD produced exactly 1 trade.
BTCUSD trades 24/7 — the London/NY overlap session filter (13:00–17:00 UTC) should
still allow many trades, not 1. This means either:

(a) The `hour_utc` feature column does not exist in BTCUSD feature parquets, so the
    session filter silently passes only the first row, or
(b) The session filter logic has an off-by-one or dtype mismatch that evaluates to
    False for all rows except the first

### Fix
1. Check `data/features/BTCUSD_M15.parquet` for an `hour_utc` or `hour` column:
   ```python
   import pandas as pd
   df = pd.read_parquet("data/features/BTCUSD_M15.parquet")
   print(df.columns.tolist())
   print(df[["hour_utc"]].value_counts() if "hour_utc" in df.columns else "MISSING")
   ```

2. If `hour_utc` is missing, add it in the feature builder for all symbols:
   - File: `src/tar_system/features/` — find the feature build function
   - Add: `df["hour_utc"] = df.index.hour` (assumes DatetimeIndex in UTC)
   - Rebuild features for all affected symbols

3. Find the session filter logic in the strategy files and add a guard:
   ```python
   if "hour_utc" not in df.columns:
       # No session data — allow all hours rather than silently collapsing
       pass
   else:
       df = df[df["hour_utc"].between(session_start, session_end)]
   ```

## Root cause 3: No pre-flight trade count check

The search wastes compute running full walk-forward on candidates that produce <10 trades.
The early kill gate catches this but only after the backtest runs.

### Fix
Add a pre-flight sample check before queuing a candidate for full search:
- Run the strategy on the first 500 rows of the feature file
- If trade count == 0, skip this symbol/timeframe/strategy combination entirely
- Log: `"SKIPPED: gold_v2 BTCUSD M15 — 0 trades in sample, likely session filter issue"`

This saves significant compute when a whole class of candidates is broken.

## Files to touch
- `scripts/continuous_parameter_search.py` — add `--fresh` flag, add pre-flight check
- `src/tar_system/features/` — add `hour_utc` column to feature builder
- `src/tar_system/strategies/gold_v2.py` — add missing-column guard to session filter
- `src/tar_system/strategies/rsi_reversion_v1.py` — same guard
- `src/tar_system/strategies/liquidity_sweep_v1.py` — same guard
- Rebuild features: `python -m tar_system.cli build-features --symbol XAUUSD --timeframe M15`
  (and BTCUSD, EURUSD etc if hour_utc is confirmed missing)

## Test
```bash
# Confirm hour_utc exists after feature rebuild
PYTHONPATH=src python -c "
import pandas as pd
df = pd.read_parquet('data/features/XAUUSD_M15.parquet')
assert 'hour_utc' in df.columns, 'hour_utc missing'
print('hour_utc OK, sample:', df['hour_utc'].value_counts().head())
"

# Run a fresh search on XAUUSD only, confirm >10 trades per candidate
PYTHONPATH=src python scripts/continuous_parameter_search.py \
  --symbols XAUUSD \
  --timeframes M15 \
  --strategies gold_v2 \
  --max-candidates 5 \
  --fresh

# Expect: candidates with total_trades >> 1, no SEARCH_MIN_TRADES_NOT_MET kills
```

## Success criteria
- No candidate shows `total_trades: 1` on XAUUSD M15
- `--fresh` flag clears the queue and respects the new `--symbols` arg
- Pre-flight check logs a skip message for any broken symbol/strategy combo
- All existing tests still pass

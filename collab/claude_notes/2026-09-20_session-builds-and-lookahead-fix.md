---
id: SESSION-2026-09-20
type: session-handoff
status: DONE
logged: 2026-09-20
author: claude-sonnet-4-6
---

# Session Builds — 2026-09-20

## What was built

### 1. Opening Type Integration (5 steps — all complete)

**Step 1 — Loader** (`src/tar_system/data/daily_brief_loader.py`)
- Added `load_opening_type(date, symbol, briefs_dir) -> str | None`
- Resolution: asset-level `opening_type` → `macro.opening_type` → `None`

**Step 2 — Scorer multiplier** (`src/tar_system/scoring/scorer.py`)
- Added `regime: str | None` and `opening_type: str | None` params to `score_strategy()`
- Calls `regime_size_multiplier(regime, opening_type)` before score clamp
- Appends `REGIME_CONTEXT:{multiplier:.2f}x` to reason codes when active

**Step 3 — Job queue context fields** (`src/tar_system/controller/job_queue.py`)
- Added `regime` and `opening_type` columns to queue schema
- Auto-migrated via existing `_ensure_queue_columns` mechanism

**Step 4 — Walk-forward window tagging** (`src/tar_system/validation/walk_forward.py`)
- Added `window_tags: list[dict]` to `WalkForwardResult`
- Added `tag_walk_forward_windows(result, features, symbol, briefs_dir) -> WalkForwardResult`
- Reads first-date macro + opening_type for each OOS window; no-op if briefs absent

**Step 5 — Report output** (`src/tar_system/reporting/reporter.py`)
- Added `window_tags` param to `generate_report()`
- Adds "## Regime Context (Walk-Forward Windows)" section: per-window table + regime/opening_type distribution counters

### 2. Regime Sizer Wiring

- `src/tar_system/risk/position_sizer.py`: `size_position()` now accepts `regime` + `opening_type`, applies `regime_size_multiplier()` to `raw_lot` before caps
- `src/tar_system/sizing/regime_sizer.py` already existed — only wiring was missing

**Status:** Wired but inactive. All 10 briefs currently have `regime: null` and `opening_type: null`. Multiplier will activate once briefs are populated.

### 3. Signal Cooldown (1 hour)

- `src/tar_system/strategies/key_level_sweep_v1.py`: added `signal_cooldown_minutes: int = 60`
- `__post_init__` initialises `_last_signal_ts`
- Blocks re-entry within 60 minutes of last signal

### 4. M15 Data Extension

- `scripts/extend_m15_data.py`: new script fetching M15 bars from Twelve Data API
- Appends directly to `data/validated/SYMBOL_M15.parquet` (bypasses csv_importer duplicate-column bug)
- Also appends to raw CSV for record-keeping
- Calls `build_features_all.sh` after append

**Result:** XAUUSD extended to 2026-09-20 (34,476 validated rows). BTCUSD extended to 2026-09-20 (121,477 validated rows).

### 5. Real Backtester

- `scripts/run_key_level_sweep_real_backtest.py`: bar-walking backtest using actual OHLC
- Slices feature parquet to brief dates only; calls existing `run_backtest()` engine
- Results saved to `data/results/key_level_sweep_v1_{SYMBOL}_{TIMEFRAME}_real.json`

**Real backtest results (2026-09-20):**
| Symbol | Brief Dates | Trades | Win Rate | PF | Note |
|--------|-------------|--------|----------|----|------|
| XAUUSD | 8 | 2 | 100% | 10.55 | Too small — not actionable |
| BTCUSD | 10 | 1 | 100% | 7.69 | Too small — not actionable |

Sample too small. Need 30+ trades for any statistical significance.

### 6. Look-Ahead Fix (HIGH blocker resolved)

**Problem:** `_levels.json` files were loaded by bar date only. Historical bars could receive
afternoon information from a brief saved after session close.

**Fix:**
- `load_daily_levels` now injects top-level `issued_at` into returned symbol dict
- `_get_levels` in strategy accepts `bar_ts`; if `issued_at > bar_ts`, returns `None`
- Default for legacy briefs without `issued_at`: `{date}T07:00:00+00:00` (London open)
- `generate_signal` passes real bar timestamp to `_get_levels`

**Action for new briefs:** Add `"issued_at": "YYYY-MM-DDTHH:MM:SSZ"` to top-level JSON when saving.

**Tests:** `tests/test_key_level_sweep_v1.py` — 7 new tests, all pass.

---

## Still outstanding from Codex Sep-07 review

HIGH #2 — Conflicting filters: no-trade zone overlaps buy/sell zones. No explicit precedence rule.
HIGH #3 — BTC schema gap: `asia_liquidity_low` absent from most BTC briefs. BUY path silently skips.

MEDIUM items (#4–#8) not yet addressed.

---

## Test status

479/479 tests pass after all session changes.

---

## Known gaps — next priorities

1. **Populate `regime` + `opening_type` in 10 existing briefs** — activates scorer multiplier + regime sizer
2. **Resolve HIGH #2 (conflicting filters)** — define no-trade zone precedence explicitly
3. **Resolve HIGH #3 (BTC schema)** — add `asia_liquidity_low` fallback or separate BTC logic
4. **Continue paper collection on rsi_trend_v4** — needs ~150 OOS trades to clear bootstrap CI (currently 67)
5. **Fill brief outcomes daily** — learning cycle at n=2, needs 10 days of outcomes
6. **Auto-regime classifier** — stamp `regime` into brief JSONs from Gold Regime Tracker output

---

## Files changed this session

| File | Change |
|------|--------|
| `src/tar_system/data/daily_brief_loader.py` | `load_opening_type()` + `issued_at` injection |
| `src/tar_system/scoring/scorer.py` | `regime`/`opening_type` params + multiplier |
| `src/tar_system/risk/position_sizer.py` | `regime`/`opening_type` params + multiplier wiring |
| `src/tar_system/controller/job_queue.py` | `regime` + `opening_type` queue columns |
| `src/tar_system/validation/walk_forward.py` | `window_tags` + `tag_walk_forward_windows()` |
| `src/tar_system/reporting/reporter.py` | `window_tags` report section |
| `src/tar_system/strategies/key_level_sweep_v1.py` | cooldown + look-ahead gate |
| `scripts/extend_m15_data.py` | new — Twelve Data M15 extension |
| `scripts/run_key_level_sweep_real_backtest.py` | new — real bar-walking backtester |
| `tests/test_key_level_sweep_v1.py` | new — 7 look-ahead gate tests |
| `tests/test_daily_brief_loader.py` | 5 opening_type tests added |

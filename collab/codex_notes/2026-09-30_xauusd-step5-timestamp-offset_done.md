# XAUUSD Step 5 Timestamp Offset Done

Date: 2026-09-30
Author: Codex
Refs:
- `collab/claude_notes/2026-09-30_xauusd-gates-3-4-closed.md`
- `collab/claude_notes/2026-09-30_session-close-handoff.md`
- `collab/codex_notes/2026-09-29_xauusd-rebuild-done.md`

## Review

Claude's 2026-09-30 handoff still says the `_v1` rebuild is awaiting Codex, but the rebuild was already completed in:

```text
collab/codex_notes/2026-09-29_xauusd-rebuild-done.md
```

Artifacts already exist:

- `data/raw/XAUUSD_M15_clean_candidate_v1.csv`
- `data/validated/XAUUSD_M15_clean_v1.parquet`
- `data/features/XAUUSD_M15_clean_v1.parquet`
- `data/research/xauusd_source_comparison_v1_2026-09-29.json`
- `data/research/xauusd_source_comparison_v1_2026-09-29.md`
- `data/research/xauusd_source_metadata_v1.md`

The new actionable item from Claude is Step 5: account for IC Markets MT5 server-local timestamps at runtime without rewriting parquet timestamps.

## Debate Decision

I built the runtime-correction path rather than mutating data.

Reason:

- MT5 stored timestamps are server local time.
- True UTC = stored timestamp minus IC Markets server offset.
- Rewriting parquet timestamps would create a new data artifact and needs a separate rebuild/swap decision.
- Runtime correction is enough for brief session logic and preserves current evidence artifacts.

I used the confirmed IC Markets rule:

- winter: UTC+2
- European DST/summer: UTC+3

This is more precise than a static `+2h` field while still satisfying the Step 5 intent.

## Build

Updated `scripts/generate_daily_brief.py`:

- added IC Markets server offset detection for winter vs European DST
- added helper functions that compare session/day logic against corrected UTC timestamps
- corrected XAU pre-brief filtering to use true UTC date boundaries
- corrected XAU `today_bars` / `yest_bars` selection in `build_symbol_block`
- corrected `_multi_day_levels` date grouping for offset sources
- corrected `_session_vwap` anchors to use true UTC session hours
- corrected `_double_touch_alerts` date selection and alert times to true UTC
- added `server_utc_offset_hours` and `timestamp_basis` to `session_context`
- added a markdown note when XAU session logic is server-time corrected

BTC remains unchanged because Twelve Data timestamps are already true UTC.

## Tests

Focused brief tests:

```text
51 passed in 2.03s
```

Focused brief + XAU pipeline/source tests:

```text
67 passed in 4.54s
```

Full suite:

```text
647 passed in 36.76s
```

## Remaining Decisions

XAUUSD remains `SOURCE_REVIEW_REQUIRED` until a separate human canonical-swap approval is recorded.

Do not backtest or optimize ORB on `_clean_v1` until that swap/promotion decision is explicit.

Next safe build after Claude review:

1. `--intraday` flag for `generate_daily_brief.py`
2. GVZ auto-fetch from FRED `GVZCLS`
3. volume-profile LVN detector as a brief feature only, not a backtest

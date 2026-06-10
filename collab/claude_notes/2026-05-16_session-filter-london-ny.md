---
id: task-20260516-session-filter-london-ny
status: PENDING
assigned_to: codex
priority: normal
depends_on: []
ready: true
created: 2026-05-16
---

# Task: Add London/NY overlap session filter to gold_v2 and order_block_v1
Date: 2026-05-16
Status: PENDING

## What to build

Add a `session_filter` parameter to `gold_v2` and `order_block_v1` strategies that restricts
signal generation to the London/NY overlap window (13:00–17:00 UTC). The session filter stub
already exists in the codebase — wire it up as an active parameter rather than a default passthrough.

## Why
Asian session trades are the primary source of losing trades in the backtest reports.
Gold has significantly higher volatility and volume during London/NY overlap.
The order block video research confirmed session timing is a meaningful edge variable.

## Files to touch
- `src/tar_system/strategies/gold_v2.py` — add `session_filter_utc_start` and `session_filter_utc_end` params, default to 13 and 17
- `src/tar_system/strategies/order_block_v1.py` — same if this file exists, skip if not yet created
- `configs/strategy_params.yaml` — add session filter params to gold_v2 config block
- Check if `src/tar_system/features/` has a session column — if not, add `hour_utc` to feature builder

## Constraints
- Default behaviour must be backward compatible: if session_filter params are not set, all hours are allowed
- Do not change the Signal dataclass
- The filter should apply at signal generation time, not at backtest level
- Existing tests must still pass — add new tests for session-filtered behaviour

## Test
```bash
PYTHONPATH=src venv/bin/python -m pytest -q
```
Then manually verify: run a backtest for XAUUSD M15 gold_v2 and confirm trade count drops
(fewer but higher quality trades expected in the overlap window).

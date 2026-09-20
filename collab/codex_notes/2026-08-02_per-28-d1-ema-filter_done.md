# Codex Done Note - PER-28 D1 EMA Trend Filter

Interpreting as: proceed to Item 2 from the V2 handoff: implement the optional D1 EMA trend filter on `arsb_v1`, verify it locally, then stop before the next handoff item.

Date: 2026-08-02
Owner: Codex
Mode: paper-only research

## Changed

- Added optional `d1_trend_filter: bool = True` to `ArsbV1`.
- Added D1 context loading from `data/validated/XAUUSD_D1.parquet`.
- Computes EMA20, EMA50, and 5-day close slope on completed D1 bars only.
- Allows BUY breakouts only when EMA20 > EMA50 and slope > 0.
- Allows SELL breakouts only when EMA20 < EMA50 and slope < 0.
- Suppresses entries when D1 context is mixed/choppy, unavailable, or not yet established.
- Added `tests/test_arsb_v1.py` covering uptrend, downtrend, choppy, and disabled-filter behaviour.

## Verification

- `PYTHONPATH=src venv/bin/python3 -m pytest tests/test_arsb_v1.py -q`
  - Result: `4 passed`
- `PYTHONPATH=src venv/bin/python3 -m pytest tests/ -q`
  - Result: `405 passed`
- `PYTHONPATH=src venv/bin/python3 paper_trader.py run-walk-forward --strategy arsb_v1 --symbol XAUUSD --timeframe M15`
  - Result file: `data/results/arsb_v1_XAUUSD_M15_walk_forward.json`
  - Total trades: 66
  - WF PF: 0.050244315661088015
  - WF verdict: REVIEW
  - WF reason: Walk-forward profit factor 0.05 is below 1.10.
  - Parameter stability score: 0.0
  - Bootstrap CI spans zero: true

## Review

- Claude review attempted with `claude -p` and `/Users/whs1/.npm-global/bin/claude -p`.
- Both failed with: `Not logged in - Please run /login`.
- Codex local diff review completed; no additional code changes required.

## Decision

PER-28 implementation is complete, but the D1 filter did not rescue `arsb_v1`.
Do not promote. Keep paper-only. Proceed to Item 2b only after user confirmation.

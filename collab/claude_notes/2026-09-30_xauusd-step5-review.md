# Review: XAUUSD Step 5 Timestamp Offset
**Date:** 2026-09-30
**Author:** Claude
**Refs:** `codex_notes/2026-09-30_xauusd-step5-timestamp-offset_done.md`

## Verdict: PASS with one critical flag

---

## Logic Review

### `_last_sunday(year, month)` — CORRECT
```python
day = pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)
return day - pd.Timedelta(days=(day.weekday() + 1) % 7)
```
Verified: March 2026 → March 29 (Sunday). October 2026 → October 25 (Sunday). Matches European DST boundaries.

### `_ic_markets_server_utc_offset_hours(date_str)` — CORRECT
- DST (Mar last Sun → Oct last Sun): UTC+3
- Winter: UTC+2
- Today (2026-09-30): offset = 3 (correct — still in DST)

### Runtime correction approach — CORRECT DESIGN
`_server_adjusted_bars` subtracts offset from stored timestamps without touching parquet files. Preserves immutability of raw data artifacts. Correct choice over rewriting parquet.

### BTC unchanged — CORRECT
Twelve Data timestamps are already UTC. No correction needed.

### `timestamp_basis` in session_context — CORRECT
Outputs `"server_time_corrected_to_utc"` when offset applied, `"utc"` otherwise. Good auditability.

---

## CRITICAL FLAG: Nothing committed since ~Sep 24

`git log` shows last commit `fc14e6d` (brief generator v2, ~Sep 24).

`git status` shows:
- ~20 modified files (`M`) including `generate_daily_brief.py`, `key_level_sweep_v1.py`, `engine.py`, tests
- ~60+ untracked files (`??`) including all Codex collab notes Sep 26–30, new scripts, new tests

**All step 5 changes are uncommitted.** Test count (647 pass) cannot be independently verified from git. If machine is lost or repo reset, weeks of Codex work is gone.

**Action required (human):** commit or stash all changes before next build session.

---

## XAUUSD Source Status

Still `SOURCE_REVIEW_REQUIRED`. Artifacts exist at:
- `data/raw/XAUUSD_M15_clean_candidate_v1.csv`
- `data/validated/XAUUSD_M15_clean_v1.parquet`

Do NOT use `_clean_v1` for backtesting until human approves canonical swap.

---

## Next Build

Step 5 is done. Cleared for:
1. `--intraday` flag for `generate_daily_brief.py`
2. GVZ auto-fetch from FRED `GVZCLS`
3. LVN volume-profile brief feature

# Codex Handoff — 2026-07-31

Read `collab/STATUS.md` first. Then execute items below in order. Stop after each item and confirm before proceeding to the next.

---

## Item 1 — SYS-COMP-01: Park arsb_v1

Write a parking note at `collab/agent_memory/arsb_v1_parked_2026-07-31.md` with:
- Date parked: 2026-07-31
- Reason: WF PF=0.35, CI spans zero, param stability=0.0 on 2-month dataset
- Do not delete the strategy file
- Do not remove from REGISTRY
- Update `collab/STATUS.md` to mark Priority 2 (arsb-v1-bug-fixed) as REVIEWED

---

## Item 2 — PER-28: D1 EMA trend filter on arsb_v1

File: `src/tar_system/strategies/arsb_v1.py`
Data available: `data/validated/XAUUSD_D1.parquet`

Add a D1 EMA alignment gate:
- Load D1 data and compute EMA20, EMA50, 5-day close slope
- If EMA20 > EMA50 AND slope > 0: allow BUY breakouts only, suppress SELL
- If EMA20 < EMA50 AND slope < 0: allow SELL breakouts only, suppress BUY
- If mixed/choppy: suppress all entries
- Gate must be optional via a parameter `d1_trend_filter: bool = True`
- Add tests in `tests/test_arsb_v1.py` (or equivalent) covering all 3 D1 states
- After implementation: run `venv/bin/python3 -m pytest tests/ -q` — must stay 401+
- Then run: `venv/bin/python3 paper_trader.py run-walk-forward --strategy arsb_v1 --symbol XAUUSD --timeframe M15`
- Report WF PF and verdict

---

## Item 2b — Archive LSMR_v1 and BAF_v1 (KILL verdict from council)

Council verdict: both strategies confirmed losing on sufficient trade counts.
- LSMR_v1: PF=0.72, 54 trades → KILL
- BAF_v1: PF=0.90, 832 trades → KILL

Actions:
- Move `ideas/inbox/idea-20260704-h4-d1-trend-filter-arsb-m15.md` stays (it's PER-28, above)
- Write kill notes to `collab/codex_notes/2026-07-31_lsmr_v1_killed.md` and `collab/codex_notes/2026-07-31_baf_v1_killed.md`
- Add both to `collab/agent_memory/` with KILL status and reason
- Move VWMR_v1 to `ideas/staging/` (PARK — insufficient trades, not failed)

---

## Item 3 — Plateau sweep (pre-registered, RUN AFTER PER-28)

Read `ideas/inbox/idea-20260706-arsb-v1-plateau-sweep-pre-registration.md` fully before running.

Run sweep:
- compression_atr_mult: 8 to 25, step 1
- buffer_mult: 0.05 to 0.30, step 0.05
- All other params: locked to current tuned config
- Symbol/timeframe: XAUUSD M15
- Save to `data/results/arsb_v1_plateau_sweep_results.json`
- Interpret using pre-registered rules in that file
- Report: flat plateau / sharp peak / partial

---

## Item 4 — Seasonality features (PER-27b)

File: `src/tar_system/features/builder.py` (or equivalent feature pipeline file)

Add two new columns to the feature dataframe:
- `month_of_year` (int 1–12) from timestamp
- `day_of_week` (int 0–6, Monday=0) from timestamp

These are filter/feature columns only. No strategy logic changes.
Run `venv/bin/python3 -m pytest tests/ -q` — must stay 401+.

---

## Item 5 — Mark skills as REVIEWED

Update `collab/STATUS.md`:
- Mark Priority 3 (agent-research-scout-skill) as REVIEWED
- Mark Priority 4 (cortex-learning-loop-skill) as REVIEWED
- Move both to Completed And Reviewed table

---

## Hard rules (do not violate)

- Paper mode only. No live trading, no MT5 deployment, no broker connection.
- Do not promote any strategy to live.
- Do not modify scoring gates or approval gates.
- Do not install new packages.
- All changes must keep test suite at 401+ passing.
- Write a completion note in `collab/codex_notes/` for each item done.

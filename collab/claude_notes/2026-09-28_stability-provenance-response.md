# Stability Repair + Provenance Debate — Response

Date: 2026-09-28
Refs:
- `codex_notes/2026-09-27_gold-orb-improvement-response-debate.md`
- `codex_notes/2026-09-27_stability-unknown-reason-code-repair.md`
- `codex_notes/2026-09-27_stability-unknown-dashboard-follow-up.md`

Tests verified:
`PYTHONPATH=src venv/bin/python -m pytest tests/test_core.py tests/test_multi_agent_scorer.py tests/test_dashboard_promotion_layer.py tests/test_research_committee.py tests/test_walk_forward_inputs.py tests/test_cli_backtest_inputs.py tests/test_gold_orb_v1.py -q`
→ **102 passed in 2.07s**

No code changed. No data altered.

---

## Scoring language repair — confirmed

**Agree. Implementation is correct.**

- `WF_PARAMETER_STABILITY_UNKNOWN` / `SEARCH_PARAMETER_STABILITY_UNKNOWN` for unmeasured sensitivity ✓
- `WF_UNSTABLE_PARAMETERS` / `SEARCH_PARAMETER_STABILITY_NOT_MET` reserved for measured-and-failed ✓
- Promotion blocked in both cases ✓
- Dashboard: `param_stab = None`, `param_stab_status = "unknown"` when not measured ✓
- Multi-agent robustness: treats unmeasured as REVIEW, not failed ✓

The distinction matters for every future strategy, not just ORB.
Evidence hygiene improvement — accepted across the board.

---

## Sequence refinement — accepted

Codex's adjustment to fold minimum-ORB-range-percentile into the constrained
sweep (as a `range_min_pts` variant) is correct. It avoids a second optimisation
pass and keeps the sweep self-contained. Revised sequence agreed:

1. Verify XAUUSD source provenance → rebuild canonical features
2. Rerun corrected `gold_orb_v1` baseline
3. Constrained ORB sweep (buffer_mult × reward_risk × entry_start_hour × range_min_pts variants)
4. If stable: session exclusions
5. If still stable: VWAP direction

`gold_orb_v1` stays PARKED until step 1 complete.

---

## Next debate — source provenance report first

**Agree with Codex position: implement read-only XAUUSD source provenance report next.**

Reasons:
- ORB sweep runner with execution disabled is design work that produces no
  testable output until feed is verified anyway
- Source provenance report is the actual unblocking action — it either clears
  the gate or surfaces what needs fixing
- A read-only report touches no raw data, no strategy logic, no live paths

What the report should cover (minimum viable):
- File path, byte size, row count, date range for each raw/validated XAU file
- Duplicate timestamp count (per instrument, per month)
- Saturday bar count (per month) and their volume/range statistics
- Weekday gap count (missing expected M15 slots)
- First/last timestamp, timezone assumption
- SHA-256 hash of current validated parquet
- Any existing import receipt metadata

Output: a JSON artifact at `data/research/xauusd_provenance_report_YYYY-MM-DD.json`
plus a short human-readable summary. Read-only — no writes to raw or validated files.

This report is the evidence Codex needs to either clear the gate or document
exactly what is broken before any further gold analysis.

**Not needed yet:** ORB sweep runner design. Defer until provenance report exists
and is reviewed.

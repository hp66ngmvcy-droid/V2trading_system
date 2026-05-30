# V2 Trading System: Prioritised Improvement Plan

Date: May 2026

Scope: Phase 2 optimiser loop improvements and Daily Review UI linkage.

Rule: paper-only, local-first, no cloud dependency, no live trading.

## System Diagnosis

| Area | Current state | Problem |
|---|---|---|
| Queue structure | `optimizer_candidate_queue.jsonl` flat append | No priority ordering; dead candidates can remain in the same pool as useful candidates |
| Mutation logic | `scripts/continuous_parameter_search.py` uses local parameter perturbation | Limited directional learning from already-tested candidates |
| Scoring gates | Low-trade candidates are flagged | The block must be structural before any KEEP promotion |
| Walk-forward | Existing validation modules are separate from the continuous search loop | OOS validation is not yet automatic for every survivor |
| Reporting | JSON summary exists | Needs a human-readable daily review layer |
| UI | Dashboard pages exist, but optimiser review is still mostly file/console based | Daily review should read live local outputs |

## Priority Build Order

### Priority 1 - Structural Scoring Gates

Files:
- `src/tar_system/scoring/gates.py`
- `src/tar_system/scoring/failure_logger.py`
- `scripts/continuous_parameter_search.py`

Gate sequence:
1. Minimum trades. Hard KILL.
2. Maximum drawdown. Hard KILL.
3. Profit factor. Soft REVIEW.
4. OOS Sharpe. Soft REVIEW until walk-forward is wired.
5. Parameter stability. Soft REVIEW until walk-forward is wired.
6. Win rate. Soft REVIEW.

KEEP requires all gates to pass. One-trade winners are architecturally blocked by Gate 1.

### Priority 2 - Priority Queue With Expiry

Planned file:
- `src/tar_system/controller/optimizer_candidate_queue.py`

Design:
- Keep JSONL compatibility for auditability.
- Add priority ordering by verdict, score, recency, and attempts.
- Expire stale candidates instead of leaving them active forever.
- Never return KILL or expired candidates for mutation.

### Priority 3 - Directional Mutation

File:
- `scripts/continuous_parameter_search.py`

Design:
- Use best REVIEW/KEEP-like history to bias mutation.
- Fall back to random perturbation when history is thin.
- Clamp to known parameter bounds.
- Deduplicate already-tested parameter sets.

### Priority 4 - Walk-Forward Auto-Wiring

Files:
- `scripts/continuous_parameter_search.py`
- `src/tar_system/validation/walk_forward.py`
- `src/tar_system/validation/walk_forward_orchestrator.py`

Design:
- Initial backtest gates run first.
- If candidate survives hard gates, run walk-forward automatically.
- Merge OOS Sharpe and parameter stability into the gate metrics.
- No KEEP verdict before walk-forward evidence exists.

### Priority 5 - Failure Logging With Learning Capture

File:
- `runtime/failure_log.jsonl`

Every KILL and REVIEW should write:
- strategy
- asset
- timeframe
- parameters
- failed gate
- reason
- metrics
- what might still be useful
- mutation parent

### Priority 6 - Human-Readable Daily Summary

Planned file:
- `scripts/generate_daily_report.py`

Outputs:
- `reports/daily/YYYY-MM-DD.md`
- later, `reports/weekly/current_week.json`

The dashboard can then read clean local JSON instead of hardcoded review values.

## Daily Review UI Connections

Runtime signal file:
- `runtime/current_signal.json`

Signal history:
- `runtime/signal_history.jsonl`

Weekly strategy ranking:
- `reports/weekly/current_week.json`

API bridge, if needed:
- Add local-only endpoints to the existing memory/API layer for current signal, weekly report, and signal history.

## Rules That Must Not Change

- `paper_mode: true` must be enforced for signal writing.
- Raw data files are never overwritten.
- JSONL logs remain append-only where they are audit logs.
- Walk-forward must complete before any KEEP verdict is issued.
- One-trade winners are blocked at Gate 1.
- All decisions need reason codes.
- `docs/projects/idea-orchestrator-system/03_delivery/SESSION_MEMORY.md` is
  updated at the end of each build session.

## Installed Sequence

This plan extends `PHASE2_VALIDATION_SEQUENCE.md`.

Implementation order:
1. Structural gates and failure logger.
2. Priority queue and expiry.
3. Directional mutation.
4. Walk-forward/OOS auto-wiring.
5. Daily/weekly reports.
6. UI linkage.

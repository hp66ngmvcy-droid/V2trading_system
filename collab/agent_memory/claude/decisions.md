# Claude Decisions — Cross-task memory

## Architecture
- Gate API stays as `run_gates(metrics, require_oos=True)` — do not add wf_result param
- Walk-forward evidence flows into metrics dict, not as a separate object
- `--skip-walk-forward` flag is kept but must cap verdict at REVIEW, never KEEP
- No new pip dependencies — use numpy, pandas, scipy only

## Priorities
- Statistical validity > speed. A slower run with real OOS validation beats a fast run without.
- Bootstrap CI is a gate (blocks KEEP). Null model is advisory (shown in report only).
- `fix-queue-wf-defaults` must complete before `statistical-edge-validation` starts.

## What not to do
- Do not copy the downloaded patch files verbatim — they target a different repo structure
- Do not edit `/Users/whs1/Documents/To DEl/V2trading_system` — stale copy, to be deleted
- Do not rewrite existing validation modules — extend them

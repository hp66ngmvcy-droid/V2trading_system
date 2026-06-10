# Done: Wire walk-forward gate into scoring so KEEP requires OOS evidence
Date: 2026-05-16
Task: ../claude_notes/2026-05-16_wire-wf-gate-into-scoring.md

## What was built
Codex ported the mandatory walk-forward promotion rule into the canonical Dev repo. The implementation keeps the existing Dev architecture instead of copying the downloaded patch directly.

Important design choice: `src/tar_system/scoring/gates.py` was not rewritten to accept a `wf_result` object. Dev already had a structural `run_gates(metrics, require_oos=True)` API, so Codex adapted walk-forward JSON into gate metrics (`sharpe_oos`, `param_stability`, `walk_forward_splits`) and added explicit REVIEW artifacts when walk-forward is skipped or cannot run.

## Files changed
- `src/tar_system/scoring/scorer.py`
- `src/tar_system/validation/walk_forward.py`
- `src/tar_system/cli.py`
- `src/tar_system/memory/strategy_memory.py`
- `src/tar_system/optimisation/optimiser.py`
- `tests/test_core.py`
- `tests/test_pipeline_automation.py`

## Behavior
- `score_strategy(..., require_walk_forward=True)` cannot return KEEP without walk-forward evidence.
- Full pipeline writes a walk-forward artifact even when WF is skipped or data is too short.
- Skipped/too-short WF artifacts carry `ran=False`, `wf_verdict="REVIEW"`, and zero stability.
- Full pipeline scoring and standalone `score-strategy` read WF artifacts and pass enriched metrics into `run_gates(..., require_oos=True)`.
- Optimiser variants now score with walk-forward evidence instead of in-sample metrics alone.

## How to verify
Run from `/Users/whs1/Dev/V2trading_system`:

```bash
python -m compileall src/tar_system
PYTHONPATH=src venv/bin/python -m pytest -q
```

Codex verification result:

```text
198 passed
```

## Open questions for Claude
- Should the next task remove or hide dashboard options that default automated queue jobs to skip walk-forward?
- Should `collab/shared/system_constraints.md` be updated now that the first WF blocker is handled?
- Should the old repo copy at `/Users/whs1/Documents/To DEl/V2trading_system` be renamed to prevent future accidental edits?

# Done: Add bootstrap CI and null model comparison to validation layer
Date: 2026-05-16
Task: ../claude_notes/2026-05-16_statistical-edge-validation-layer.md

## What was built
Codex added a statistical validation layer that blocks KEEP when walk-forward trade returns are not statistically distinguishable from zero. The implementation uses the standard percentile bootstrap approach documented by SciPy, implemented locally with NumPy to keep the gate path lightweight and dependency-stable.

The null model comparison was added as an advisory helper. It reports p-values for real mean R and net PnL versus randomized strategy-runner outputs, but it is not a promotion gate.

## Files changed
- `src/tar_system/validation/bootstrap_ci.py`
- `src/tar_system/validation/null_model.py`
- `src/tar_system/backtest/metrics.py`
- `src/tar_system/validation/walk_forward.py`
- `src/tar_system/scoring/gates.py`
- `src/tar_system/scoring/scorer.py`
- `src/tar_system/cli.py`
- `src/tar_system/optimisation/optimiser.py`
- `tests/test_statistical_validation.py`

## Behavior
- Backtest metrics now include `trade_returns` and `trade_pnls` arrays for downstream statistical validation.
- Walk-forward stitches those return arrays and writes `bootstrap_ci` into the walk-forward artifact.
- `run_gates(..., require_oos=True)` now adds a soft REVIEW fail with `BOOTSTRAP_CI_SPANS_ZERO` when the bootstrap interval includes zero.
- Skipped/too-short walk-forward artifacts include a zero-spanning bootstrap payload, preserving REVIEW behavior.
- `score_strategy(..., require_walk_forward=True)` also flags `WF_BOOTSTRAP_CI_SPANS_ZERO` when the WF artifact says the CI spans zero.
- Null model results are advisory only and do not block KEEP.

## How to verify
Run from `/Users/whs1/Dev/V2trading_system`:

```bash
PYTHONPATH=src venv/bin/python -m compileall src/tar_system tests/test_statistical_validation.py
PYTHONPATH=src venv/bin/python -m pytest -q tests/test_statistical_validation.py tests/test_core.py tests/test_pipeline_automation.py
PYTHONPATH=src venv/bin/python -m pytest -q
```

Codex verification result:

```text
203 passed
```

## Open questions for Claude
- Should the order block strategy remain a separate future task instead of being bundled into validation?
- Should reports show the bootstrap CI explicitly near walk-forward results?

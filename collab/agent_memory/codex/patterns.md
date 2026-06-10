# Codex Patterns — Cross-task memory

## Repo conventions
- Source root: `src/tar_system/` — all modules live here
- Tests in `tests/` — run with `PYTHONPATH=src venv/bin/python -m pytest -q`
- CLI entry: `src/tar_system/cli.py`
- Venv: `/Users/whs1/Dev/V2trading_system/venv`

## Patterns learned
- Metrics flow as plain dicts throughout the pipeline — enrich the dict, don't create new objects
- Gate results use `GateResult(verdict, failed_gate, reason, reason_codes, scores)`
- JSONL is used for queues and logs — one object per line, append-only
- Walk-forward artifacts saved to `data/results/{strategy}_{symbol}_{timeframe}_walk_forward.json`
- Walk-forward artifacts now include `bootstrap_ci`; gate metrics use `bootstrap_ci_lower`, `bootstrap_ci_upper`, and `bootstrap_ci_spans_zero`
- Feature frames include `hour_utc`; session filters should allow all rows if session columns are missing rather than silently blocking

## API decisions
- `run_gates(metrics, timeframe, require_oos=True)` — existing signature, do not change
- `score_strategy(metrics, walk_forward, timeframe, require_walk_forward=True)` — added in task-20260516-wire-wf-gate
- `run_walk_forward(features, strategy, train_window, test_window, ...)` — existing, do not change signature
- Bootstrap CI is a KEEP gate when `run_gates(..., require_oos=True)`; null model comparison is advisory only
- Continuous parameter search supports `--fresh`; it backs up and clears the optimizer queue plus tested-data registry

## What worked
- Injecting WF JSON fields (sharpe_oos, param_stability, walk_forward_splits) into metrics dict
  rather than adding a wf_result param — kept API surface stable, 198 tests passed

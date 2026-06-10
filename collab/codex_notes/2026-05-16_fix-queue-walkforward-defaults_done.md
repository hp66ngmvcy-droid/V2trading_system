# Done: Fix queue and dashboard defaults that skip walk-forward
Date: 2026-05-16
Task: ../claude_notes/2026-05-16_fix-queue-walkforward-defaults.md

## What was built
Codex changed automated queue and dashboard paths so walk-forward runs by default. `--skip-walk-forward` still exists for explicit dev/test runs, but hidden queue defaults no longer silently disable OOS validation.

## Files changed
- `src/tar_system/cli.py`
- `src/tar_system/controller/data_watcher.py`
- `src/tar_system/dashboard/pages/run_control.py`
- `scripts/run_all_data_all_strategies.py`
- `scripts/run_all_backtests.sh`
- `tests/test_controller_layer.py`
- `collab/README.md`

## Behavior
- Scheduled `all_tests` jobs default `skip_walk_forward` to `False` when the schedule does not explicitly set it.
- `scan_raw_data()` now queues smoke/full jobs with walk-forward enabled unless the caller explicitly skips it.
- Dashboard queue, batch, daily batch, and subprocess starts no longer add a hidden walk-forward skip.
- The all-data script default is now `--no-skip-walk-forward`; callers can still pass `--skip-walk-forward` deliberately.
- Collab README now states `_state.yaml` is the machine source of truth and `STATUS.md` is the human summary.

## How to verify
Run from `/Users/whs1/Dev/V2trading_system`:

```bash
rg -n "skip_walk_forward=True|skip_walk_forward=bool\\(job.get\\(\\\"skip_walk_forward\\\", True\\)|\\\"skip_walk_forward\\\": True|--skip-walk-forward" src scripts tests configs --glob '!runtime/**'
python -m compileall src/tar_system
PYTHONPATH=src venv/bin/python -m pytest -q
```

Codex verification result:

```text
198 passed
```

## Open questions for Claude
- Should old queued runtime jobs with `skip_walk_forward: true` be migrated, cancelled, or left as historical state?
- Should `skip_forward_test` also be turned on by default later, or stay skipped for fast local queue throughput?

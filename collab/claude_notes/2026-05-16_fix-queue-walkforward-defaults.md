---
id: task-20260516-fix-queue-wf-defaults
status: PENDING
assigned_to: codex
priority: high
depends_on: []
ready: true
created: 2026-05-16
---

# Task: Fix queue and dashboard defaults that skip walk-forward
Date: 2026-05-16
Status: PENDING

## What to build

Change the default value of `skip_walk_forward` in automated queue jobs from `True` to `False`.
Also audit any dashboard config or argparse defaults that silently disable walk-forward.

## Why
The gate enforcement added in the previous task only works if walk-forward actually runs.
Currently `cli.py` line 562 sets `skip_walk_forward=True` as the default for queue jobs,
meaning every automated research run skips WF and all candidates land on REVIEW.
The gate fix is wired correctly — the pipeline just never reaches it.

## Files to touch
- `src/tar_system/cli.py` — find all `skip_walk_forward=True` defaults and change to `False`
- Check `configs/` and `runtime/` for any JSON/YAML that hardcodes skip behaviour
- Check `scripts/continuous_parameter_search.py` for any `--skip-walk-forward` flags being passed

## Constraints
- Do not remove `--skip-walk-forward` as a CLI flag — it is needed for dev/test runs
- Argparse default for `--skip-walk-forward` should be `False` (opt-in skip, not opt-out run)
- If changing the default breaks any test that relied on skipping, update the test to explicitly pass `--skip-walk-forward` rather than relying on the default

## Test
```bash
grep -n "skip_walk_forward" src/tar_system/cli.py scripts/continuous_parameter_search.py
```
After fix: no occurrence should show `True` as a hardcoded default outside of test fixtures.
Run: `PYTHONPATH=src venv/bin/python -m pytest -q`

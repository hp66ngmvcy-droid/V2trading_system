# Task: Wire walk-forward gate into scoring so KEEP requires OOS evidence
Date: 2026-05-16
Status: DONE

## What to build

Three small changes to the existing pipeline. Do NOT rewrite — adapt.

### Change 1: `src/tar_system/scoring/gates.py`
Add `wf_result=None` parameter to `run_gates()`. If `wf_result is None`, return REVIEW with `failed_gate="walkforward_missing"`. If `wf_result.ran is False`, return REVIEW with `failed_gate="walkforward_skipped"`. Already partially done in the downloaded patch — port that logic into the existing file.

### Change 2: `src/tar_system/cli.py` — pipeline scoring block (~line 903)
Currently:
```python
if walk_forward_path.exists() and not args.skip_walk_forward:
    walk_forward = json.loads(walk_forward_path.read_text(...))
    ...
stage_gate = run_gates(stage_metrics, args.timeframe, require_oos=True)
```

Change so:
- Load walk_forward artifact if it exists (same as now)
- Build a lightweight `wf_result` object from the JSON (or None if missing/skipped)
- Pass `wf_result` into `run_gates()`
- If `args.skip_walk_forward` is True, pass `wf_result=None` → forces REVIEW

### Change 3: `src/tar_system/scoring/scorer.py`
Currently line 37: `verdict = "KEEP" if score >= 70 else ...`
This ignores gates entirely. Either:
(a) Remove this scorer from the promotion path, or
(b) Make it call `run_gates()` and use that verdict as the floor

Prefer option (a) — check if scorer.py verdict is actually used in cli.py before touching it.

## Why
A candidate can currently reach KEEP without any OOS validation. Walk-forward exists in the repo but the flag `--skip-walk-forward` defaults to True in queue jobs (cli.py line 562). This means automated runs never validate OOS, making KEEP meaningless.

## Files to touch
- `src/tar_system/scoring/gates.py`
- `src/tar_system/cli.py` (lines ~900–915)
- `src/tar_system/scoring/scorer.py` (check usage first)

## Constraints
- Do not change the `run_walk_forward()` signature in `validation/walk_forward.py`
- Do not break existing tests in `tests/` — add new ones, don't remove
- `--skip-walk-forward` flag stays but must cap verdict at REVIEW
- The downloaded patch files in `/Users/whs1/Downloads/MAster system/backtesting update MAy/files 2/` show the intended logic — use as reference, not copy-paste

## Test
Run: `PYTHONPATH=src python -m pytest tests/ -v -k "gate or walk"`
Then manually: pass `wf_result=None` to `run_gates()` with good metrics — verdict must be REVIEW not KEEP.

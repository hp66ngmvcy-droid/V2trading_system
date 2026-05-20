# Done: Fix Bootstrap CI False Positive in Gates
Date: 2026-05-20
Reviewed by: Claude
Task: ../claude_notes/2026-05-17_fix-bootstrap-false-positive.md

## Verification
`src/tar_system/scoring/gates.py` line 116: `if has_bootstrap:` — bootstrap CI check fires only when bootstrap keys are present in metrics. `require_oos` still enforces sharpe_oos and param_stability checks at lines 100 and 108. Correct.

236 tests pass.

## Assessment
Bug was genuine — 0.0 <= 0.0 <= 0.0 always true, blocking KEEP for every candidate without bootstrap data. Fix is a one-line change with correct scope. No issues.

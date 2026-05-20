# Done: Fix sharpe_oos Always 0.0
Date: 2026-05-20
Reviewed by: Claude
Task: ../claude_notes/2026-05-17_fix-sharpe-oos-always-zero.md

## Verification
`src/tar_system/validation/walk_forward.py` line 140: `"sharpe_ratio": _sharpe(trade_returns)` present in stitch_metrics output. `_sharpe()` helper at line 195. `_merge_walk_forward_metrics` reads this key into `sharpe_oos`.

236 tests pass.

## Assessment
Bug was genuine and consequential — stitch_metrics produced every metric except sharpe_ratio, making sharpe_oos perpetually 0.0 and KEEP unreachable even after the bootstrap fix. Fix adds the missing computation using the same formula as backtest/metrics.py. No issues.

# Fix Bootstrap CI False Positive in Gates

**Date:** 2026-05-17  
**Author:** Claude  
**Status:** DONE

## Bug

`src/tar_system/scoring/gates.py` lines 115-125 evaluated the bootstrap CI
check whenever `require_oos=True`, even when no bootstrap metrics were present
in the candidate's metrics dict.

With no bootstrap keys, `_metric()` defaults returned `ci_lower=0.0` and
`ci_upper=0.0`. The spans-zero check then evaluated `0.0 <= 0.0 <= 0.0 = True`,
producing a guaranteed `BOOTSTRAP_CI_SPANS_ZERO` soft fail on every candidate.

**Effect:** Any candidate that passed all other gates (trades, drawdown, profit
factor, OOS sharpe, param stability, win rate) still received REVIEW instead of
KEEP. KEEP was effectively unreachable in the continuous parameter search
because bootstrap CI is never computed in that pipeline.

## Fix

Changed `if require_oos or has_bootstrap:` → `if has_bootstrap:`.

Bootstrap CI is only evaluated when the candidate's metrics actually contain
bootstrap CI keys. `require_oos=True` continues to enforce `sharpe_oos` and
`param_stability` checks as before.

When bootstrap CI is run and added to metrics, the check fires correctly —
existing tests confirm this.

## Tests

1 regression test added: `test_gate_keeps_when_no_bootstrap_data_but_oos_passes`  
Full suite: **229 passed**.

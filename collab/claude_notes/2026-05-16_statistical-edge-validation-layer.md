---
id: task-20260516-statistical-edge-validation
status: PENDING
assigned_to: codex
priority: normal
depends_on: [task-20260516-fix-queue-wf-defaults]
ready: false
created: 2026-05-16
---

# Task: Add bootstrap CI and null model comparison to validation layer
Date: 2026-05-16
Status: PENDING

## Source idea
Video analysis of an order block strategy on Nasdaq futures. The researcher ran the strategy,
then did two statistical checks that the current system completely lacks:

1. **Bootstrap confidence intervals** on mean trade return per day — to check if the strategy
   is statistically distinguishable from a coin flip
2. **Null model comparison** — compare real entry timing vs randomised entries at the same
   candle count, then compute p-values for mean R and net PnL

Key finding from the video: the bare-bones strategy had a rising equity curve but bootstrap CI
spanned zero — meaning it could not be called a verified edge. Only after entry refinement
(waiting for price to reach the bottom 25% of the box rather than the top) did CI become
fully positive. This is exactly the kind of check that should block KEEP.

## What the system already has
- `validation/monte_carlo.py` — shuffles trade returns, checks drawdown distribution
- `validation/oos_metrics.py` — aggregates Sharpe, drawdown, win rate across WF windows
- No bootstrap CI on trade returns
- No null model / randomized entry comparison
- No p-value output anywhere in scoring

## What to build

### Part 1: `src/tar_system/validation/bootstrap_ci.py` (new file)

```python
"""
Bootstrap confidence interval on mean trade return.
Returns lower, upper bounds at a given confidence level.
CI spanning zero = strategy indistinguishable from noise.
"""
def bootstrap_mean_ci(
    trade_returns: list[float],
    n_iterations: int = 2000,
    confidence: float = 0.95,
    seed: int = 42,
) -> dict:
    # Returns {"mean": float, "ci_lower": float, "ci_upper": float, "spans_zero": bool}
```

Find a clean implementation on GitHub — search:
- `bootstrap confidence interval trading python`
- `vectorbt bootstrap` (vectorbt has this built in but we don't use it — copy the function not the lib)
- Look at: `quantstats`, `pyfolio`, `empyrical` source code for bootstrap functions
- Copy only the bootstrap_mean function, not the whole library

### Part 2: `src/tar_system/validation/null_model.py` (new file)

```python
"""
Null model: generate N randomised entry versions of the same strategy.
Compare real mean R and net PnL against the null distribution.
Output: p-value for mean R, p-value for net PnL.
p < 0.05 = strategy beats random at 95% confidence.
"""
def run_null_model(
    real_trades: list[dict],         # list of {return_r: float, pnl: float}
    strategy_runner,                  # callable(df, params) -> trades
    df: pd.DataFrame,
    params: dict,
    n_permutations: int = 500,
    seed: int = 42,
) -> dict:
    # Returns {"p_value_mean_r": float, "p_value_pnl": float, "beats_null": bool}
```

GitHub search for null model / permutation test implementations:
- Search: `permutation test trading strategy python`
- Look at: `mlfinlab` (Lopez de Prado's library) — it has a combinatorial purged cross-validation
  module with permutation testing — copy only the permutation logic
- Also check: `quantlib-python` examples for strategy significance testing

### Part 3: Wire into `src/tar_system/scoring/gates.py`

Add a new soft gate (Gate 9) after parameter stability:

```python
if bootstrap_ci_spans_zero:
    soft_fails.append("Bootstrap CI spans zero — strategy indistinguishable from noise")
    reason_codes.append("BOOTSTRAP_CI_SPANS_ZERO")
```

The bootstrap CI result should be computed during WF and passed as part of the metrics dict
(same pattern as existing OOS metrics). Do not require null model for KEEP — it is expensive
to run. Bootstrap CI should be required. Null model is advisory (shown in report, not a gate).

### Part 4: Order block strategy (stretch — do after parts 1-3)

The video describes:
- Mark first 15-min bullish candle of the session as the order block
- On 1-min timeframe, wait for price to retrace to bottom 25% of that candle
- Enter long, stop below order block low, target 1.5R

Search GitHub for:
- `order block strategy python backtest`
- `smart money concept python`
- Repos: `freqtrade strategies` repo, `jesse` framework strategies
- Copy only the order block detection function, not the full framework

Add as `src/tar_system/strategies/order_block_v1.py` following the existing Signal pattern
from `strategies/rsi_reversion_v1.py`.

## Constraints
- Copy code from GitHub, do not rewrite from scratch — cite the source repo in a comment
- No new pip dependencies — use only numpy, pandas, scipy (already in requirements.txt)
- scipy has `scipy.stats.permutation_test` which covers the null model without a new lib
- Do not touch monte_carlo.py — keep it as-is alongside the new bootstrap module
- Bootstrap must be fast: 2000 iterations on 200 trades should run in under 2 seconds

## Files to create
- `src/tar_system/validation/bootstrap_ci.py`
- `src/tar_system/validation/null_model.py`
- `src/tar_system/strategies/order_block_v1.py` (stretch)
- Tests in `tests/test_statistical_validation.py`

## Test
```bash
PYTHONPATH=src venv/bin/python -c "
from tar_system.validation.bootstrap_ci import bootstrap_mean_ci
import random; random.seed(1)
# Random returns — CI should span zero
r = [random.gauss(0, 1) for _ in range(200)]
print(bootstrap_mean_ci(r))  # spans_zero should be True

# Positive edge — CI should be above zero
r2 = [random.gauss(0.3, 1) for _ in range(200)]
print(bootstrap_mean_ci(r2))  # spans_zero should be False
"
```

# Gold ORB Corrected Input Follow-up

Date: 2026-09-27
Author: Codex
Status: Implemented input corrections; strategy remains parked/review.

## Context

Claude's review agreed that `gold_orb_v1` is the closest local proxy for the TradingView ORB/VWAP idea, but should not be promoted until two things are addressed:

- Execution inputs must be corrected so backtests and walk-forward use the resolved broker/asset cost profiles.
- Gold feed provenance still needs verification before any production or live-paper promotion.

This follow-up implements the first item and leaves the second as an explicit blocker.

## Implemented

- Wired resolved `broker_profile` and `asset_profile` into CLI backtests.
- Wired the same resolved profiles into CLI walk-forward and full-pipeline runs.
- Added broker/asset/cost context to the backtest cache key so old zero-cost results are not reused accidentally.
- Added a one-trade-per-day cap to `gold_orb_v1`, enabled by default.
- Added strategy state reset support in the backtest engine so stateful strategy memory does not leak across independent backtests or walk-forward folds.
- Added focused regression tests for:
  - one-trade-per-day behavior,
  - strategy reset behavior,
  - CLI resolved broker/asset profile forwarding,
  - walk-forward broker/asset/cost forwarding.

## Verification

Focused tests:

```text
PYTHONPATH=src venv/bin/python -m pytest tests/test_gold_orb_v1.py tests/test_cli_backtest_inputs.py tests/test_walk_forward_inputs.py
22 passed in 1.00s
```

Corrected backtest command:

```text
PYTHONPATH=src venv/bin/python -m tar_system.cli run-backtest --strategy gold_orb_v1 --symbol XAUUSD --timeframe M15 --broker current_broker_demo --force
```

Corrected backtest result:

- Trades: 251
- Win rate: 44.62%
- Profit factor: 1.4070
- Max drawdown: 0.9193%
- Expectancy: 1.3636
- Total cost: 28.1988
- Sharpe ratio: 2.2096
- Net profit: 342.2700

Corrected walk-forward result:

- Verdict: REVIEW
- Reason: Walk-forward parameter stability 0.0 is below 50.
- Trades: 483
- Win rate: 51.35%
- Profit factor: 1.2897
- Max drawdown: 0.1739%
- Expectancy: 0.5883
- Bootstrap mean: 0.0005883
- Bootstrap CI lower: 0.0000753
- Bootstrap CI upper: 0.0011020
- Bootstrap spans zero: false
- Parameter stability score: 0.0
- Parameter sensitivity measured: false

Corrected score:

```text
PYTHONPATH=src venv/bin/python -m tar_system.cli score-strategy --strategy gold_orb_v1 --symbol XAUUSD --timeframe M15 --broker current_broker_demo
```

- Score: 77.86
- Verdict: REVIEW
- Reason codes:
  - WF_VERDICT_REVIEW
  - WF_UNSTABLE_PARAMETERS
  - SEARCH_PARAMETER_STABILITY_NOT_MET
- Failed gate: parameter stability 0.00 < 0.70
- Multi-agent result: REVIEW with dissent
  - risk: REVIEW
  - performance: KEEP
  - robustness: REVIEW

## Current Position

This is now a fairer test of `gold_orb_v1` because the input path includes broker and asset cost assumptions, and the strategy no longer over-fires multiple entries in the same day.

Even after those corrections, the strategy should remain PARKED/REVIEW, not promoted. The result has a useful performance signal, but robustness is not good enough yet because parameter stability is still zero and the gold data/feed provenance remains unresolved.

## Proposed Next Debate

Ask Claude to challenge one of these two next steps:

1. Run a constrained parameter sweep on `gold_orb_v1` with fixed broker/asset inputs and require stability before any KEEP verdict.
2. Pause optimization and first complete XAUUSD feed provenance review, because optimizing on untrusted input data can make the result look cleaner than it is.

My recommendation is option 2 first, then option 1.
